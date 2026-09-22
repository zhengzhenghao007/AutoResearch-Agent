import os

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.research import get_workflow
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


@pytest.fixture
def workspace(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    app.dependency_overrides[get_workflow] = lambda: flow
    with TestClient(app) as client:
        yield client, flow
    app.dependency_overrides.clear()


def test_history_empty_and_pagination_validation(workspace):
    client, _ = workspace
    assert client.get('/api/research/runs').json() == {
        'items': [], 'total': 0, 'page': 1, 'page_size': 10,
    }
    for query in ('page=0', 'page_size=0', 'page_size=51', 'page=no'):
        assert client.get('/api/research/runs?' + query).status_code == 422


def test_history_sorted_lightweight_and_persisted(workspace):
    client, flow = workspace
    runs = [flow.search(f'Topic {i}') for i in range(3)]
    for i, run in enumerate(runs):
        os.utime(flow.store._path(run.id), (1000 + i, 1000 + i))
    first = client.get('/api/research/runs?page_size=2').json()
    assert first['total'] == 3
    assert [row['id'] for row in first['items']] == [runs[2].id, runs[1].id]
    summary = first['items'][0]
    assert summary['topic'] == 'Topic 2'
    assert summary['candidate_count'] == summary['selected_count'] == summary['paper_count'] == 0
    assert summary['source_support_passed'] is False
    assert summary['updated_at']
    assert 'papers' not in summary
    second = client.get('/api/research/runs?page=2&page_size=2').json()
    assert [row['id'] for row in second['items']] == [runs[0].id]
    assert client.get('/api/research/runs?page=3&page_size=2').json()['items'] == []
    restored = ResearchStore(flow.store.root).load(summary['id'])
    assert client.get('/api/research/runs/' + restored.id).json() == restored.model_dump(mode='json')


def test_history_rejects_corrupt_snapshot(workspace):
    client, flow = workspace
    run = flow.search('Valid before corruption')
    flow.store._path(run.id).write_text('{broken', encoding='utf-8')
    response = client.get('/api/research/runs')
    assert response.status_code == 400
    assert 'Invalid stored research run' in response.json()['detail']
    assert str(flow.store.root) not in response.text


def test_upload_comparison_and_failures_leave_snapshot_unchanged(workspace):
    client, flow = workspace
    run = flow.search('Compare uploads')
    for title, quote in [('one.pdf', 'We propose a navigation method.'),
                         ('two.pdf', 'Our approach uses a second planner.')]:
        response = client.post('/api/research/upload', data={'run_id': run.id},
                               files={'file': (title, pdf_bytes([quote]), 'application/pdf')})
        assert response.status_code == 200
    saved = client.get('/api/research/runs/' + run.id).json()
    assert len(saved['papers']) == 2
    assert len(next(a for a in saved['artifacts'] if a['kind'] == 'method_comparison')['evidence_ids']) == 2
    for data in (pdf_bytes(['We propose a navigation method.']), b'not PDF'):
        failed = client.post('/api/research/upload', data={'run_id': run.id}, files={'file': ('one.pdf', data)})
        assert failed.status_code == 400
        assert client.get('/api/research/runs/' + run.id).json() == saved
    summary = client.get('/api/research/runs').json()['items'][0]
    assert summary['paper_count'] == 2 and summary['source_support_passed']


def test_search_select_two_downloads_through_real_services(workspace, monkeypatch):
    import requests
    client, flow = workspace
    flow.search_source = lambda *a, **k: [
        {'title': 'First', 'pdf_url': 'https://arxiv.org/pdf/2401.12345'},
        {'title': 'Second', 'pdf_url': 'https://arxiv.org/pdf/2401.12346'},
    ]
    downloads = []

    class Response:
        status_code = 200

        def __init__(self, text):
            self.data = pdf_bytes([text])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def iter_content(self, size):
            yield self.data

    def get(url, **kwargs):
        downloads.append(url)
        return Response('We propose the first method.' if url.endswith('5')
                        else 'Our approach uses the second method.')

    monkeypatch.setattr(requests, 'get', get)
    run = client.post('/api/research/search', json={'topic': 'Methods'}).json()
    assert not downloads and not run['papers'] and not run['selected_ids']
    assert client.post(f"/api/research/runs/{run['id']}/analyze",
                       json={'selected_ids': ['unknown']}).status_code == 400
    selected = [c['id'] for c in run['candidates']]
    result = client.post(f"/api/research/runs/{run['id']}/analyze",
                         json={'selected_ids': selected})
    assert result.status_code == 200
    assert len(downloads) == 2
    assert result.json()['selected_ids'] == selected
    assert len(result.json()['papers']) == 2
    assert client.get(f"/api/research/runs/{run['id']}").json() == result.json()


def test_empty_search_and_source_failure_are_distinct(workspace):
    import requests
    client, flow = workspace
    empty = client.post('/api/research/search', json={'topic': 'No matches'})
    assert empty.status_code == 200 and empty.json()['candidates'] == []

    def unavailable(*args, **kwargs):
        raise requests.Timeout('source timeout')

    flow.search_source = unavailable
    failed = client.post('/api/research/search', json={'topic': 'Unavailable'})
    assert failed.status_code == 502
    assert client.get('/api/research/runs').json()['total'] == 1
