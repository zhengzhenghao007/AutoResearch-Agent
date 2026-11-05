import pytest
from schemas.research import ResearchRun
from services.research_store import ResearchStore
from services.sqlite_store import SQLiteResearchStore, ConflictError
from workflow.evidence_workflow import EvidenceWorkflow

@pytest.fixture(params=[ResearchStore, SQLiteResearchStore])
def flow(request, tmp_path):
    return EvidenceWorkflow(store=request.param(tmp_path), search=lambda *a, **k: [{'title': 'Paper', 'pdf_url': 'https://arxiv.org/pdf/2401.12345'}])

def test_blank_project_defaults_are_unique(flow):
    first, second = flow.create(), flow.create()
    assert first.project_name == 'Research'
    assert second.project_name == 'Research 2'
    assert first.research_goal == ''
    assert flow.store.history().items[0].project_name == 'Research 2'

def test_metadata_is_separate_and_stale_edits_fail(flow):
    run = flow.create('old evidence topic')
    changed = flow.update_project(run.id, 'My library', 'Compare methods', None, '')
    assert changed.topic == 'old evidence topic'
    assert changed.project_name == 'My library'
    assert changed.research_goal == 'Compare methods'
    with pytest.raises(ConflictError):
        flow.update_project(run.id, 'Lost update', '', None, '')
    assert flow.store.load(run.id).project_name == 'My library'

def test_legacy_filename_fallback_preserves_original_topic(flow):
    run = flow.create('private-paper.PDF')
    assert run.project_name is None
    assert run.effective_project_name == 'Research'
    assert run.topic == 'private-paper.PDF'
    assert flow.create('Battery research').effective_project_name == 'Battery research'

def test_search_reloads_preserves_project_and_deduplicates(flow):
    run = flow.create(project_name='Collection', research_goal='My goal')
    def source(*args, **kwargs):
        current = flow.store.load(run.id)
        current.plan.append('Concurrent change')
        flow.store.save(current)
        return [{'title': 'Paper', 'pdf_url': 'https://arxiv.org/pdf/2401.12345'}]
    flow.search_source = source
    found = flow.search('new query', run_id=run.id)
    again = flow.search('another query', run_id=run.id)
    assert found.project_name == 'Collection'
    assert found.research_goal == 'My goal'
    assert found.topic == run.topic
    assert 'Concurrent change' in found.plan
    assert len(again.candidates) == 1
    assert again.papers == run.papers

def test_upload_failure_creates_no_project(flow):
    with pytest.raises(ValueError):
        flow.import_pdf(b'not a PDF', 'private.pdf')
    assert flow.store.history().total == 0

def test_upload_defaults_and_search_keeps_real_papers(flow):
    from test_evidence_pdf import pdf_bytes
    run = flow.import_pdf(pdf_bytes(['We propose a navigation method.']), 'private.pdf')
    assert run.project_name == 'Research'
    assert run.topic == 'Research'
    before = run.papers[0].model_dump(mode='json')
    updated = flow.search('navigation', run_id=run.id)
    assert updated.papers[0].model_dump(mode='json') == before
    assert updated.project_name == 'Research'

def test_metadata_api_create_update_conflict_and_search(flow):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from backend.app.api.research import get_workflow, router
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            created = client.post('/api/research/runs', json={})
            assert created.status_code == 200
            run = created.json()
            edit = dict(project_name='Library', research_goal='Question', expected_project_name='Research', expected_research_goal='')
            response = client.post(f"/api/research/runs/{run['id']}/project", json=edit)
            assert response.status_code == 200
            assert response.json()['topic'] == 'Research'
            assert client.post(f"/api/research/runs/{run['id']}/project", json=edit).status_code == 409
            result = client.post('/api/research/search', json={'topic': 'methods', 'run_id': run['id']})
            assert result.status_code == 200
            assert result.json()['project_name'] == 'Library'
    finally:
        app.dependency_overrides.clear()

def test_metadata_edit_preserves_manuscript_evidence_hash(flow):
    from test_evidence_pdf import pdf_bytes
    from services.manuscript_draft import build_manuscript_draft
    run = flow.import_pdf(pdf_bytes(['We propose a navigation method.']), 'paper.pdf')
    digest = build_manuscript_draft(run).input_sha256
    changed = flow.update_project(run.id, 'Different name', 'Different goal', 'Research', '')
    assert build_manuscript_draft(changed).input_sha256 == digest


def test_search_query_is_not_a_project_name_or_goal(flow):
    run = flow.search('scheduling methods')
    assert run.project_name == 'Research'
    assert run.research_goal == ''


def test_slow_analysis_does_not_overwrite_a_project_rename(flow, monkeypatch):
    from test_evidence_pdf import pdf_bytes
    run = flow.search('methods')
    def download(url, title):
        flow.update_project(run.id, 'Renamed while analyzing', '', run.project_name, '')
        return flow.processor.parse_bytes(pdf_bytes(['We propose a method.']), title, url)
    monkeypatch.setattr(flow.processor, 'download', download)
    with pytest.raises(ValueError, match='changed'):
        flow.analyze(run.id, [run.candidates[0].id])
    assert flow.store.load(run.id).project_name == 'Renamed while analyzing'
