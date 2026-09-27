import json
import subprocess
import sys
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from services.research_store import ResearchStore
from services.citation_registry import build_citation_registry
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


def setup_run(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [
        {'title': 'Navigation', 'pdf_url': 'https://arxiv.org/pdf/2401.12345v1'}])
    run = flow.search('navigation')
    return flow, run, run.candidates[0].id


def test_legacy_read_does_not_rewrite_snapshot(tmp_path):
    flow, run, _ = setup_run(tmp_path)
    path = tmp_path / f'{run.id}.json'
    data = run.model_dump(mode='json')
    data.pop('candidate_decisions', None)
    path.write_text(json.dumps(data), encoding='utf-8')
    before = path.read_bytes(), path.stat().st_mtime_ns
    assert flow.store.load(run.id).candidate_decisions == []
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_history_appends_and_does_not_change_analysis_or_citations(tmp_path, monkeypatch):
    flow, run, candidate = setup_run(tmp_path)
    run = flow.import_pdf(pdf_bytes(['We propose a navigation method.']), 'Uploaded', run.id)
    registry = build_citation_registry(run)
    before = datetime.now(timezone.utc)
    included = flow.record_candidate_decision(run.id, candidate, 'include', 'Relevant method')
    excluded = flow.record_candidate_decision(run.id, candidate, 'exclude', 'Protocol differs')
    assert included.selected_ids == excluded.selected_ids == []
    assert excluded.papers == run.papers
    assert build_citation_registry(excluded) == registry
    history = flow.store.load(run.id).candidate_decisions
    assert [(e.candidate_id, e.decision, e.reason) for e in history] == [
        (candidate, 'include', 'Relevant method'), (candidate, 'exclude', 'Protocol differs')]
    assert all(before <= e.decided_at <= datetime.now(timezone.utc) for e in history)
    # Only the remote download is replaced; extraction, validation and persistence are real.
    monkeypatch.setattr(flow.processor, 'download', lambda url, title:
        flow.processor.parse_bytes(pdf_bytes(['We propose a mapping method.']), title, url))
    analyzed = flow.analyze(run.id, [candidate])
    assert analyzed.selected_ids == [candidate]
    assert len(analyzed.papers) == 2
    assert analyzed.candidate_decisions == history
    revised = flow.record_candidate_decision(run.id, candidate, 'include', 'Reconsidered')
    assert revised.selected_ids == analyzed.selected_ids
    assert revised.papers == analyzed.papers
    assert len(revised.candidate_decisions) == 3
    uploaded = flow.import_pdf(pdf_bytes(['We propose a localization method.']), 'Another upload', run.id)
    assert uploaded.candidate_decisions == revised.candidate_decisions
    assert len(uploaded.papers) == 3


@pytest.mark.parametrize('candidate,decision,reason', [
    ('unknown', 'include', 'Reason'), (None, 'maybe', 'Reason'),
    (None, 'include', '   '), (None, 'exclude', 'x' * 2001),
])
def test_invalid_mutation_preserves_snapshot(tmp_path, candidate, decision, reason):
    flow, run, valid_id = setup_run(tmp_path)
    path = tmp_path / f'{run.id}.json'
    before = path.read_bytes()
    with pytest.raises(ValueError):
        flow.record_candidate_decision(run.id, candidate or valid_id, decision, reason)
    assert path.read_bytes() == before


def test_corrupt_decision_reference_rejected_on_load(tmp_path):
    flow, run, candidate = setup_run(tmp_path)
    flow.record_candidate_decision(run.id, candidate, 'exclude', 'Reason')
    path = tmp_path / f'{run.id}.json'
    data = json.loads(path.read_text())
    data['candidate_decisions'][0]['candidate_id'] = 'unknown'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        flow.store.load(run.id)


def test_api_cli_persist_shared_history_and_reject_invalid_input(tmp_path):
    flow, run, candidate = setup_run(tmp_path)
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            url = f'/api/research/runs/{run.id}'
            payload = {'candidate_id': candidate, 'decision': 'include', 'reason': 'Relevant'}
            response = client.post(url + '/candidate-decisions', json=payload)
            assert response.status_code == 200
            assert client.get(url).json() == response.json()
            first = response.json()['candidate_decisions'][0]
            assert {k: first[k] for k in payload} == payload
            assert set(first) == {*payload, 'decided_at'}
            for invalid in ({**payload, 'reason': ' '}, {**payload, 'decision': 'maybe'},
                            {**payload, 'decided_at': '2020-01-01T00:00:00Z'}):
                assert client.post(url + '/candidate-decisions', json=invalid).status_code == 422
            assert client.post(url + '/candidate-decisions', json={**payload, 'candidate_id': 'missing'}).status_code == 400
            assert client.post('/api/research/runs/' + 'f'*32 + '/candidate-decisions', json=payload).status_code == 404
            command = [sys.executable, 'research_cli.py', '--store', str(tmp_path),
                       'candidate-decision', run.id, candidate, 'exclude', '--reason', 'Protocol differs']
            result = subprocess.run(command, capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            output = json.loads(result.stdout)
            assert client.get(url).json() == output
            assert output['candidate_decisions'][0] == first
            assert output['candidate_decisions'][1]['reason'] == 'Protocol differs'
            assert output['candidate_decisions'][1]['decision'] == 'exclude'
            assert set(output['candidate_decisions'][1]) == set(first)
            assert subprocess.run(command[:-1] + [' '], capture_output=True).returncode != 0
            assert client.get(url).json() == output
    finally:
        app.dependency_overrides.clear()
