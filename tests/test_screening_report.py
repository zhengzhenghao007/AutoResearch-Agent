import importlib
import json
import subprocess
import sys
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from schemas.research import Candidate, CandidateDecision
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


def report(run):
    return importlib.import_module('services.screening_report').build_screening_report(run)


def fixture_run(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.search('Screening')
    run.candidates = [Candidate(id=x, title=x, pdf_url=f'https://arxiv.org/pdf/2401.1234{i}')
                      for i, x in enumerate('abcd')]
    run.selected_ids = ['a', 'c']
    run.candidate_decisions = [
        CandidateDecision(candidate_id='a', decision='include', reason='Initial'),
        CandidateDecision(candidate_id='b', decision='include', reason='Relevant'),
        CandidateDecision(candidate_id='a', decision='exclude', reason='Correction'),
    ]
    flow.store.save(run)
    return flow, run


def test_summary_history_and_selection_are_independent(tmp_path):
    _, run = fixture_run(tmp_path)
    before = run.model_dump_json()
    result = report(run)
    assert result.counts.model_dump() == dict(total=4, include=1, exclude=1, undecided=2, selected=2)
    assert [r.candidate.id for r in result.items] == list('abcd')
    assert [r.status for r in result.items] == ['exclude', 'include', 'undecided', 'undecided']
    assert [r.selection_notice for r in result.items] == [
        'excluded_but_selected', 'included_but_not_selected', 'selected_without_decision', None]
    assert [e.reason for e in result.items[0].history] == ['Initial', 'Correction']
    assert result.items[0].latest.reason == 'Correction'
    assert run.model_dump_json() == before
    # Stored append order is authoritative, not user-controlled timestamps.
    run.candidate_decisions[0].decided_at = run.candidate_decisions[-1].decided_at + timedelta(days=1)
    assert report(run).items[0].status == 'exclude'
    assert result.model_dump_json() == report(run.model_validate_json(before)).model_dump_json()
    result.items[0].history[0].reason = 'Mutated export'
    assert run.candidate_decisions[0].reason == 'Initial'


def test_empty_legacy_and_invalid_references(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.search('Empty')
    legacy = run.model_dump()
    legacy.pop('candidate_decisions')
    assert report(run.model_validate(legacy)).counts.total == 0
    assert report(run).items == []
    legacy['candidates'] = [Candidate(id='old', title='Old', pdf_url='https://arxiv.org/pdf/2401.12345').model_dump()]
    legacy['selected_ids'] = ['old']
    old_report = report(run.model_validate(legacy))
    assert old_report.counts.undecided == 1
    assert old_report.items[0].latest is None
    assert old_report.items[0].history == []
    assert old_report.items[0].selection_notice == 'selected_without_decision'
    run.candidate_decisions = [CandidateDecision(candidate_id='absent', decision='exclude', reason='Invalid')]
    with pytest.raises(ValueError, match='Invalid candidate decision reference'):
        report(run)


def test_api_cli_identical_and_snapshot_unchanged(tmp_path):
    flow, run = fixture_run(tmp_path)
    path = tmp_path / f'{run.id}.json'
    before = path.read_bytes(), path.stat().st_mtime_ns
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            response = client.get(f'/api/research/runs/{run.id}/screening-report')
            assert response.status_code == 200
            assert response.json() == report(run).model_dump(mode='json')
            assert client.get('/api/research/runs/' + '0'*32 + '/screening-report').status_code == 404
            assert client.get('/api/research/runs/bad/screening-report').status_code == 400
    finally:
        app.dependency_overrides.clear()
    output = subprocess.run([sys.executable, 'research_cli.py', '--store', str(tmp_path),
                             'screening-report', run.id], capture_output=True, text=True)
    assert output.returncode == 0, output.stderr
    assert json.loads(output.stdout) == response.json()
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
