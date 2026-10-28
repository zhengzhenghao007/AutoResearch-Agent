import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from test_experiments import flow_run, raw
from services.experiments import import_experiment

@pytest.fixture
def workspace(tmp_path):
    flow, run = flow_run(tmp_path)
    run = import_experiment(flow.store, run.id, raw())
    app.dependency_overrides[get_workflow] = lambda: flow
    with TestClient(app) as client:
        yield client, flow, run, f'/api/research/runs/{run.id}'
    app.dependency_overrides.clear()

def spec(run, **kwargs):
    return dict(kind='table', title='Observations', dataset_id=run.experiments[0].id,
                columns=['temperature','score'], **kwargs)

def test_workspace_preview_persist_reload_and_immutable_source(workspace):
    client, flow, run, base = workspace
    original = flow.store._path(run.id).read_bytes()
    preview = client.post(base+'/workspace/preview', json=spec(run))
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data['headers'] == ['sample_id','temperature (C)','score (unit unspecified)']
    assert data['rows'] == [['s1',0,None],['s2',23.5,2]]
    assert data['dataset_sha256'] == run.experiments[0].sha256
    assert flow.store._path(run.id).read_bytes() == original
    result = client.post(base+'/workspace/items', json=spec(run))
    assert result.status_code == 200, result.text
    saved = result.json()['workspace_items'][0]
    assert len(saved['id']) == 32
    assert client.get(base+'/workspace/items/'+saved['id']).json() == data
    assert flow.store.load(run.id).experiments == run.experiments
    assert client.get(base).json()['workspace_items'] == [saved]
    assert client.delete(base+'/workspace/items/'+saved['id']).status_code == 405

@pytest.mark.parametrize('changes', [dict(columns=['missing']), dict(columns=['score','score']),
    dict(dataset_id=None), dict(svg='<svg/>'),dict(kind='figure',columns=['score','temperature']),
    dict(kind='figure',columns=['score'],chart_type='line'),dict(kind='figure',columns=['score'],x_column='missing')])
def test_workspace_rejects_invalid_bindings_without_write(workspace,changes):
    client, flow, run, base = workspace
    before = flow.store._path(run.id).read_bytes()
    response = client.post(base+'/workspace/items', json={**spec(run),**changes})
    assert response.status_code in (400,422), response.text
    assert flow.store._path(run.id).read_bytes() == before

def test_figure_svg_is_deterministic_and_missing_values_explicit(workspace):
    client, flow, run, base = workspace
    request = {**spec(run), 'kind':'figure','columns':['score'],'title':'<script>alert(1)</script>'}
    first = client.post(base+'/workspace/preview',json=request)
    assert first.status_code == 200,first.text
    result=first.json()
    assert '<svg' in result['svg'] and '<script>' not in result['svg']
    assert result['warnings'] and '1' in ' '.join(result['warnings'])
    assert client.post(base+'/workspace/preview',json=request).json()==result

def test_asset_binding_export_gate_and_note_hash_stability(workspace):
    client, flow, run, base = workspace
    initial=client.get(base+'/manuscript-draft').json()['input_sha256']
    assert client.post(base+'/workspace/items',json={'kind':'note','title':'Record','text':'Real observation'}).status_code==200
    assert client.get(base+'/manuscript-draft').json()['input_sha256']==initial
    saved=client.post(base+'/workspace/items',json={**spec(run),'kind':'figure','columns':['temperature'],'text':'Measured temperature'}).json()
    item=saved['workspace_items'][-1]
    draft=client.get(base+'/manuscript-draft').json()
    assert draft['input_sha256']!=initial
    block=next(b for s in draft['sections'] for b in s['blocks'] if b['kind']=='research_asset')
    assert block['asset']['item_id']==item['id']
    request={'expected_revision':None,'expected_input_sha256':draft['input_sha256'],'reason':'Draft'}
    result=client.post(base+'/manuscript/revisions',json=request)
    assert result.status_code==200,result.text
    revision=result.json()['revisions'][-1]
    bundle=base+'/manuscript/bundle?revision_id='+revision['id']
    assert client.get(bundle).status_code==400
    sections=revision['sections']
    sentence=next(s for section in sections for s in section['sentences'] if s['kind']=='research_asset')
    sentence['text']='Changed result'
    response=client.post(base+'/manuscript/revisions',json={**request,'expected_revision':revision['id'],'sections':sections})
    assert response.status_code==400
    approval={'revision_id':revision['id'],'expected_review_count':0,'reviewer':'Fixture','note':'Fixture only','confirm':True}
    assert client.post(base+'/manuscript/approval',json=approval).status_code==200
    exported=client.get(bundle)
    assert exported.status_code==200,exported.text
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        assert {'manuscript.md','references.json','provenance.json'}<=set(archive.namelist())
        assert any(name.endswith('.svg') for name in archive.namelist())
        assert item['dataset_sha256'] in archive.read('provenance.json').decode()
    assert client.post(base+'/workspace/items',json=spec(run)).status_code==200
    assert client.get(bundle).status_code==400

def test_legacy_manuscript_hash_remains_loadable(workspace):
    import hashlib
    client, flow, run, base = workspace
    draft = client.get(base+'/manuscript-draft').json()
    result = client.post(base+'/manuscript/revisions',json={'expected_revision':None,
        'expected_input_sha256':draft['input_sha256'],'reason':'Legacy fixture'}).json()
    source = result['revisions'][0]['source']
    for section in source['sections']:
        for block in section['blocks']:
            block.pop('asset',None)
    value = {'sections':result['revisions'][0]['sections'],'source':source}
    digest = hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert result['revisions'][0]['content_sha256']==digest
    (flow.store.root/'manuscripts'/f'{run.id}.json').write_text(json.dumps(result),encoding='utf-8')
    reopened=client.get(base+'/manuscript')
    assert reopened.status_code==200,reopened.text
    assert reopened.json()['revisions'][0]['content_sha256']==digest

@pytest.mark.parametrize('sqlite',[False,True])
def test_workspace_concurrent_notes_are_not_lost(tmp_path,sqlite):
    from concurrent.futures import ThreadPoolExecutor
    from services.research_store import ResearchStore
    from services.sqlite_store import SQLiteResearchStore
    from workflow.evidence_workflow import EvidenceWorkflow
    from services.workspace import save_workspace_item
    store=(SQLiteResearchStore if sqlite else ResearchStore)(tmp_path)
    run=EvidenceWorkflow(store=store,search=lambda *a,**k:[]).create('Concurrent notes')
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i:save_workspace_item(store,run.id,{'kind':'note','title':f'Note {i}','text':f'Record {i}'}),range(12)))
    saved=store.load(run.id)
    assert len(saved.workspace_items)==12
    assert {i.text for i in saved.workspace_items}=={f'Record {i}' for i in range(12)}

def test_workspace_limit_and_corrupt_binding(workspace):
    from services.workspace import save_workspace_item
    client,flow,run,base=workspace
    saved=client.post(base+'/workspace/items',json=spec(run)).json()['workspace_items'][0]
    corrupted=flow.store.load(run.id)
    corrupted.workspace_items[0].dataset_sha256='a'*64
    with pytest.raises(ValueError,match='hash binding|append-only'):
        flow.store.save(corrupted)
    for i in range(99):
        save_workspace_item(flow.store,run.id,{'kind':'note','title':str(i),'text':'Record'})
    before=flow.store._path(run.id).read_bytes()
    assert client.post(base+'/workspace/items',json={'kind':'note','title':'Excess','text':'Record'}).status_code==400
    assert flow.store._path(run.id).read_bytes()==before

def test_line_gap_and_sorting_are_preserved(tmp_path):
    import xml.etree.ElementTree as ET
    from services.workspace import preview_workspace
    flow,run=flow_run(tmp_path)
    data={'title':'Gap','columns':[{'name':'x'},{'name':'y'}],
          'rows':[{'sample_id':str(x),'values':{'x':x,'y':y}} for x,y in [(3,30),(1,10),(2,None),(4,40)]]}
    run=import_experiment(flow.store,run.id,json.dumps(data).encode())
    result=preview_workspace(run,{'kind':'figure','title':'Gap','dataset_id':run.experiments[0].id,
        'columns':['y'],'x_column':'x','chart_type':'line'})
    root=ET.fromstring(result.svg)
    paths=[p.attrib.get('d','') for p in root.iter('{http://www.w3.org/2000/svg}path')
           if 'stroke: #1f77b4' in p.attrib.get('style','') and 'fill: none' in p.attrib.get('style','')]
    # One singleton at X=1, then a segment X=3 to X=4. No line crosses missing X=2.
    assert len(paths)==1 and paths[0].count('M')==2 and paths[0].count('L')==1

def test_asset_cannot_be_relabelled_as_hypothesis(workspace):
    client,flow,run,base=workspace
    client.post(base+'/workspace/items',json=spec(run))
    digest=client.get(base+'/manuscript-draft').json()['input_sha256']
    request={'expected_revision':None,'expected_input_sha256':digest,'reason':'Initial'}
    revision=client.post(base+'/manuscript/revisions',json=request).json()['revisions'][0]
    for section in revision['sections']:
        for sentence in section['sentences']:
            if sentence['kind']=='research_asset':
                sentence['kind']='hypothesis'
    result=client.post(base+'/manuscript/revisions',json={**request,'expected_revision':revision['id'],'sections':revision['sections']})
    assert result.status_code==400

@pytest.mark.parametrize('sqlite',[False,True])
@pytest.mark.parametrize('mutation',['edit','remove'])
def test_saved_workspace_records_are_append_only(tmp_path,sqlite,mutation):
    from services.research_store import ResearchStore
    from services.sqlite_store import SQLiteResearchStore
    from workflow.evidence_workflow import EvidenceWorkflow
    from services.workspace import save_workspace_item
    store=(SQLiteResearchStore if sqlite else ResearchStore)(tmp_path)
    run=EvidenceWorkflow(store=store,search=lambda *a,**k:[]).create('Immutable notes')
    save_workspace_item(store,run.id,{'kind':'note','title':'Note','text':'Original'})
    changed=store.load(run.id)
    if mutation=='edit':
        changed.workspace_items[0].text='Replacement'
    else:
        changed.workspace_items=[]
    with pytest.raises(ValueError,match='append-only'):
        store.save(changed)
    assert store.load(run.id).workspace_items[0].text=='Original'

def test_workspace_routes_respect_reader_and_tenant_security(tmp_path):
    from fastapi import FastAPI
    from backend.app import security
    from backend.app.api.research import router
    isolated=FastAPI()
    config=security.SecurityConfig(True,tmp_path,{'alice':{'token':'a'*32,'role':'writer'},
        'bob':{'token':'b'*32,'role':'writer'},'reader':{'token':'r'*32,'role':'reader'}},sqlite=True)
    isolated.state.security_config=config
    isolated.add_middleware(security.SecurityMiddleware,config=config)
    isolated.include_router(router)
    with TestClient(isolated) as client:
        alice={'Authorization':'Bearer '+'a'*32};bob={'Authorization':'Bearer '+'b'*32};reader={'Authorization':'Bearer '+'r'*32}
        run=client.post('/api/research/runs',json={'topic':'Private'},headers=alice).json()
        base=f'/api/research/runs/{run["id"]}'
        note={'kind':'note','title':'Private record','text':'Private observation'}
        saved=client.post(base+'/workspace/items',json=note,headers=alice)
        assert saved.status_code==200,saved.text
        item=saved.json()['workspace_items'][0]
        assert client.post(base+'/workspace/items',json=note,headers=reader).status_code==403
        assert client.get(base+'/workspace/items/'+item['id'],headers=bob).status_code==404
        assert client.post(base+'/workspace/preview',json=note,headers=bob).status_code==404
        assert client.get(base+'/manuscript/bundle?revision_id=anything',headers=bob).status_code==404
        assert client.get(base+'/workspace/items/'+item['id']).status_code==401

def test_legacy_sqlite_record_without_workspace_field(tmp_path):
    from services.sqlite_store import SQLiteResearchStore
    from workflow.evidence_workflow import EvidenceWorkflow
    store=SQLiteResearchStore(tmp_path)
    run=EvidenceWorkflow(store=store,search=lambda *a,**k:[]).create('Legacy SQLite')
    with store.transaction() as db:
        data=json.loads(db.execute('SELECT data FROM runs WHERE id=?',(run.id,)).fetchone()['data'])
        data.pop('workspace_items')
        db.execute('UPDATE runs SET data=? WHERE id=?',(json.dumps(data),run.id))
    reopened=store.load(run.id)
    assert reopened.workspace_items==[]
    store.save(reopened)
    assert store.load(run.id).topic=='Legacy SQLite'

def test_figure_rejects_unrenderable_range_without_persisting(tmp_path):
    from services.workspace import save_workspace_item
    flow,run=flow_run(tmp_path)
    run=import_experiment(flow.store,run.id,json.dumps({'title':'Extreme','columns':[{'name':'x'}],
        'rows':[{'sample_id':'a','values':{'x':10**200}}]}).encode())
    with pytest.raises(ValueError,match='plotting range'):
        save_workspace_item(flow.store,run.id,{'kind':'figure','title':'Too large',
            'dataset_id':run.experiments[0].id,'columns':['x']})
    assert flow.store.load(run.id).workspace_items==[]

def test_unknown_x_discloses_points_only_line_render(tmp_path):
    from services.workspace import preview_workspace
    flow,run=flow_run(tmp_path)
    run=import_experiment(flow.store,run.id,json.dumps({'title':'Unknown X','columns':[{'name':'x'},{'name':'y'}],
        'rows':[{'sample_id':str(i),'values':{'x':x,'y':i}} for i,x in enumerate([1,None,3])]}).encode())
    result=preview_workspace(run,{'kind':'figure','title':'Unknown X','chart_type':'line',
        'dataset_id':run.experiments[0].id,'columns':['y'],'x_column':'x'})
    assert any('points only' in warning for warning in result.warnings)

def test_statistics_only_bundle_contains_original_data_provenance(workspace):
    client, flow, run, base = workspace
    draft = client.get(base+'/manuscript-draft').json()
    response = client.post(base+'/manuscript/revisions',json={'expected_revision':None,
        'expected_input_sha256':draft['input_sha256'],'reason':'Statistics without saved charts'})
    assert response.status_code == 200, response.text
    revision = response.json()['revisions'][-1]
    assert any(s['kind']=='user_observation' for section in revision['sections'] for s in section['sentences'])
    approval = client.post(base+'/manuscript/approval',json={'revision_id':revision['id'],
        'expected_review_count':0,'reviewer':'Fixture','note':'Fixture only','confirm':True})
    assert approval.status_code == 200, approval.text
    response = client.get(base+'/manuscript/bundle',params={'revision_id':revision['id']})
    assert response.status_code == 200,response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        provenance = json.loads(archive.read('provenance.json'))
    assert provenance['assets'] == []
    assert provenance['datasets'] == [run.experiments[0].model_dump(mode='json')]
    assert provenance['datasets'][0]['raw_json'] == raw().decode('utf-8')

def test_preview_preserves_integers_outside_javascript_exact_range(tmp_path):
    from services.workspace import preview_workspace
    flow, run = flow_run(tmp_path)
    run = import_experiment(flow.store, run.id, json.dumps({'title':'Exact counts','columns':[{'name':'count'}],
        'rows':[{'sample_id':str(i),'values':{'count':n}} for i,n in enumerate(
            [9007199254740991,9007199254740993,-9007199254740993])]}).encode())
    result=preview_workspace(run,{'kind':'table','title':'Counts','dataset_id':run.experiments[0].id,'columns':['count']})
    assert result.model_dump(mode='json')['rows']==[['0',9007199254740991],['1','9007199254740993'],['2','-9007199254740993']]
    assert '9007199254740993' in result.markdown
