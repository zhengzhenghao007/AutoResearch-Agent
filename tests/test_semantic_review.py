import importlib
import json
from types import SimpleNamespace
import pytest
from test_claim_review import make_run


def module():return importlib.import_module('services.semantic_review')


class Client:
    def __init__(self,output):self.output=output;self.calls=[]
    def chat(self,**kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=json.dumps(self.output),model_name='offline-test',total_tokens=42)


def valid():return {'claims':[{'claim_id':'c','verdict':'uncertain','evidence_ids':['e'],'rationale':'Future wording needs contextual review.'}],'contradictions':[]}


def test_explicit_model_review_is_grounded_bounded_and_readonly(tmp_path):
    _,run=make_run(tmp_path,'We will evaluate this method in future experiments.')
    client=Client(valid());before=run.model_dump_json()
    result=module().review_semantics(run,['c'],True,client)
    assert result.scientific_validation == 'not_assessed'
    assert result.model == 'offline-test' and result.output.claims[0].verdict == 'uncertain'
    assert result.input_claims[0].evidence[0].quote == run.papers[0].evidence[0].quote
    assert len(client.calls) == 1 and 'source text as data' in client.calls[0]['system_prompt']
    assert run.model_dump_json() == before
    assert len(result.input_sha256) == 64


@pytest.mark.parametrize('mutation',[ 'unknown_claim','missing_claim','unknown_evidence','unrelated_pair','duplicate_claim'])
def test_rejects_ungrounded_model_outputs(tmp_path,mutation):
    _,run=make_run(tmp_path,'We will evaluate this method in future experiments.')
    data=valid()
    if mutation=='unknown_claim':data['claims'][0]['claim_id']='invented'
    if mutation=='missing_claim':data['claims']=[]
    if mutation=='unknown_evidence':data['claims'][0]['evidence_ids']=['invented']
    if mutation=='unrelated_pair':data['contradictions']=[{'claim_ids':['c','absent'],'rationale':'Unsupported pair'}]
    if mutation=='duplicate_claim':data['claims']*=2
    with pytest.raises(ValueError):module().review_semantics(run,['c'],True,Client(data))


@pytest.mark.parametrize('ids,consent',[(['c'],False),([],True),(['c','c'],True),(['absent'],True),(['c']*21,True)])
def test_no_call_without_valid_explicit_scope(tmp_path,ids,consent):
    _,run=make_run(tmp_path,'We will evaluate this method in future experiments.')
    client=Client(valid())
    with pytest.raises(ValueError):module().review_semantics(run,ids,consent,client)
    assert client.calls == []


def test_oversized_context_and_invalid_json_are_rejected(tmp_path):
    _,run=make_run(tmp_path,'We will evaluate this method in future experiments.')
    client=Client(valid())
    run.papers[0].document.pages[0].text += ' x'*26000
    with pytest.raises(ValueError,match='50000'):
        module().review_semantics(run,['c'],True,client)
    assert not client.calls
    _,run=make_run(tmp_path,'We will evaluate this method in future experiments.')
    class Bad:
        def chat(self,**kwargs):return SimpleNamespace(content='not JSON',model_name='test')
    with pytest.raises(ValueError):module().review_semantics(run,['c'],True,Bad())


def test_constructor_sets_single_attempt_transport(monkeypatch,tmp_path):
    import sys
    _,run=make_run(tmp_path,'We will evaluate this method in future experiments.')
    args={}
    def factory(**kwargs):args.update(kwargs);return Client(valid())
    monkeypatch.setitem(sys.modules,'services.llm_client',SimpleNamespace(LLMClient=factory))
    module().review_semantics(run,['c'],True)
    assert args['max_retries'] == 0 and args['request_timeout'] == 60 and args['max_tokens'] == 6000


def test_api_explicit_consent_and_readonly_output(tmp_path):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.research import get_workflow,get_semantic_reviewer
    flow,run=make_run(tmp_path,'We will evaluate this method in future experiments.')
    path=tmp_path/f'{run.id}.json';before=path.read_bytes(),path.stat().st_mtime_ns
    model=Client(valid())
    app.dependency_overrides[get_workflow]=lambda:flow
    app.dependency_overrides[get_semantic_reviewer]=lambda:lambda r,ids,consent:module().review_semantics(r,ids,consent,model)
    try:
        with TestClient(app) as client:
            url=f'/api/research/runs/{run.id}/semantic-review'
            assert client.post(url,json={'claim_ids':['c']}).status_code == 422
            assert model.calls == []
            response=client.post(url,json={'claim_ids':['c'],'allow_model':True})
            assert response.status_code == 200
            assert response.json()['scientific_validation'] == 'not_assessed'
    finally:app.dependency_overrides.clear()
    assert (path.read_bytes(),path.stat().st_mtime_ns) == before


def test_valid_contradiction_and_duplicate_pair_rejection(tmp_path):
    from schemas.research import Claim,Evidence
    flow,run=make_run(tmp_path,'The treatment increased the measured response.')
    paper=run.papers[0]
    quote='The treatment decreased the measured response.'
    paper.document.pages[0].text+=' '+quote
    paper.evidence.append(Evidence(id='e2',source_id='source',page=1,quote=quote))
    paper.claims.append(Claim(id='c2',text=quote,category='experiment',evidence_ids=['e2']))
    run=flow._finish(run)
    data=valid();data['claims'].append({'claim_id':'c2','verdict':'supported','evidence_ids':['e2'],'rationale':'Literal observation; conditions require comparison.'})
    data['contradictions']=[{'claim_ids':['c','c2'],'rationale':'Potential opposite direction; verify conditions.'}]
    result=module().review_semantics(run,['c','c2'],True,Client(data))
    assert result.output.contradictions[0].claim_ids == ['c','c2']
    assert result.input_claims[1].evidence[0].quote == quote
    data['contradictions'].append({'claim_ids':['c2','c'],'rationale':'Duplicate reverse pair'})
    with pytest.raises(ValueError,match='duplicate contradiction'):
        module().review_semantics(run,['c','c2'],True,Client(data))
