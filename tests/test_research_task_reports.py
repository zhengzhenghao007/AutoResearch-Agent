from tests.test_research_tasks import populated
from schemas.research_tasks import ResearchTaskCreate
from services.research_tasks import ResearchTaskExecutor


def setup_task(tmp_path, complete=True):
    store, run = populated(tmp_path)
    executor = ResearchTaskExecutor(store)
    task = executor.create(run.id, ResearchTaskCreate(question='coverage', subquestions=['coverage']))
    task = executor.next(run.id, task.id)
    if complete:
        task = executor.next(run.id, task.id)
    return store, run, executor, task


def test_report_resolves_checked_quotes_without_mutation(tmp_path):
    from services.research_task_reports import build_task_report
    store, run, executor, task = setup_task(tmp_path)
    report = build_task_report(task, run)
    assert report['source_status'] == 'current'
    assert report['scientific_validation'] == 'not_assessed'
    evidence = report['questions'][0]['evidence']
    assert evidence and all(e['binding_status'] == 'checked' for e in evidence)
    assert evidence[0]['title'] == 'study'
    assert evidence[0]['page'] == 1
    assert evidence[0]['quote'] in run.papers[0].document.pages[0].text
    assert report['task']['usage'] == task.usage.model_dump()
    assert executor.get(run.id, task.id) == task
    assert store.load(run.id) == run


def test_pending_inspection_is_explicit(tmp_path):
    from services.research_task_reports import build_task_report
    _, run, _, task = setup_task(tmp_path, complete=False)
    report = build_task_report(task, run)
    assert report['questions'][0]['inspection_status'] == 'pending'
    assert all(e['binding_status'] == 'not_checked' for e in report['questions'][0]['evidence'])


def test_changed_sources_never_supply_replacement_quotations(tmp_path):
    from services.research_task_reports import build_task_report
    _, run, _, task = setup_task(tmp_path)
    run.papers[0].document.source.title = 'replacement'
    report = build_task_report(task, run)
    assert report['source_status'] == 'stale'
    assert report['questions'][0]['evidence'] == []
    assert report['questions'][0]['evidence_ids']
    assert report['warnings']


def test_invalid_evidence_id_is_reported_not_silently_omitted(tmp_path):
    from services.research_task_reports import build_task_report
    _, run, _, task = setup_task(tmp_path)
    task.steps[-1].result.evidence_ids.append('missing')
    report = build_task_report(task, run)
    assert any('missing' in gap for gap in report['questions'][0]['gaps'])


def test_markdown_treats_document_content_as_literal_text(tmp_path):
    from services.research_task_reports import build_task_report, render_task_report
    _, run, _, task = setup_task(tmp_path)
    task.question = '<script>alert(1)</script>\n# forged\n[x](javascript:alert(1))'
    text = render_task_report(build_task_report(task, run))
    assert '<script>' not in text
    assert '\n# forged' not in text
    assert '[x](javascript:' not in text
    assert 'Scientific validation: not_assessed' in text
    assert 'PDF page 1' in text
    assert task.source_sha256 in text


def test_report_api_formats_and_cross_run_isolation(tmp_path):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.research import get_workflow
    from types import SimpleNamespace
    store, run, _, task = setup_task(tmp_path)
    app.dependency_overrides[get_workflow] = lambda: SimpleNamespace(store=store)
    try:
        client = TestClient(app)
        url = f'/api/research/runs/{run.id}/tasks/{task.id}/report'
        response = client.get(url)
        assert response.status_code == 200
        assert response.json()['task']['id'] == task.id
        markdown = client.get(url + '?format=markdown')
        assert markdown.status_code == 200
        assert markdown.headers['content-type'].startswith('text/markdown')
        assert 'attachment' in markdown.headers['content-disposition']
        assert 'PDF page 1' in markdown.text
        assert client.get(url + '?format=html').status_code == 422
        assert client.get(url.replace(run.id, 'f' * 32)).status_code == 404
        import sqlite3
        with sqlite3.connect(store.root / 'research_tasks.sqlite3') as db:
            before = db.execute('SELECT * FROM tasks').fetchall()
        run.papers[0].document.source.sha256 = 'b' * 64
        store.save(run)
        assert client.get(url).json()['source_status'] == 'stale'
        with sqlite3.connect(store.root / 'research_tasks.sqlite3') as db:
            assert db.execute('SELECT * FROM tasks').fetchall() == before
    finally:
        app.dependency_overrides.clear()


def test_report_reader_and_tenant_access(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.app.security import SecurityConfig, SecurityMiddleware
    from backend.app.api.research_tasks import router
    from services.sqlite_store import SQLiteResearchStore
    _, run, _, _ = setup_task(tmp_path / 'fixture')
    store = SQLiteResearchStore(tmp_path / 'users' / 'reader')
    store.save(run)
    task = ResearchTaskExecutor(store).create(run.id, ResearchTaskCreate(question='coverage'))
    app = FastAPI()
    config = SecurityConfig(True, tmp_path, {'reader': {'role': 'reader', 'token': 'a'*32}, 'other': {'role': 'writer', 'token': 'b'*32}}, sqlite=True)
    app.state.security_config = config
    app.add_middleware(SecurityMiddleware, config=config)
    app.include_router(router)
    client = TestClient(app)
    url = f'/api/research/runs/{run.id}/tasks/{task.id}/report'
    assert client.get(url).status_code == 401
    assert client.get(url, headers={'Authorization': 'Bearer ' + 'a'*32}).status_code == 200
    assert client.get(url, headers={'Authorization': 'Bearer ' + 'b'*32}).status_code == 404
