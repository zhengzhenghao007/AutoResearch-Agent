from pathlib import Path
from schemas.research import ResearchRun
from schemas.research_tasks import ResearchTaskCreate, TaskBudget
from services.research_store import ResearchStore
from services.research_tasks import ResearchTaskExecutor
from services.research_task_reports import build_task_report, render_task_report


def setup(tmp_path):
    store = ResearchStore(tmp_path)
    run = ResearchRun.model_validate_json(Path('examples/conformal-prediction/outputs/run.json').read_text(encoding='utf-8'))
    store.save(run)
    return store, run


def finish(store, run, task):
    for _ in range(30):
        task = ResearchTaskExecutor(store).next(run.id, task.id)
        if task.status in ('completed', 'incomplete'): return task
    raise AssertionError(task.status)


def test_research_workflow_persists_grounded_artifacts_and_exports(tmp_path):
    store, run = setup(tmp_path)
    task = ResearchTaskExecutor(store).create(run.id, ResearchTaskCreate(question='Compare conformal prediction limitations', mode='research', budget=TaskBudget(max_evidence=100)))
    task = finish(store, run, task)
    kinds = {a.kind for s in task.steps for a in s.result.artifacts}
    assert {'matrix', 'review', 'quality', 'hypothesis'} <= kinds
    checked = {e for s in task.steps if s.tool == 'inspect_sources' for e in s.result.evidence_ids}
    assert all(set(a.evidence_ids) <= checked for s in task.steps for a in s.result.artifacts)
    assert any(a.status == 'proposal' for s in task.steps for a in s.result.artifacts)
    report = build_task_report(task, run)
    assert report['scientific_validation'] == 'not_assessed'
    assert 'Research artifacts' in render_task_report(report)
    assert task.usage.input_tokens == 0


def test_goal_change_marks_research_stale_and_replan_keeps_history(tmp_path):
    store, run = setup(tmp_path)
    ex = ResearchTaskExecutor(store)
    old = ex.create(run.id, ResearchTaskCreate(question='coverage', mode='research'))
    ex.next(run.id, old.id)
    run.research_goal = 'New deployment setting'
    store.save(run)
    assert ex.get(run.id, old.id).status == 'stale'
    new = ex.create(run.id, ResearchTaskCreate(question=run.research_goal, mode='research', parent_task_id=old.id))
    assert new.parent_task_id == old.id
    assert len(ex.list(run.id)) == 2
    report = build_task_report(ex.snapshot(run.id, old.id), run)
    assert report['source_status'] == 'stale'
    assert report['artifacts'] == []


def test_small_evidence_budget_exposes_omissions_and_never_overruns(tmp_path):
    store, run = setup(tmp_path)
    task = ResearchTaskExecutor(store).create(run.id, ResearchTaskCreate(question='coverage',mode='research',budget=TaskBudget(max_evidence=1)))
    task = finish(store, run, task)
    assert task.usage.evidence == 1
    assert task.status == 'incomplete'
    assert any('budget' in g.lower() for s in task.steps for g in s.result.gaps)


def test_empty_research_proposes_search_instead_of_inventing_findings(tmp_path):
    store, run = setup(tmp_path)
    run=ResearchRun(id=run.id,topic='unknown area',plan=[])
    store.save(run)
    task = ResearchTaskExecutor(store).create(run.id, ResearchTaskCreate(question='unknown area',mode='research'))
    task = finish(store, run, task)
    assert task.status == 'incomplete'
    assert not [a for s in task.steps for a in s.result.artifacts if a.kind == 'hypothesis']
    assert any('search' in a.text.lower() for s in task.steps for a in s.result.artifacts if a.kind == 'quality')


def test_experimental_outlier_preserves_sample_id_and_small_sample_boundary():
    from schemas.experiment_statistics import ObservationReference
    from services.research_capabilities import outlier_samples
    refs = [ObservationReference(sample_id=f'row-{i}', column='score', value=str(value))
            for i,value in enumerate([2, 2, 3, 3, 3, 4, 4, 100])]
    assert outlier_samples(refs) == [refs[-1]]
    assert outlier_samples(refs[:3]) == []
