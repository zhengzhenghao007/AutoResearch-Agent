from uuid import uuid4
import pytest
from schemas.research import ResearchRun
from schemas.multi_source_search import SearchRequest, SearchHit
from services.multi_source_search import multi_search, safe_url, doi_value, search_source
from services.search_history import search_and_save, search_history
from services.research_store import ResearchStore


def test_partial_failure_and_exact_doi_groups_preserve_sources():
    def adapter(source, query, limit):
        if source == 'semantic_scholar': raise ValueError('secret token')
        return [SearchHit(source=source,source_id=source,title='Shared paper',doi='10.1234/a',rank=1)]
    batch=multi_search('a'*32,SearchRequest(query='coverage',sources=['crossref','openalex','semantic_scholar']),adapter)
    assert len(batch.groups)==1
    assert len(batch.groups[0].records)==2
    assert batch.sources[-1].status=='failed'
    assert 'secret' not in batch.model_dump_json()


def test_no_doi_does_not_merge_same_titles():
    def adapter(source,query,limit):
        return [SearchHit(source=source,source_id=source,title='Same title',rank=1)]
    batch=multi_search('a'*32,SearchRequest(query='coverage'),adapter)
    assert len(batch.groups)==2


def test_history_is_durable_scoped_and_rate_limited(tmp_path):
    store=ResearchStore(tmp_path)
    first=ResearchRun(id=uuid4().hex,topic='topic',plan=[])
    second=ResearchRun(id=uuid4().hex,topic='other',plan=[])
    store.save(first);store.save(second)
    def search(run_id,request): return multi_search(run_id,request,lambda *args:[])
    request=SearchRequest(query='coverage')
    batch=search_and_save(store,first.id,request,search)
    assert search_history(ResearchStore(tmp_path),first.id)==[batch]
    assert search_history(store,second.id)==[]
    with pytest.raises(ValueError,match='cooldown'):search_and_save(store,second.id,request,search)
    assert len(search_history(store,first.id))==1


def test_identifiers_and_links():
    assert doi_value('https://doi.org/10.1234/ABC')=='10.1234/abc'
    assert doi_value('invalid') is None
    assert safe_url('javascript:alert(1)')==''
    assert safe_url('https://user:password@example.com')==''


def test_crossref_metadata_does_not_infer_pdf_permission(monkeypatch):
    monkeypatch.setattr('services.multi_source_search.fetch_json',lambda *args:{'message':{'items':[{'title':['Title'],'DOI':'10.1234/A','URL':'https://doi.org/10.1234/A','link':[{'URL':'https://example.org/paper.pdf'}]}]}})
    hit=search_source('crossref','query',5)[0]
    assert hit.doi_status=='crossref_registered'
    assert hit.pdf_url==''

def test_metadata_search_api_roundtrip(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from backend.app.main import app
    from backend.app.api.research import get_workflow
    store=ResearchStore(tmp_path)
    run=ResearchRun(id=uuid4().hex,topic='topic',plan=[]);store.save(run)
    monkeypatch.setattr('services.multi_source_search.search_source',lambda *args:[])
    def saved_search(store,run_id,request):
        return search_and_save(store,run_id,request,lambda rid,req:multi_search(rid,req,lambda *args:[]))
    monkeypatch.setattr('backend.app.api.research.search_and_save',saved_search)
    app.dependency_overrides[get_workflow]=lambda:SimpleNamespace(store=store)
    try:
        client=TestClient(app)
        path=f'/api/research/runs/{run.id}/metadata-search'
        result=client.post(path,json={'query':'coverage'})
        assert result.status_code==200,result.text
        assert client.get(path).json()['items'][0]['id']==result.json()['id']
        assert client.get('/api/research/runs/'+'0'*32+'/metadata-search').status_code==404
    finally:app.dependency_overrides.clear()

def test_provider_retry_after_is_saved_and_enforced(tmp_path,monkeypatch):
    from services.multi_source_search import ProviderResponseError
    store=ResearchStore(tmp_path)
    run=ResearchRun(id=uuid4().hex,topic='topic',plan=[]);store.save(run)
    clock=[1000.0]
    monkeypatch.setattr('services.search_history.time.time',lambda:clock[0])
    def adapter(*args):raise ProviderResponseError(429,120)
    def search(rid,request):return multi_search(rid,request,adapter)
    request=SearchRequest(query='query',sources=['crossref'])
    batch=search_and_save(store,run.id,request,search)
    assert '429' in batch.sources[0].error
    clock[0]+=31
    with pytest.raises(ValueError,match='cooldown'):search_and_save(store,run.id,request,search)
    clock[0]+=90
    assert search_and_save(store,run.id,request,search).id!=batch.id
