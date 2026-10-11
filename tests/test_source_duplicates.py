import importlib
import json
import subprocess
import sys

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from schemas.research import Candidate
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


def report(run):
    return importlib.import_module('services.source_duplicates').build_source_duplicates(run)


def test_strict_candidate_groups_and_versions(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.search('Test')
    urls = ['http://arxiv.org/abs/2401.12345v1', 'https://arxiv.org/pdf/2401.12345v1.pdf',
            'https://arxiv.org/pdf/2401.12345', 'https://arxiv.org/pdf/2401.12345v2',
            'https://arxiv.org/pdf/2401.12345v1?q=1', 'https://evil.org/pdf/2401.12345v1']
    run.candidates = [Candidate(id=str(i), title='Same title', pdf_url=url) for i, url in enumerate(urls)]
    before = run.model_dump_json()
    result = report(run)
    assert [(g.kind, g.identity_value, [m.entity_id for m in g.members]) for g in result.groups] == [
        ('exact_arxiv_identifier', '2401.12345v1', ['0', '1'])]
    assert result.candidate_source_links == []
    assert report(run).model_dump_json() == result.model_dump_json()
    assert run.model_dump_json() == before


def test_doi_groups_clear_and_readonly_api_cli(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['We propose a first method.']), 'First')
    run = flow.import_pdf(pdf_bytes(['We propose a second method.']), 'Second', run.id)
    ids = [p.document.source.id for p in run.papers]
    for source in ids:
        run = flow.record_source_identity(run.id, source, 'set', '10.1234/shared', 'User claim')
    result = report(run)
    assert len(result.groups) == 1
    assert result.groups[0].kind == 'shared_user_supplied_doi'
    assert result.groups[0].identity_status == 'user_supplied_unverified'
    assert [m.entity_id for m in result.groups[0].members] == ids
    path = tmp_path / f'{run.id}.json'
    before = path.read_bytes(), path.stat().st_mtime_ns
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            response = client.get(f'/api/research/runs/{run.id}/source-duplicates')
            assert response.status_code == 200
            assert response.json() == result.model_dump(mode='json')
            assert client.get('/api/research/runs/' + '0'*32 + '/source-duplicates').status_code == 404
    finally:
        app.dependency_overrides.clear()
    output = subprocess.run([sys.executable, 'research_cli.py', '--store', str(tmp_path), 'source-duplicates', run.id], capture_output=True, text=True)
    assert output.returncode == 0, output.stderr
    assert json.loads(output.stdout) == result.model_dump(mode='json')
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    run = flow.record_source_identity(run.id, ids[0], 'clear', None, 'Correction')
    assert report(run).groups == []

import pytest
from schemas.research import CandidateDecision
from services.citation_registry import build_citation_registry
from services.bibtex_export import build_bibtex_export


@pytest.mark.parametrize('url', ['https://arxiv.org:443/pdf/2401.12345v1',
    'https://user@arxiv.org/pdf/2401.12345v1', 'https://arxiv.org/pdf/2401.12345v1#x',
    'https://arxiv.org/pdf/%32%34%30%31.12345v1'])
def test_unrecognized_links_never_group(tmp_path, url):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.search('Test')
    run.candidates = [Candidate(id=str(i), title='Same', pdf_url=url) for i in range(2)]
    assert report(run).groups == []


def test_links_are_not_duplicate_sources_and_annotations_do_not_filter(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['We propose a navigation method.']), 'Paper')
    run.papers[0].document.source.uri = 'https://arxiv.org/pdf/hep-th/9901001v2'
    run.candidates = [Candidate(id='a', title='Paper', pdf_url='http://arxiv.org/abs/hep-th/9901001v2.pdf'),
                      Candidate(id='b', title='Paper', pdf_url='https://arxiv.org/pdf/hep-th/9901001')]
    run.selected_ids = ['a']
    baseline = report(run)
    assert baseline.groups == []
    assert [link.model_dump() for link in baseline.candidate_source_links] == [dict(
        candidate_id='a', source_id=run.papers[0].document.source.id, arxiv_identifier='hep-th/9901001v2')]
    run.candidate_decisions = [CandidateDecision(candidate_id='a', decision='exclude', reason='User annotation')]
    citations, bibtex = build_citation_registry(run), build_bibtex_export(run)
    assert report(run) == baseline
    assert run.selected_ids == ['a']
    assert build_citation_registry(run) == citations and build_bibtex_export(run) == bibtex


def test_stored_hash_clue_and_invalid_duplicate_ids(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['We propose a first method.']), 'First')
    run = flow.import_pdf(pdf_bytes(['We propose a second method.']), 'Second', run.id)
    assert report(run).groups == []
    # The version-1 contract permits external source IDs and stored hash metadata.
    # No validator bypass: this is a metadata comparison, not a rehash of PDF bytes.
    run.papers[1].document.source.sha256 = run.papers[0].document.source.sha256
    groups = report(run).groups
    assert [(g.kind, g.identity_value) for g in groups] == [('same_pdf_bytes',run.papers[0].document.source.sha256)]
    run.papers.append(run.papers[0].model_copy(deep=True))
    with pytest.raises(ValueError, match='Duplicate source IDs'):
        report(run)


def test_inactive_doi_is_not_a_current_group(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['We propose a first method.']), 'First')
    run = flow.import_pdf(pdf_bytes(['We propose a second method.']), 'Second', run.id)
    for paper in run.papers:
        run = flow.record_source_identity(run.id, paper.document.source.id, 'set', '10.1234/shared', 'Claim')
    run.papers.pop()
    run = flow._finish(run)
    assert len(run.source_identity_annotations) == 2
    assert report(run).groups == []
