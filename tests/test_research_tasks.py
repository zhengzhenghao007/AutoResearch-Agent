from uuid import uuid4
import pytest
from schemas.research import ResearchRun
from services.research_store import ResearchStore


def fixture(tmp_path):
    store = ResearchStore(tmp_path)
    run = ResearchRun(id=uuid4().hex, topic='conformal prediction', plan=[])
    store.save(run)
    return store, run


def test_durable_plan_and_empty_evidence_outcome(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate
    store, run = fixture(tmp_path)
    executor = ResearchTaskExecutor(store)
    task = executor.create(run.id, ResearchTaskCreate(question='What are coverage limits?'))
    assert task.steps and task.subquestions
    assert any(step.depends_on for step in task.steps)
    assert ResearchTaskExecutor(store).get(run.id, task.id) == task
    for _ in range(20):
        task = executor.next(run.id, task.id)
        if task.status in ('completed', 'incomplete'): break
    assert task.status == 'incomplete'
    assert any(s.result and s.result.gaps for s in task.steps)
    assert executor.next(run.id, task.id) == task
    assert task.usage.cost_usd == task.usage.input_tokens == task.usage.output_tokens == 0
    assert store.load(run.id) == run

@pytest.mark.parametrize('budget', [{'max_steps': 0}, {'max_seconds': 0}, {'max_evidence': 0}])
def test_zero_budget_and_explicit_increase(tmp_path, budget):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate, TaskBudget
    store, run = fixture(tmp_path)
    ex = ResearchTaskExecutor(store)
    task = ex.create(run.id, ResearchTaskCreate(question='coverage', budget=TaskBudget(**budget)))
    stopped = ex.next(run.id, task.id)
    assert stopped.status == 'budget_exhausted'
    assert stopped.usage.steps == 0
    assert ex.next(run.id, task.id) == stopped
    ex.increase_budget(run.id, task.id, TaskBudget())
    assert ex.next(run.id, task.id).usage.steps == 1
    with pytest.raises(ValueError): ex.increase_budget(run.id, task.id, TaskBudget(max_steps=0))


def test_concurrent_cancel_charges_time_and_discards_result(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate
    from threading import Event, Thread
    store, run = fixture(tmp_path)
    entered, release = Event(), Event()
    clock = [100.0]
    ex = ResearchTaskExecutor(store, clock=lambda: clock[0])
    original = ex._compute
    def compute(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    ex._compute = compute
    task = ex.create(run.id, ResearchTaskCreate(question='coverage'))
    worker = Thread(target=lambda: ex.next(run.id, task.id))
    worker.start()
    assert entered.wait(5)
    assert ResearchTaskExecutor(store).get(run.id, task.id).usage.steps == 1
    assert ex.next(run.id, task.id).usage.steps == 1
    clock[0] += 2
    stopped = ex.cancel(run.id, task.id)
    release.set()
    worker.join(5)
    assert stopped.status == 'cancelled'
    assert stopped.usage.seconds == 2
    assert ex.get(run.id, task.id) == stopped
    assert all(s.result is None for s in stopped.steps)


def test_crash_recovery_reserves_attempt_and_time(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate, TaskBudget
    store, run = fixture(tmp_path)
    clock = [100.0]
    ex = ResearchTaskExecutor(store, clock=lambda: clock[0], lease_seconds=2)
    task = ex.create(run.id, ResearchTaskCreate(question='coverage', budget=TaskBudget(max_steps=2)))
    def crash(*args): raise KeyboardInterrupt()
    ex._compute = crash
    with pytest.raises(KeyboardInterrupt): ex.next(run.id, task.id)
    clock[0] += 3
    recovered = ResearchTaskExecutor(store, clock=lambda: clock[0], lease_seconds=2).next(run.id, task.id)
    assert recovered.usage.steps == 2
    assert recovered.usage.seconds >= 2
    assert recovered.steps[0].attempts == 2
    assert recovered.steps[0].status == 'completed'
    assert ex.next(run.id, task.id).status == 'budget_exhausted'


def test_stale_source_rejected_and_cross_run_isolated(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate
    from schemas.research import Document, Source, Page, PaperEvidence, Review
    from services.literature_synthesis import synthesize, build_suggestions
    store, run = fixture(tmp_path)
    ex = ResearchTaskExecutor(store)
    task = ex.create(run.id, ResearchTaskCreate(question='coverage'))
    other = ResearchRun(id=uuid4().hex, topic='other', plan=[])
    store.save(other)
    with pytest.raises(FileNotFoundError): ex.get(other.id, task.id)
    with pytest.raises(ValueError): ex.get('../escape', task.id)
    p = PaperEvidence(document=Document(source=Source(id='s', title='source', uri='upload:test', sha256='a'*64), pages=[Page(number=1,text='text')],total_pages=1),missing_fields=['problem','method','dataset','experiment','result','limitation','future_work'])
    run.papers = [p]
    run.review = Review(approved=False, issues=['source: No supported claims extracted'])
    run.artifacts, run.generated_claims = synthesize(run.papers), build_suggestions(run.papers)
    store.save(run)
    assert ex.next(run.id, task.id).status == 'stale'
    assert ex.next(run.id, task.id).usage.steps == 0


def test_api_uses_existing_workflow_and_run_binding(tmp_path):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.research import get_workflow
    from types import SimpleNamespace
    store, run = fixture(tmp_path)
    app.dependency_overrides[get_workflow] = lambda: SimpleNamespace(store=store)
    try:
        client = TestClient(app)
        prefix = f'/api/research/runs/{run.id}/tasks'
        response = client.post(prefix, json={'question':'coverage'})
        assert response.status_code == 200, response.text
        task_id = response.json()['id']
        assert client.get(prefix).json()['items'][0]['id'] == task_id
        assert client.get(prefix+'/'+task_id).status_code == 200
        assert client.post(prefix+'/'+task_id+'/next').json()['usage']['steps'] == 1
        assert client.post(prefix+'/'+task_id+'/budget', json={'max_steps':25,'max_seconds':60,'max_evidence':30}).status_code == 200
        assert client.post(prefix+'/'+task_id+'/cancel').json()['status'] == 'cancelled'
    finally:
        app.dependency_overrides.clear()

@pytest.mark.parametrize('question', ['???', '   ', ';\n;'])
def test_unusable_question_rejected(tmp_path, question):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate
    store, run = fixture(tmp_path)
    with pytest.raises(ValueError): ResearchTaskExecutor(store).create(run.id, ResearchTaskCreate(question=question))

@pytest.mark.parametrize('value',[True,1.2,'4'])
def test_step_budget_strict_integer(value):
    from schemas.research_tasks import TaskBudget
    with pytest.raises(ValueError): TaskBudget(max_steps=value)


def populated(tmp_path):
    from schemas.research import Document, Source, Page, Review
    from services.evidence_extraction import EvidenceExtractor
    from services.literature_synthesis import synthesize, build_suggestions
    store, run = fixture(tmp_path)
    doc = Document(source=Source(id='s',title='study',uri='upload:test',sha256='a'*64),total_pages=1,pages=[Page(number=1,text='Our method provides coverage guarantees. Our method improves coverage bounds. Our method requires coverage assumptions. Our method has coverage limitations.')])
    run.papers = [EvidenceExtractor().extract(doc)]
    run.review = Review(approved=True,issues=[])
    run.artifacts, run.generated_claims = synthesize(run.papers), build_suggestions(run.papers)
    store.save(run)
    return store,run


def test_intent_planning_and_cap_gap(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate, TaskBudget
    store,run=populated(tmp_path)
    ex=ResearchTaskExecutor(store)
    comparison=ex.create(run.id,ResearchTaskCreate(question='Compare coverage methods'))
    limitations=ex.create(run.id,ResearchTaskCreate(question='What limits coverage?'))
    assert len(comparison.subquestions)>1
    assert comparison.subquestions[0].requirements != limitations.subquestions[0].requirements
    task=ex.create(run.id,ResearchTaskCreate(question='coverage',subquestions=['coverage'],budget=TaskBudget(max_evidence=1)))
    task=ex.next(run.id,task.id)
    assert task.usage.evidence == 1
    assert task.steps[0].result.gaps
    task=ex.next(run.id,task.id)
    assert task.status == 'incomplete'


def test_cancel_exhausted_is_terminal(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate, TaskBudget
    store,run=fixture(tmp_path)
    ex=ResearchTaskExecutor(store)
    task=ex.create(run.id,ResearchTaskCreate(question='coverage',budget=TaskBudget(max_steps=0)))
    ex.next(run.id,task.id)
    assert ex.cancel(run.id,task.id).status == 'cancelled'


def test_completed_task_becomes_stale_on_read_and_next(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate
    store,run=populated(tmp_path)
    ex=ResearchTaskExecutor(store)
    tasks=[ex.create(run.id,ResearchTaskCreate(question='coverage',subquestions=['coverage'])) for _ in range(3)]
    for task in tasks:
        ex.next(run.id,task.id)
        assert ex.next(run.id,task.id).status == 'completed'
    run.papers[0].document.source.sha256='b'*64
    store.save(run)
    assert ex.get(run.id,tasks[0].id).status == 'stale'
    assert ex.next(run.id,tasks[1].id).status == 'stale'
    assert all(t.status=='stale' for t in ex.list(run.id))


def test_commit_source_validation_is_charged_to_deadline(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate, TaskBudget
    store,run=fixture(tmp_path)
    now=[100.0]
    ex=ResearchTaskExecutor(store,clock=lambda:now[0])
    task=ex.create(run.id,ResearchTaskCreate(question='coverage',budget=TaskBudget(max_seconds=1)))
    load=store.load
    calls=[0]
    def slow_load(run_id):
        calls[0]+=1
        if calls[0]==2: now[0]+=2
        return load(run_id)
    store.load=slow_load
    task=ex.next(run.id,task.id)
    assert task.status=='budget_exhausted'
    assert task.usage.seconds==1
    assert task.steps[0].result is None


def test_cancelled_checkpoint_becomes_stale_after_source_change(tmp_path):
    from services.research_tasks import ResearchTaskExecutor
    from schemas.research_tasks import ResearchTaskCreate
    store, run = populated(tmp_path)
    ex = ResearchTaskExecutor(store)
    task = ex.create(run.id, ResearchTaskCreate(question='coverage', subquestions=['coverage']))
    ex.next(run.id, task.id)
    assert ex.cancel(run.id, task.id).status == 'cancelled'
    run.papers[0].document.source.sha256 = 'c' * 64
    store.save(run)
    current = ex.get(run.id, task.id)
    assert current.status == 'stale'
    assert current.steps[0].result.evidence_ids


def test_task_api_writer_and_tenant_guards(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.app.security import SecurityConfig, SecurityMiddleware
    from backend.app.api.research_tasks import router
    from services.sqlite_store import SQLiteResearchStore
    users={'alice':{'role':'writer','token':'a'*32},'bob':{'role':'writer','token':'b'*32},'reader':{'role':'reader','token':'c'*32}}
    app=FastAPI()
    config=SecurityConfig(True,tmp_path,users,sqlite=True)
    app.state.security_config=config
    app.add_middleware(SecurityMiddleware,config=config)
    app.include_router(router)
    run=ResearchRun(id=uuid4().hex,topic='coverage',plan=[])
    SQLiteResearchStore(tmp_path/'users'/'alice').save(run)
    client=TestClient(app)
    url=f'/api/research/runs/{run.id}/tasks'
    assert client.post(url,json={'question':'coverage'}).status_code==401
    assert client.post(url,json={'question':'coverage'},headers={'Authorization':'Bearer '+'c'*32}).status_code==403
    task=client.post(url,json={'question':'coverage'},headers={'Authorization':'Bearer '+'a'*32})
    assert task.status_code==200
    assert client.get(url+'/'+task.json()['id'],headers={'Authorization':'Bearer '+'b'*32}).status_code==404
