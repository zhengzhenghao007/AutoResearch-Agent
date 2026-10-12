import importlib
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from schemas.research import CATEGORIES, Source, Document, Page, Evidence, Claim, PaperEvidence
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


def report(run):
    return importlib.import_module('services.claim_review').build_claim_review(run)


def make_run(tmp_path, quote, category='experiment'):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    run = flow.search('Review')
    run.papers = [PaperEvidence(
        document=Document(source=Source(id='source',title='Paper',uri='upload:paper.pdf',sha256='a'*64),
                          pages=[Page(number=1,text=quote)],total_pages=1),
        evidence=[Evidence(id='e',source_id='source',page=1,quote=quote)],
        claims=[Claim(id='c',text=quote,category=category,evidence_ids=['e'])],
        missing_fields=[c for c in CATEGORIES if c != category])]
    return flow, flow._finish(run)


@pytest.mark.parametrize('quote', [
    'We plan to evaluate the algorithm next year.',
    'Future work will investigate experiments on new datasets.',
    'We intend to measure accuracy in a later experiment.',
    'We will evaluate this method on additional data.',
])
def test_planned_observation_is_flagged_with_evidence(tmp_path, quote):
    _, run = make_run(tmp_path, quote)
    before = run.model_dump_json()
    result = report(run)
    assert result.semantic_validation == 'not_assessed'
    assert result.claim_count == 1
    assert result.flagged_claim_count == 1
    flag = result.flags[0]
    assert flag.code == 'planning_language_in_observation'
    assert flag.claim_id == 'c' and flag.source_id == 'source'
    assert flag.evidence[0].quote == quote and flag.evidence[0].page == 1
    assert flag.matched_text.lower() in quote.lower()
    assert run.model_dump_json() == before


@pytest.mark.parametrize('quote,category', [
    ('We plan to evaluate the algorithm next year.','future_work'),
    ('We evaluated the algorithm on a public dataset.','experiment'),
    ('The results show an improvement over the baseline.','result'),
    ('The model predicts future work schedules accurately.','method'),
])
def test_no_flag_is_not_semantic_approval(tmp_path,quote,category):
    _,run=make_run(tmp_path,quote,category)
    result=report(run)
    assert result.flags == []
    assert result.semantic_validation == 'not_assessed'


def test_result_flag_empty_run_and_invalid_quote(tmp_path):
    flow,run=make_run(tmp_path,'We will evaluate the predicted results later.','result')
    assert report(run).flags[0].category == 'result'
    assert report(flow.search('Empty')).claim_count == 0
    run.papers[0].evidence[0].quote='This fabricated quote is absent from the page.'
    with pytest.raises(ValueError,match='Invalid persisted evidence'):
        report(run)


def test_readonly_api_cli_and_snapshot(tmp_path):
    flow,run=make_run(tmp_path,'We plan to evaluate the algorithm next year.')
    path=tmp_path/f'{run.id}.json'
    before=path.read_bytes(),path.stat().st_mtime_ns
    app.dependency_overrides[get_workflow]=lambda:flow
    try:
        with TestClient(app) as client:
            response=client.get(f'/api/research/runs/{run.id}/claim-review')
            assert response.status_code == 200
            assert response.json() == report(run).model_dump(mode='json')
            assert client.get('/api/research/runs/'+'0'*32+'/claim-review').status_code == 404
    finally:
        app.dependency_overrides.clear()
    output=subprocess.run([sys.executable,'research_cli.py','--store',str(tmp_path),'claim-review',run.id],capture_output=True,text=True)
    assert output.returncode == 0,output.stderr
    assert json.loads(output.stdout) == response.json()
    assert (path.read_bytes(),path.stat().st_mtime_ns) == before
