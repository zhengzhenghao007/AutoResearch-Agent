import importlib
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


def builder():
    return importlib.import_module('services.citation_registry').build_citation_registry


def populated(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['We propose a navigation method. A limitation is the small sample size.']), 'Paper')
    return flow, run


@pytest.mark.parametrize('uri,expected', [
    ('https://arxiv.org/pdf/2401.12345v2', '2401.12345v2'),
    ('http://arxiv.org/abs/hep-th/9901001v1', 'hep-th/9901001v1'),
    ('https://arxiv.org/pdf/2401.12345', None),
    ('upload:paper.pdf', None),
    ('https://arxiv.org.evil.test/pdf/2401.12345v2', None),
    ('https://user@arxiv.org/pdf/2401.12345v2', None),
    ('https://arxiv.org:443/pdf/2401.12345v2', None),
    ('https://arxiv.org/pdf/2401.12345v2?x=1', None),
    ('https://arxiv.org/pdf/2401.12345v2#x', None),
])
def test_explicit_revision_only(uri, expected):
    from services import arxiv_identity
    assert arxiv_identity.explicit_arxiv_revision_id(uri) == expected


def test_registry_preserves_provenance_and_does_not_mutate(tmp_path):
    flow, run = populated(tmp_path)
    before = run.model_dump_json()
    snapshot = (tmp_path / f'{run.id}.json').read_bytes()
    result = builder()(run)
    entry = result.sources[0]
    source = run.papers[0].document.source
    assert (entry.source_id, entry.sha256, entry.uri) == (source.id, source.sha256, source.uri)
    assert entry.evidence[0].model_dump() == {k: getattr(run.papers[0].evidence[0], k) for k in ('id', 'page', 'quote')}
    assert {c.id for c in entry.claims} == {c.id for c in run.papers[0].claims + run.generated_claims}
    assert any(c.claim_type == 'suggestion' for c in entry.claims)
    assert builder()(run) == result
    assert run.model_dump_json() == before
    assert (tmp_path / f'{run.id}.json').read_bytes() == snapshot


def test_search_only_run_exports_no_sources(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [
        {'title': 'Candidate', 'pdf_url': 'https://arxiv.org/pdf/2401.12345v2'}])
    assert builder()(flow.search('navigation')).sources == []


def test_api_cli_share_registry_and_reject_corrupt_snapshot(tmp_path):
    flow, run = populated(tmp_path)
    expected = builder()(run).model_dump(mode='json')
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            url = f'/api/research/runs/{run.id}/citations'
            assert client.get(url).json() == expected
            assert client.get('/api/research/runs/' + 'f'*32 + '/citations').status_code == 404
            command = [sys.executable, 'research_cli.py', '--store', str(tmp_path), 'citations', run.id]
            result = subprocess.run(command, capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout) == expected
            path = tmp_path / f'{run.id}.json'
            broken = json.loads(path.read_text())
            broken['papers'][0]['evidence'][0]['quote'] = 'Fabricated quotation not in the original.'
            path.write_text(json.dumps(broken))
            assert client.get(url).status_code == 400
            assert subprocess.run(command, capture_output=True).returncode != 0
    finally:
        app.dependency_overrides.clear()


def test_multiple_sources_keep_references_scoped(tmp_path):
    flow, first = populated(tmp_path)
    run = flow.import_pdf(pdf_bytes(['We propose a different mapping method.']), 'Second', first.id)
    result = builder()(run)
    assert len(result.sources) == 2
    for entry, paper in zip(result.sources, run.papers):
        ids = {e.id for e in paper.evidence}
        assert {e.id for e in entry.evidence} == ids
        assert all(ids.intersection(c.evidence_ids) for c in entry.claims)
        assert {c.id for c in paper.claims} <= {c.id for c in entry.claims}


def test_api_read_preserves_snapshot_and_original_contract(tmp_path, monkeypatch):
    import requests
    flow, run = populated(tmp_path)
    path = tmp_path / f'{run.id}.json'
    before, modified = path.read_bytes(), path.stat().st_mtime_ns
    def no_network(*args, **kwargs):
        raise AssertionError('Registry must be offline')
    monkeypatch.setattr(requests, 'get', no_network)
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            assert client.get(f'/api/research/runs/{run.id}/citations').status_code == 200
            assert client.get(f'/api/research/runs/{run.id}').json() == run.model_dump(mode='json')
        assert path.read_bytes() == before
        assert path.stat().st_mtime_ns == modified
    finally:
        app.dependency_overrides.clear()
