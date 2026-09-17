from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


def test_upload_get_and_legacy_health(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            assert client.get('/api/health').json() == {'status': 'healthy'}
            response = client.post('/api/research/upload', files={'file': ('paper.pdf', pdf_bytes(['We propose a navigation method.']), 'application/pdf')})
            assert response.status_code == 200, response.text
            run = response.json()
            assert run['review']['approved']
            assert client.get('/api/research/runs/' + run['id']).json() == run
            assert client.post('/api/research/upload', files={'file': ('bad.pdf', b'bad', 'application/pdf')}).status_code == 400
            assert client.get('/api/research/runs/' + 'a'*32).status_code == 404
            assert client.post('/api/research/search', json={'topic': '', 'max_results': 5}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_existing_search_and_analysis_contracts(monkeypatch):
    from backend.app.api import papers, analysis
    paper = {'title': 'Example', 'pdf_url': 'https://arxiv.org/pdf/2401.12345'}
    monkeypatch.setattr(papers.research_service.workflow, 'search', lambda **kw: {'topic': kw['topic'], 'plan': ['Search'], 'papers': [paper]})
    monkeypatch.setattr(analysis.analysis_service, 'analyze_paper', lambda request: {'topic':'navigation', 'paper': request.paper, 'analysis': {'methodology': 'Example method'}})
    with TestClient(app) as client:
        result = client.post('/api/papers/search', json={'topic': 'navigation', 'max_results': 1})
        assert result.status_code == 200, result.text
        assert result.json()['total'] == 1
        result = client.post('/api/papers/analyze', json={'paper': paper, 'reader_mode':'rule'})
        assert result.status_code == 200
        assert result.json()['analysis']['methodology'] == 'Example method'


def test_upload_size_and_path_redaction(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            result = client.post('/api/research/upload', files={'file': ('C:\\private\\paper.pdf', pdf_bytes(['We propose a useful method.']), 'application/pdf')})
            assert result.status_code == 200
            assert 'private' not in result.text
            flow.processor.max_bytes = 10
            assert client.post('/api/research/upload', files={'file': ('p.pdf', b'a'*11)}).status_code == 413
    finally:
        app.dependency_overrides.clear()
