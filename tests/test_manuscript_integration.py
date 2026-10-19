"""Public API regression of the offline manuscript lifecycle."""
import json
import subprocess
import sys

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from test_claim_review import make_run


def test_api_revision_approval_and_source_change_lifecycle(tmp_path):
    flow, run = make_run(tmp_path, 'The authors reported a measured outcome.', 'result')
    original = flow.store._path(run.id).read_bytes()
    app.dependency_overrides[get_workflow] = lambda: flow
    base = f'/api/research/runs/{run.id}/manuscript'
    try:
        with TestClient(app) as client:
            response = client.get(base)
            assert response.status_code == 200, response.text
            state = response.json()
            assert state['revisions'] == []
            response = client.post(base + '/revisions', json={
                'expected_revision': None, 'expected_input_sha256': state['current_input_sha256'],
                'reason': 'Create offline writing material', 'sections': None})
            assert response.status_code == 200, response.text
            state = response.json()
            first = state['revisions'][-1]
            export = base + '/export'
            assert client.get(export, params={'revision_id': first['id']}).status_code == 400
            approval = {'revision_id': first['id'], 'reviewer': 'Synthetic test reviewer',
                        'expected_review_count': 0,
                        'note': 'Test fixture approval only; not a real scientific review.'}
            assert client.post(base + '/approval', json=approval).status_code == 422
            approval['confirm'] = True
            assert client.post(base + '/approval', json={**approval, 'expected_review_count': 1}).status_code == 400
            assert client.post(base + '/approval', json={k: v for k, v in approval.items()
                                                        if k != 'expected_review_count'}).status_code == 422
            assert client.post(base + '/approval', json=approval).status_code == 200
            response = client.get(export, params={'revision_id': first['id']})
            assert response.status_code == 200, response.text
            assert 'not_assessed' in response.json()['markdown']
            assert 'No user experimental observations' in response.json()['markdown']
            assert 'a' * 64 in response.json()['markdown']
            assert flow.store._path(run.id).read_bytes() == original

            sections = first['sections']
            sections[0]['title'] = 'Revised background'
            response = client.post(base + '/revisions', json={
                'expected_revision': first['id'], 'expected_input_sha256': state['current_input_sha256'],
                'reason': 'Rename the chapter', 'sections': sections})
            assert response.status_code == 200, response.text
            latest = response.json()['revisions'][-1]
            assert latest['content_sha256'] != first['content_sha256']
            assert client.get(export, params={'revision_id': latest['id']}).status_code == 400
            assert client.get(export, params={'revision_id': first['id']}).status_code == 400
            assert client.post(base + '/approval', json=approval).status_code == 400
            reopened = client.get(base).json()
            assert reopened['revisions'][0]['sections'][0]['title'] != 'Revised background'
            assert len(reopened['approvals']) == 1

            run.topic = 'Updated research context'
            flow.store.save(run)
            reopened = client.get(base).json()
            assert reopened['current_input_sha256'] != latest['input_sha256']
            approval['revision_id'] = latest['id']
            assert client.post(base + '/approval', json=approval).status_code == 400
            assert client.post(base + '/review', json={'revision_id': latest['id'], 'allow_model': False}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_cli_offline_save_and_export_gate(tmp_path):
    flow, run = make_run(tmp_path, 'The authors describe their method.', 'method')

    def cli(*args):
        return subprocess.run([sys.executable, 'research_cli.py', '--store', str(flow.store.root),
                               *args], capture_output=True, text=True)

    shown = cli('manuscript-show', run.id)
    assert shown.returncode == 0, shown.stderr
    state = json.loads(shown.stdout)
    saved = cli('manuscript-save', run.id, '--expected-input-sha256', state['current_input_sha256'],
                '--reason', 'Synthetic CLI fixture')
    assert saved.returncode == 0, saved.stderr
    revision = json.loads(saved.stdout)['revisions'][-1]
    denied = cli('manuscript-export', run.id, revision['id'])
    assert denied.returncode == 1
    approved = cli('manuscript-approve', run.id, revision['id'], '--reviewer', 'Synthetic fixture',
                   '--note', 'Test fixture only', '--expected-review-count', '0', '--confirm')
    assert approved.returncode == 0, approved.stderr
    exported = cli('manuscript-export', run.id, revision['id'])
    assert exported.returncode == 0, exported.stderr
    assert json.loads(exported.stdout)['revision_id'] == revision['id']
