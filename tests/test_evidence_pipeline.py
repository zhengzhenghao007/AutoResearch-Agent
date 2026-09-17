import pytest
from schemas.research import Document, Source, Page
from services.evidence_extraction import EvidenceExtractor
from services.evidence_review import review_paper
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


def document():
    return Document(source=Source(id='a'*64, title='Example', uri='upload:example.pdf', sha256='a'*64), total_pages=1,
                    pages=[Page(number=1, text='We propose a navigation method. A limitation is the small sample size. Future work will study larger samples.')])


def test_extraction_never_fills_missing_experiments():
    paper = EvidenceExtractor().extract(document())
    assert review_paper(paper).approved
    assert 'result' in paper.missing_fields
    assert 'experiment' in paper.missing_fields
    assert all(c.claim_type == 'paper_report' for c in paper.claims)


def test_search_selection_persistence_and_comparison(tmp_path):
    class Processor:
        def download(self, url, title): return document()
        def parse_bytes(self, data, title, uri): return document()
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), processor=Processor(),
                            search=lambda topic, max_results: [{'title':'Example', 'pdf_url':'https://arxiv.org/pdf/2401.12345'}])
    run = flow.search('navigation')
    assert not run.papers
    with pytest.raises(ValueError): flow.analyze(run.id, ['unknown'])
    result = flow.analyze(run.id, [run.candidates[0].id])
    assert len(result.papers) == 1 and result.review.approved
    assert result.artifacts
    assert flow.store.load(run.id) == result
    assert 'whole field' in result.artifacts[-1].content
    imported = flow.import_pdf(b'pdf', 'Example')
    assert [(c.text, c.category) for c in imported.papers[0].claims] == [(c.text, c.category) for c in result.papers[0].claims]


def test_store_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError): ResearchStore(tmp_path).load('../secret')


def test_bad_llm_quote_is_rejected():
    from types import SimpleNamespace
    from services.evidence_extraction import Selections, Selection
    class FakeLLM:
        def structured_chat(self, **kwargs):
            return SimpleNamespace(parsed=Selections(items=[Selection(page=1, quote='Invented accuracy of 99 percent.', category='result')]))
    with pytest.raises(ValueError, match='quote'):
        EvidenceExtractor(mode='llm', llm_client=FakeLLM()).extract(document())


def test_two_papers_share_ingestion_and_keep_citations(tmp_path, monkeypatch):
    from services.paper_processing import PaperProcessor
    from test_evidence_pdf import pdf_bytes
    import requests
    payloads = [pdf_bytes(['We propose a navigation method. Results show improved accuracy.']), pdf_bytes(['We propose a mapping framework. A limitation is the sample size.'])]
    class Response:
        status_code = 200
        def __init__(self, data): self.data = data
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def iter_content(self, size): yield self.data
    monkeypatch.setattr(requests, 'get', lambda url, **kw: Response(payloads[0 if '00001' in url else 1]))
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [
        {'title': 'First', 'pdf_url': 'http://arxiv.org/pdf/2401.00001'},
        {'title': 'Second', 'pdf_url': 'https://arxiv.org/pdf/2401.00002'}])
    run = flow.search('navigation')
    result = flow.analyze(run.id, [c.id for c in run.candidates])
    assert len(result.papers) == 2 and result.review.approved
    methods = next(a for a in result.artifacts if a.kind == 'method_comparison')
    assert 'First' in methods.content and 'Second' in methods.content
    assert len(methods.evidence_ids) == 2
    uploaded = PaperProcessor().parse_bytes(payloads[0], 'First', 'upload:first.pdf')
    assert uploaded.pages == result.papers[0].document.pages
    assert uploaded.source.sha256 == result.papers[0].document.source.sha256


def test_hypothetical_results_are_not_reported_as_observed():
    doc = document()
    doc.pages[0].text = 'We expect that future results show improved accuracy.'
    paper = EvidenceExtractor().extract(doc)
    assert 'result' in paper.missing_fields


def test_schema_version_and_atomic_write_failure(tmp_path, monkeypatch):
    import json
    import os
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.search('navigation')
    before = (tmp_path / f'{run.id}.json').read_bytes()
    def fail(*args): raise OSError('simulated interruption')
    monkeypatch.setattr(os, 'replace', fail)
    run.topic = 'Changed'
    with pytest.raises(OSError): flow.store.save(run)
    assert (tmp_path / f'{run.id}.json').read_bytes() == before
    assert len(list(tmp_path.iterdir())) == 1
    data = json.loads(before)
    data['schema_version'] = 999
    (tmp_path / f'{run.id}.json').write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError): flow.store.load(run.id)


def test_cli_import_and_show(tmp_path):
    import subprocess
    import sys
    import json
    from pathlib import Path
    from test_evidence_pdf import pdf_bytes
    path = tmp_path / 'paper.pdf'
    path.write_bytes(pdf_bytes(['We propose an evidence based method.']))
    command = [sys.executable, 'research_cli.py', '--store', str(tmp_path / 'runs')]
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(command + ['import-pdf', str(path)], cwd=root, capture_output=True, text=True, check=True)
    run = json.loads(result.stdout)
    assert run['review']['approved']
    result = subprocess.run(command + ['show', run['id']], cwd=root, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == run


def test_stored_artifact_tampering_is_rejected(tmp_path):
    import json
    from test_evidence_pdf import pdf_bytes
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['A limitation is the small sample size.']), 'Paper')
    assert run.generated_claims and run.generated_claims[0].claim_type == 'suggestion'
    path = tmp_path / f'{run.id}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['artifacts'][0]['content'] = 'Invented result'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='artifact'):
        flow.store.load(run.id)


@pytest.mark.parametrize('tamper', ['quote', 'reference', 'review', 'selection', 'suggestion'])
def test_reloading_rejects_stale_or_forged_provenance(tmp_path, tamper):
    import json
    from test_evidence_pdf import pdf_bytes
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['A limitation is the small sample size.']), 'Paper')
    path = tmp_path / f'{run.id}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if tamper == 'quote': data['papers'][0]['evidence'][0]['quote'] = 'Invented accuracy is 99 percent.'
    if tamper == 'reference': data['artifacts'][0]['evidence_ids'] = ['missing']
    if tamper == 'review': data['review']['approved'] = False
    if tamper == 'selection': data['selected_ids'] = ['unknown']
    if tamper == 'suggestion': data['generated_claims'][0]['claim_type'] = 'paper_report'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError): flow.store.load(run.id)


def test_reanalysis_keeps_uploaded_papers(tmp_path):
    from test_evidence_pdf import pdf_bytes
    from services.paper_processing import PaperProcessor
    class Processor(PaperProcessor):
        def download(self, url, title):
            return self.parse_bytes(pdf_bytes(['We propose an online method.']), title, url)
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), processor=Processor(), search=lambda *a, **k: [{'title':'Online', 'pdf_url':'https://arxiv.org/pdf/2401.12345'}])
    run = flow.search('navigation')
    flow.import_pdf(pdf_bytes(['We propose an uploaded method.']), 'Uploaded', run.id)
    result = flow.analyze(run.id, [run.candidates[0].id])
    assert len(result.papers) == 2
    assert any(p.document.source.title == 'Uploaded' for p in result.papers)
