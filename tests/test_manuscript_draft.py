import importlib
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from test_claim_review import make_run
from test_experiments import flow_run, raw
from services.experiments import import_experiment


def build(run):
    return importlib.import_module('services.manuscript_draft').build_manuscript_draft(run)


def test_empty_run_has_explicit_placeholders_and_no_approval(tmp_path):
    _, run = flow_run(tmp_path)
    draft = build(run)
    assert len(draft.sections) == 5
    assert all(section.blocks[0].kind == 'placeholder' for section in draft.sections)
    assert draft.scientific_validation == draft.contradiction_review == 'not_assessed'
    assert draft.approval == 'not_requested'
    assert build(run) == draft


def test_paper_blocks_preserve_claim_and_all_citations_without_user_results(tmp_path):
    flow, run = make_run(tmp_path,'The measured outcome was reported in the paper.',category='result')
    draft = build(run)
    block = next(s for s in draft.sections if s.id == 'reported_findings').blocks[0]
    assert block.kind == 'paper_claim' and block.text == run.papers[0].claims[0].text
    assert block.paper.claim_id == 'c'
    assert block.paper.source.sha256 == 'a'*64
    assert block.paper.evidence == run.papers[0].evidence
    assert next(s for s in draft.sections if s.id == 'user_results').blocks[0].kind == 'placeholder'
    before=flow.store._path(run.id).read_bytes();mtime=flow.store._path(run.id).stat().st_mtime_ns
    build(flow.store.load(run.id))
    assert flow.store._path(run.id).read_bytes() == before
    assert flow.store._path(run.id).stat().st_mtime_ns == mtime


def test_statistics_are_reproducible_and_hash_tracks_input(tmp_path):
    flow, run = flow_run(tmp_path)
    old = build(run).input_sha256
    run = import_experiment(flow.store,run.id,raw())
    draft = build(run)
    assert draft.input_sha256 != old
    blocks = next(s for s in draft.sections if s.id == 'user_results').blocks
    assert blocks[0].kind == 'user_statistics'
    assert blocks[0].computation.dataset_id == run.experiments[0].id
    assert blocks[0].computation.column.mean == '11.75'
    assert blocks[0].computation.column.references[0].sample_id == 's1'
    assert blocks[1].computation.column.sample_standard_deviation is None
    assert 'unavailable' in blocks[1].text.lower()
    corrupt=run.model_copy(deep=True);corrupt.experiments[0].data.rows[0].values['score']=33
    with pytest.raises(ValueError):
        build(corrupt)


def test_missing_values_remain_placeholders_not_results(tmp_path):
    flow,run=flow_run(tmp_path)
    value={'title':'Unknown','columns':[{'name':'x','unit':None}],
           'rows':[{'sample_id':'s','values':{'x':None}}]}
    run=import_experiment(flow.store,run.id,raw(value))
    block=next(s for s in build(run).sections if s.id=='user_results').blocks[0]
    assert block.kind=='placeholder' and block.computation.column.mean is None
    assert 'No nonmissing observations' in block.text


def test_preview_api_cli_are_offline_and_read_only(tmp_path):
    flow,run=flow_run(tmp_path)
    app.dependency_overrides[get_workflow]=lambda:flow
    path=flow.store._path(run.id);before=(path.read_bytes(),path.stat().st_mtime_ns)
    try:
        with TestClient(app) as client:
            response=client.get(f'/api/research/runs/{run.id}/manuscript-draft')
            assert response.status_code==200,response.text
            assert response.json()==build(run).model_dump(mode='json')
            assert client.get('/api/research/runs/'+'0'*32+'/manuscript-draft').status_code==404
    finally:
        app.dependency_overrides.clear()
    result=subprocess.run([sys.executable,'research_cli.py','--store',str(tmp_path),'manuscript-draft',run.id],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['input_sha256']==build(run).input_sha256
    assert (path.read_bytes(),path.stat().st_mtime_ns)==before


def test_all_bound_evidence_and_truncation_are_visible(tmp_path):
    from schemas.research import Evidence
    flow,run=make_run(tmp_path,'This paper reports a reproducible method.',category='method')
    paper=run.papers[0]
    paper.evidence.append(Evidence(id='e2',source_id='source',page=1,quote=paper.claims[0].text))
    paper.claims[0].evidence_ids.append('e2')
    paper.document.total_pages=2;paper.document.truncated=True
    run=flow._finish(run)
    block=next(s for s in build(run).sections if s.id=='reported_methods').blocks[0]
    assert [e.id for e in block.paper.evidence]==['e','e2']
    assert block.paper.truncated and block.paper.parsed_pages==1 and block.paper.total_pages==2
    corrupt=run.model_copy(deep=True);corrupt.papers[0].claims[0].text='An unsupported invented result.'
    with pytest.raises(ValueError):
        build(corrupt)


def test_draft_hash_changes_when_category_revision_moves_a_quote(tmp_path):
    flow,run=make_run(tmp_path,'We plan to test the proposed experiment.',category='experiment')
    old=build(run)
    changed=flow.revise_claim_category(run.id,run.papers[0].claims[0].model_dump(),'future_work','This is planned work')
    new=build(changed)
    assert old.input_sha256!=new.input_sha256
    assert next(s for s in new.sections if s.id=='reported_methods').blocks[0].kind=='placeholder'
    assert next(s for s in new.sections if s.id=='limitations').blocks[0].text==run.papers[0].claims[0].text
