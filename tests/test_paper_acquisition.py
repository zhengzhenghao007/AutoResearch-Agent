from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from schemas.multi_source_search import SearchBatch, SearchRequest, SearchHit, SourceSearch
from schemas.paper_acquisition import AcquisitionRequest
from services.search_history import database
from services.paper_acquisition import acquire, history, download, import_acquired
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


class Response:
    status_code = 200
    headers = {}
    def __init__(self, content=b'%PDF-fake', status=200, headers=None):
        self.content, self.status_code, self.headers = content, status, headers or {}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def iter_content(self, size): yield self.content


@pytest.fixture
def setup(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path))
    run = flow.create('test')
    return flow, run.id


def saved(flow, run_id, urls):
    hits = [SearchHit(source='arxiv', source_id=str(i), title='Paper', rank=i, pdf_url=url) for i, url in enumerate(urls)]
    now = datetime.now(timezone.utc)
    batch = SearchBatch(run_id=run_id, request=SearchRequest(query='test'), groups=[], sources=[SourceSearch(source='arxiv',status='success',started_at=now,finished_at=now,hits=hits)])
    with database(flow.store) as db:
        db.execute('INSERT INTO batches VALUES(?,?,?,?)', (batch.id,run_id,0,batch.model_dump_json()))
    return AcquisitionRequest(selections=[{'batch_id':batch.id,'source':'arxiv','source_id':hit.source_id} for hit in hits])


PARSER = SimpleNamespace(parse_bytes=lambda *args: None)
URL = 'https://arxiv.org/pdf/2401.12345'


@pytest.mark.parametrize('url', ['https://127.0.0.1/pdf/2401.12345', 'https://arxiv.org.evil/pdf/2401.12345', 'https://arxiv.org@localhost/pdf/2401.12345', URL+'?next=http://localhost', URL+'#x', 'https://arxiv.org:443/pdf/2401.12345', 'file:///etc/passwd'])
def test_hostile_urls_never_requested(setup,url):
    flow, run_id = setup
    request = saved(flow,run_id,[url])
    def transport(*args,**kwargs): pytest.fail('Unsafe network call')
    assert acquire(flow.store,run_id,request,transport=transport,processor=PARSER)[0].status == 'unsupported'


def test_cached_duplicate_and_restart(setup):
    flow, run_id = setup
    request = saved(flow,run_id,[URL,URL])
    calls=[]
    def transport(url,**kwargs):
        assert kwargs['allow_redirects'] is False
        calls.append(url)
        return Response()
    results=acquire(flow.store,run_id,request,transport=transport,processor=PARSER)
    assert [r.status for r in results] == ['downloaded','cached']
    assert len(calls)==1
    assert acquire(ResearchStore(flow.store.root),run_id,request,transport=transport,processor=PARSER)[0].status=='cached'
    assert len(calls)==1
    assert len(history(flow.store,run_id))==4
    assert not flow.store.load(run_id).papers


def test_partial_failure_retry_and_redirect(setup):
    flow,run_id=setup
    request=saved(flow,run_id,[URL,URL+'v2'])
    result=acquire(flow.store,run_id,request,transport=lambda url,**kw:Response(status=302 if url.endswith('v2') else 200),processor=PARSER)
    assert [r.status for r in result]==['downloaded','failed']
    result=acquire(flow.store,run_id,request,transport=lambda *a,**kw:Response(),processor=PARSER)
    assert [r.status for r in result]==['cached','downloaded']
    assert len(history(flow.store,run_id))==4


def test_limits(monkeypatch):
    monkeypatch.setattr('services.paper_acquisition.MAX_BYTES', 8)
    for response in [Response(),Response(b'%PDF-x',headers={'Content-Length':'9'}),Response(b'not pdf')]:
        with pytest.raises(ValueError): download(URL,lambda *a,**kw:response)


def test_tenant_and_run_isolation(setup,tmp_path):
    flow,run_id=setup
    request=saved(flow,run_id,[URL])
    item=acquire(flow.store,run_id,request,transport=lambda *a,**kw:Response(),processor=PARSER)[0]
    other=flow.create('other')
    with pytest.raises(ValueError): acquire(flow.store,other.id,request,processor=PARSER)
    with pytest.raises(FileNotFoundError): import_acquired(flow,other.id,item.id)
    other_store=ResearchStore(tmp_path/'tenant2')
    with pytest.raises(FileNotFoundError): history(other_store,run_id)


def test_import_reuses_workflow_and_rejects_model(setup):
    flow,run_id=setup
    request=saved(flow,run_id,[URL])
    item=acquire(flow.store,run_id,request,transport=lambda *a,**kw:Response(),processor=PARSER)[0]
    calls=[]
    flow.import_pdf=lambda data,title,run_id: calls.append((data,title,run_id)) or 'imported'
    assert import_acquired(flow,run_id,item.id)=='imported'
    assert calls==[(b'%PDF-fake','Paper',run_id)]
    flow.extractor.mode='llm'
    with pytest.raises(ValueError): import_acquired(flow,run_id,item.id)


def test_parser_failure_is_persisted(setup):
    flow,run_id=setup
    request=saved(flow,run_id,[URL])
    def reject(*args): raise ValueError('invalid PDF')
    assert acquire(flow.store,run_id,request,transport=lambda *a,**kw:Response(),processor=SimpleNamespace(parse_bytes=reject))[0].status=='failed'
    assert not list((flow.store.root/'acquired_originals').glob('*.pdf'))


def test_real_pdf_acquisition_import_research_and_export(setup):
    from pathlib import Path
    from schemas.research_tasks import ResearchTaskCreate
    from services.research_tasks import ResearchTaskExecutor
    from services.research_task_reports import build_task_report
    flow, run_id = setup
    request = saved(flow, run_id, [URL])
    data = Path('tests/fixtures/evidence/normal.pdf').read_bytes()
    item = acquire(flow.store, run_id, request, transport=lambda *a, **kw: Response(data))[0]
    run = import_acquired(flow, run_id, item.id)
    assert run.papers[0].document.source.sha256 == item.sha256
    executor = ResearchTaskExecutor(flow.store)
    task = executor.create(run_id, ResearchTaskCreate(question='Study methods and limitations', mode='research'))
    for _ in task.steps:
        task = ResearchTaskExecutor(flow.store).next(run_id, task.id)
    report = build_task_report(task, run)
    assert report['source_status'] == 'current'
    assert report['questions'][0]['evidence']
    assert any(a['kind'] == 'matrix' for a in report['artifacts'])


def test_download_slots_are_shared_and_bounded(setup):
    from services.paper_acquisition import _reserve_download
    flow, _ = setup
    assert _reserve_download(flow.store, 100) == 0
    assert _reserve_download(ResearchStore(flow.store.root), 101) == 2
    for _ in range(4): _reserve_download(flow.store, 101)
    with pytest.raises(ValueError, match='queue'): _reserve_download(flow.store, 101)
