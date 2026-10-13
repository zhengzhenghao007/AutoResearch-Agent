import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from schemas.research import Candidate
from services.claim_review import build_claim_review
from test_claim_review import make_run


def revise(flow,run,category='future_work'):
    claim=run.papers[0].claims[0]
    return flow.revise_claim_category(run.id,claim.model_dump(),category,'Correct planned work')


def test_revision_preserves_quote_and_rebuilds_derivatives(tmp_path):
    flow,run=make_run(tmp_path,'We will evaluate this method in a future experiment.')
    before=run.papers[0].model_copy(deep=True)
    changed=revise(flow,run)
    assert changed.papers[0].claims[0].category == 'future_work'
    assert changed.papers[0].evidence == before.evidence
    assert changed.papers[0].document == before.document
    assert 'experiment' in changed.papers[0].missing_fields
    assert 'future_work' not in changed.papers[0].missing_fields
    assert len(changed.generated_claims) == 1
    assert build_claim_review(changed).flags == []
    event=changed.category_revisions[0]
    assert event.before == before
    assert event.after == changed.papers[0]
    assert event.reason == 'Correct planned work'
    assert flow.store.load(run.id) == changed
    with pytest.raises(ValueError,match='stale'):
        revise(flow,run,'result')


def test_noop_budget_and_tampered_history(tmp_path):
    flow,run=make_run(tmp_path,'We will evaluate this method in a future experiment.')
    path=tmp_path/f'{run.id}.json'
    before=path.read_bytes()
    with pytest.raises(ValueError,match='unchanged'):
        revise(flow,run,'experiment')
    assert path.read_bytes() == before
    for n in range(20):
        run=revise(flow,run,'future_work' if n%2==0 else 'experiment')
    assert len(run.category_revisions) == 20
    with pytest.raises(ValueError,match='budget'):
        revise(flow,run)
    raw=json.loads(path.read_text())
    raw['category_revisions'][0]['after']['claims'][0]['text']='Invented result'
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='revision'):
        flow.store.load(run.id)


def test_reanalysis_replays_only_matching_evidence(tmp_path):
    flow,run=make_run(tmp_path,'We will evaluate this method in a future experiment.')
    run.papers[0].document.source.uri='https://arxiv.org/pdf/2401.12345'
    run.candidates=[Candidate(id='a',title='Paper',pdf_url=run.papers[0].document.source.uri)]
    original=run.papers[0].model_copy(deep=True)
    flow._finish(run)
    run=revise(flow,run)
    class Processor:
        def download(self,*args):return original.document.model_copy(deep=True)
    class Extractor:
        def extract(self,document):return original.model_copy(deep=True)
    flow.processor=Processor();flow.extractor=Extractor()
    again=flow.analyze(run.id,['a'])
    assert again.papers[0].claims[0].category == 'future_work'
    assert len(again.category_revisions) == 1
    original.document.source.sha256='b'*64
    different=flow.analyze(run.id,['a'])
    assert different.papers[0].claims[0].category == 'experiment'
    assert len(different.category_revisions) == 1


def test_api_and_cli_revision(tmp_path):
    flow,run=make_run(tmp_path,'We will evaluate this method in a future experiment.')
    body=dict(expected_claim=run.papers[0].claims[0].model_dump(mode='json'),category='future_work',reason='Planned only')
    app.dependency_overrides[get_workflow]=lambda:flow
    try:
        with TestClient(app) as client:
            response=client.post(f'/api/research/runs/{run.id}/category-revisions',json=body)
            assert response.status_code == 200
            assert len(response.json()['category_revisions']) == 1
            assert client.post(f'/api/research/runs/{run.id}/category-revisions',json=body).status_code == 400
    finally:app.dependency_overrides.clear()
    expected=tmp_path/'expected.json'
    expected.write_text(json.dumps(response.json()['papers'][0]['claims'][0]))
    output=subprocess.run([sys.executable,'research_cli.py','--store',str(tmp_path),'revise-category',run.id,
                           str(expected),'result','--reason','Reconsidered'],capture_output=True,text=True)
    assert output.returncode == 0,output.stderr
    assert len(json.loads(output.stdout)['category_revisions']) == 2


def test_legacy_reads_and_invalid_requests_do_not_write(tmp_path):
    flow,run=make_run(tmp_path,'We will evaluate this method in a future experiment.')
    path=tmp_path/f'{run.id}.json'
    raw=json.loads(path.read_text())
    raw.pop('category_revisions')
    path.write_text(json.dumps(raw))
    before=path.read_bytes(),path.stat().st_mtime_ns
    assert flow.store.load(run.id).category_revisions == []
    with pytest.raises(ValueError):
        flow.revise_claim_category(run.id,run.papers[0].claims[0].model_dump(),'future_work',' ')
    missing=run.papers[0].claims[0].model_copy(update={'id':'absent'})
    with pytest.raises(ValueError,match='not currently processed'):
        flow.revise_claim_category(run.id,missing.model_dump(),'future_work','Reason')
    assert (path.read_bytes(),path.stat().st_mtime_ns) == before


def test_replay_chain_and_historical_snapshot_isolation(tmp_path):
    from services.category_revisions import replay_revisions
    flow,run=make_run(tmp_path,'We will evaluate this method in a future experiment.')
    original=run.papers[0].model_copy(deep=True)
    run=revise(flow,run,'future_work')
    run=revise(flow,run,'method')
    result=replay_revisions([original],run.category_revisions)
    assert result[0].claims[0].category == 'method'
    assert original.claims[0].category == 'experiment'
    assert run.category_revisions[0].after.claims[0].category == 'future_work'
    assert replay_revisions([],run.category_revisions) == []
    result[0].evidence[0].quote='Altered detached output'
    assert run.category_revisions[1].after.evidence[0].quote == original.evidence[0].quote
