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
from services.bibtex_export import build_bibtex_export
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


def view(run):
    return importlib.import_module('services.source_identity').build_source_identities(run)


def populated(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.import_pdf(pdf_bytes(['We propose a navigation method.']), 'First')
    return flow, run, run.papers[0].document.source.id


def test_legacy_read_and_set_revision_clear_history(tmp_path):
    flow, run, source = populated(tmp_path)
    path = tmp_path / f'{run.id}.json'
    data = run.model_dump(mode='json')
    data.pop('source_identity_annotations', None)
    path.write_text(json.dumps(data))
    before = path.read_bytes(), path.stat().st_mtime_ns
    assert flow.store.load(run.id).source_identity_annotations == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    citations, bibtex = build_citation_registry(run), build_bibtex_export(run)
    first = flow.record_source_identity(run.id, source, 'set', 'https://doi.org/10.1234/ABC', 'Publisher page')
    assert first.source_identity_annotations[0].doi == '10.1234/abc'
    assert first.source_identity_annotations[0].recorded_at.tzinfo is not None
    second = flow.record_source_identity(run.id, source, 'set', '10.1234/def', 'Correction')
    assert [e.doi for e in second.source_identity_annotations] == ['10.1234/abc', '10.1234/def']
    assert view(second).sources[0].doi == '10.1234/def'
    assert view(second).sources[0].provenance == 'user_supplied'
    cleared = flow.record_source_identity(run.id, source, 'clear', None, 'Wrong association')
    assert view(cleared).sources[0].doi is None
    assert view(cleared).sources[0].provenance is None
    assert len(flow.store.load(run.id).source_identity_annotations) == 3
    assert build_citation_registry(cleared) == citations
    assert build_bibtex_export(cleared) == bibtex


@pytest.mark.parametrize('doi', ['bad', '10.1234/', 'https://doi.org.evil/10.1234/x',
    'https://user@doi.org/10.1234/x', 'https://doi.org:443/10.1234/x',
    'https://doi.org/10.1234/x?q=1', 'https://doi.org/10.1234/x#part',
    'https://doi.org/10.1234/%78', '10.1234/a b', '10.1234/a\nb'])
def test_unsupported_syntax_preserves_snapshot(tmp_path, doi):
    flow, run, source = populated(tmp_path)
    path = tmp_path / f'{run.id}.json'
    before = path.read_bytes()
    with pytest.raises(ValueError):
        flow.record_source_identity(run.id, source, 'set', doi, 'Reason')
    assert path.read_bytes() == before


def test_conflicts_do_not_merge_and_clear_resolves(tmp_path):
    flow, run, source = populated(tmp_path)
    run = flow.import_pdf(pdf_bytes(['We propose a mapping method.']), 'Second', run.id)
    second = run.papers[1].document.source.id
    flow.record_source_identity(run.id, source, 'set', '10.1234/ABC', 'Reason')
    updated = flow.record_source_identity(run.id, second, 'set', '10.1234/abc', 'Reason')
    result = view(updated)
    assert [c.model_dump() for c in result.conflicts] == [{'doi': '10.1234/abc', 'source_ids': [source, second]}]
    assert updated.papers == run.papers
    assert updated.selected_ids == run.selected_ids
    updated = flow.record_source_identity(run.id, second, 'clear', None, 'Correction')
    assert view(updated).conflicts == []


def test_invalid_references_and_actions_and_corruption(tmp_path):
    flow, run, source = populated(tmp_path)
    path = tmp_path / f'{run.id}.json'
    before = path.read_bytes()
    for source_id, action, doi, reason in [('unknown', 'set', '10.1234/a', 'Reason'),
            (source, 'clear', '10.1234/a', 'Reason'), (source, 'set', None, 'Reason'),
            (source, 'set', '10.1234/a', ' '), (source, 'maybe', '10.1234/a', 'Reason')]:
        with pytest.raises(ValueError):
            flow.record_source_identity(run.id, source_id, action, doi, reason)
        assert path.read_bytes() == before
    flow.record_source_identity(run.id, source, 'set', '10.1234/a', 'Reason')
    data = json.loads(path.read_text())
    data['source_identity_annotations'][0]['source_id'] = 'forged'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        flow.store.load(run.id)


def test_api_cli_same_history_and_read_only_view(tmp_path):
    flow, run, source = populated(tmp_path)
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            url = f'/api/research/runs/{run.id}/source-identities'
            body = {'source_id': source, 'action': 'set', 'doi': '10.1234/x', 'reason': 'Reason'}
            response = client.post(url, json=body)
            assert response.status_code == 200
            assert client.post(url, json={**body, 'recorded_at': '2020-01-01T00:00:00Z'}).status_code == 422
            assert client.post(url, json={**body, 'source_id': 'missing'}).status_code == 400
            assert client.get('/api/research/runs/' + 'f'*32 + '/source-identities').status_code == 404
            cmd = [sys.executable, 'research_cli.py', '--store', str(tmp_path)]
            read = subprocess.run(cmd + ['source-identities', run.id], capture_output=True, text=True)
            assert read.returncode == 0, read.stderr
            assert json.loads(read.stdout) == client.get(url).json()
            write = subprocess.run(cmd + ['source-doi', run.id, source, 'clear', '--reason', 'Correction'], capture_output=True, text=True)
            assert write.returncode == 0, write.stderr
            assert json.loads(write.stdout) == client.get(f'/api/research/runs/{run.id}').json()
            path = tmp_path / f'{run.id}.json'
            before = path.read_bytes(), path.stat().st_mtime_ns
            assert client.get(url).json()['sources'][0]['doi'] is None
            assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    finally:
        app.dependency_overrides.clear()


def test_deselection_reselection_and_upload_preserve_history(tmp_path, monkeypatch):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [
        {'title': 'First', 'pdf_url': 'https://arxiv.org/pdf/2401.00001v1'},
        {'title': 'Second', 'pdf_url': 'https://arxiv.org/pdf/2401.00002v1'}])
    payloads = {'First': pdf_bytes(['We propose a navigation method.']),
                'Second': pdf_bytes(['We propose a mapping method.'])}
    monkeypatch.setattr(flow.processor, 'download', lambda url, title:
        flow.processor.parse_bytes(payloads[title], title, url))
    run = flow.search('Navigation')
    a, b = [c.id for c in run.candidates]
    with pytest.raises(ValueError):
        flow.record_source_identity(run.id, a, 'set', '10.1234/x', 'Candidate only')
    run = flow.analyze(run.id, [a])
    source = run.papers[0].document.source.id
    run = flow.record_source_identity(run.id, source, 'set', '10.1234/x', 'Reason')
    history = run.source_identity_annotations
    run = flow.analyze(run.id, [b])
    inactive = next(s for s in view(run).sources if s.source.id == source)
    assert not inactive.active and inactive.doi == '10.1234/x'
    assert run.source_identity_annotations == history
    before = (tmp_path / f'{run.id}.json').read_bytes()
    with pytest.raises(ValueError):
        flow.record_source_identity(run.id, source, 'clear', None, 'Absent')
    assert (tmp_path / f'{run.id}.json').read_bytes() == before
    run = flow.record_source_identity(run.id, run.papers[0].document.source.id, 'set', '10.1234/x', 'Reason')
    assert view(run).conflicts == []
    run = flow.analyze(run.id, [a, b])
    assert len(view(run).conflicts) == 1
    run = flow.record_source_identity(run.id, source, 'clear', None, 'Correction')
    flow.analyze(run.id, [b])
    run = flow.analyze(run.id, [a])
    assert view(run).sources[0].doi is None and view(run).sources[0].active
    history = run.source_identity_annotations
    run = flow.import_pdf(pdf_bytes(['We propose another method.']), 'Upload', run.id)
    assert flow.store.load(run.id).source_identity_annotations == history


@pytest.mark.parametrize('field,value', [('sha256', 'a' * 64), ('uri', 'upload:changed')])
def test_source_identity_drift_is_rejected(tmp_path, field, value):
    flow, run, source = populated(tmp_path)
    run = flow.record_source_identity(run.id, source, 'set', '10.1234/x', 'Reason')
    setattr(run.source_identity_annotations[0].source, field, value)
    with pytest.raises(ValueError, match='binding'):
        flow.store.save(run)
