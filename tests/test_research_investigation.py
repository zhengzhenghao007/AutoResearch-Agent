from pathlib import Path
import pytest
from schemas.research import ResearchRun
from services.research_investigation import build_investigation


def corpus():
    return ResearchRun.model_validate_json(Path('examples/conformal-prediction/outputs/run.json').read_text(encoding='utf-8'))


def test_report_only_uses_selected_verified_evidence():
    run = corpus()
    selected = [paper.document.source.id for paper in run.papers[:2]]
    report = build_investigation(run, selected)
    assert report.candidates
    assert report.source_ids == selected
    for item in report.candidates:
        assert item.source_id in selected
        assert all(passage.source_id in selected and passage.source_id != item.source_id for passage in item.related_passages)
        assert item.novelty.startswith('Unverified')
    assert len(report.candidates) <= 20
    assert build_investigation(run, selected) == report
    run.research_goal = 'A different question'
    assert build_investigation(run, selected).input_sha256 != report.input_sha256


def test_unknown_and_duplicate_sources_rejected():
    run = corpus()
    with pytest.raises(ValueError): build_investigation(run, ['missing'])
    sid = run.papers[0].document.source.id
    with pytest.raises(ValueError): build_investigation(run, [sid, sid])


def test_invalid_quotes_are_excluded_and_reported():
    run = corpus()
    paper = run.papers[0]
    paper.evidence[0].quote = 'This fabricated quote does not appear on its cited page.'
    report = build_investigation(run, [])
    assert all(item.source_id != paper.document.source.id for item in report.candidates)
    assert any('Excluded invalid evidence' in item for item in report.limitations)


def test_api_report_is_bound_to_existing_run(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from backend.app.main import app
    from backend.app.api.research import get_workflow
    from services.research_store import ResearchStore
    run = corpus()
    store = ResearchStore(tmp_path)
    store.save(run)
    app.dependency_overrides[get_workflow] = lambda: SimpleNamespace(store=store)
    try:
        client = TestClient(app)
        response = client.post(f'/api/research/runs/{run.id}/investigation', json={'source_ids':[]})
        assert response.status_code == 200, response.text
        assert response.json()['candidates']
        assert client.post('/api/research/runs/' + '0'*32 + '/investigation', json={'source_ids':[]}).status_code == 404
    finally:
        app.dependency_overrides.clear()
