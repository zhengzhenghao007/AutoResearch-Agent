import importlib
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from services.research_store import ResearchStore
from services.citation_registry import build_citation_registry
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


def export(run):
    return importlib.import_module('services.bibtex_export').build_bibtex_export(run)


def populated(tmp_path, uri='https://arxiv.org/pdf/2401.12345v2', title='Navigation'):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['We propose a navigation method.']), title)
    run.papers[0].document.source.uri = uri
    flow.store.save(run)
    return flow, run


@pytest.mark.parametrize('identifier', ['2401.12345v2', '2401.12345', 'hep-th/9901001v1'])
def test_minimal_fields_preserve_identifier(tmp_path, identifier):
    _, run = populated(tmp_path, f'http://arxiv.org/abs/{identifier}')
    result = export(run)
    key = 'source_' + run.papers[0].document.source.id.encode('utf-8').hex()
    assert result.bibtex == (f'@misc{{{key},\n'
        '  title = {{Navigation}},\n'
        f'  eprint = {{{identifier}}},\n'
        '  archivePrefix = {arXiv},\n'
        f'  url = {{https://arxiv.org/abs/{identifier}}}\n'
        '}\n')
    assert result.skipped_sources == []


@pytest.mark.parametrize('uri', [
    'upload:paper.pdf', 'https://arxiv.org.evil.test/pdf/2401.12345v2',
    'https://arxiv.org/pdf/2401.12345v2?x=1', 'https://arxiv.org/pdf/2401.12345#x',
    'https://user@arxiv.org/pdf/2401.12345', 'https://arxiv.org:443/pdf/2401.12345',
])
def test_unsupported_sources_are_explicitly_skipped(tmp_path, uri):
    _, run = populated(tmp_path, uri)
    result = export(run)
    assert result.bibtex == ''
    assert [s.model_dump() for s in result.skipped_sources] == [{
        'source_id': run.papers[0].document.source.id,
        'reason': 'missing_bibliographic_identity'}]


def test_escaping_unicode_and_stable_keys(tmp_path):
    _, run = populated(tmp_path, title='A {B} \\input & 50% #1_$ ~^ “研究”\nNext')
    text = export(run).bibtex
    assert r'A \textbraceleft{}B\textbraceright{} \textbackslash{}input \& 50\% \#1\_\$ \textasciitilde{}\textasciicircum{} “研究” Next' in text
    key = text.split(',')[0]
    run.papers[0].document.source.title = 'Renamed'
    # Rebuild title-dependent artifacts using the real workflow.
    from services.literature_synthesis import synthesize, build_suggestions
    run.artifacts = synthesize(run.papers)
    run.generated_claims = build_suggestions(run.papers)
    assert export(run).bibtex.split(',')[0] == key


def test_api_cli_readonly_and_corrupt_snapshot_rejection(tmp_path):
    flow, run = populated(tmp_path)
    run = flow.import_pdf(pdf_bytes(['We propose a mapping method.']), 'Local', run.id)
    path = tmp_path / f'{run.id}.json'
    before = path.read_bytes(), path.stat().st_mtime_ns
    registry = build_citation_registry(run)
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            url = f'/api/research/runs/{run.id}/bibtex'
            response = client.get(url)
            assert response.status_code == 200
            result = response.json()
            assert client.get(url).json() == result
            assert len(result['skipped_sources']) == 1
            cmd = [sys.executable, 'research_cli.py', '--store', str(tmp_path), 'bibtex', run.id]
            cli = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            assert cli.returncode == 0, cli.stderr
            assert cli.stdout == result['bibtex']
            assert 'missing_bibliographic_identity' in cli.stderr
            assert build_citation_registry(flow.store.load(run.id)) == registry
            assert (path.read_bytes(), path.stat().st_mtime_ns) == before
            assert client.get('/api/research/runs/' + 'f'*32 + '/bibtex').status_code == 404
            data = json.loads(path.read_text())
            data['papers'][0]['evidence'][0]['quote'] = 'Fabricated quotation with no source.'
            path.write_text(json.dumps(data))
            assert client.get(url).status_code == 400
            failed = subprocess.run(cmd, capture_output=True)
            assert failed.returncode != 0 and not failed.stdout
    finally:
        app.dependency_overrides.clear()


def test_search_only_empty_and_screening_independent(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [
        {'title': 'Candidate', 'pdf_url': 'https://arxiv.org/pdf/2401.12345v2'}])
    run = flow.search('Navigation')
    assert export(run).bibtex == ''
    assert export(run).skipped_sources == []
    run = flow.import_pdf(pdf_bytes(['We propose a method.']), 'Upload', run.id)
    before = export(run)
    run = flow.record_candidate_decision(run.id, run.candidates[0].id, 'exclude', 'Scope')
    assert export(run) == before


def test_distinct_legacy_sources_with_same_hash_have_unique_keys(tmp_path):
    from copy import deepcopy
    from services.literature_synthesis import synthesize, build_suggestions
    flow, run = populated(tmp_path)
    second = deepcopy(run.papers[0])
    second.document.source.id = 'legacy-alias'
    second.document.source.uri = 'https://arxiv.org/pdf/2401.12345v3'
    for evidence in second.evidence:
        old_id = evidence.id
        evidence.id = 'second-' + old_id
        evidence.source_id = 'legacy-alias'
        for claim in second.claims:
            claim.evidence_ids = [evidence.id if item == old_id else item for item in claim.evidence_ids]
    for claim in second.claims:
        claim.id = 'second-' + claim.id
    run.papers.append(second)
    run.artifacts = synthesize(run.papers)
    run.generated_claims = build_suggestions(run.papers)
    flow.store.save(run)
    text = export(run).bibtex
    keys = [line for line in text.splitlines() if line.startswith('@misc')]
    assert len(keys) == len(set(keys)) == 2
    assert text.index('2401.12345v2') < text.index('2401.12345v3')
    assert export(flow.store.load(run.id)).bibtex == text


@pytest.mark.parametrize('title', ['A { B', 'A } B', r'} @misc{injected, title={bad}'])
def test_unbalanced_title_braces_cannot_break_entry_structure(tmp_path, title):
    _, run = populated(tmp_path, title=title)
    text = export(run).bibtex
    # BibTeX counts braces even when preceded by a TeX backslash.
    depth = 0
    for char in text:
        depth += (char == '{') - (char == '}')
        assert depth >= 0
    assert depth == 0
