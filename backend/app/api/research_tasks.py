"""Research task routes inherit principal isolation and writer middleware."""
from typing import Annotated, Literal
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from backend.app.api.research import get_workflow, invoke
from schemas.research_tasks import ResearchTask, ResearchTaskCreate, TaskBudget
from services.research_tasks import ResearchTaskExecutor
from services.research_task_reports import build_task_report, render_task_report
from workflow.evidence_workflow import EvidenceWorkflow

router = APIRouter(prefix='/api/research/runs/{run_id}/tasks', tags=['research tasks'])
Flow = Annotated[EvidenceWorkflow, Depends(get_workflow)]

@router.get('')
def list_tasks(run_id: str, flow: Flow):
    return invoke(lambda: {'items': ResearchTaskExecutor(flow.store).list(run_id)})

@router.post('', response_model=ResearchTask)
def create_task(run_id: str, request: ResearchTaskCreate, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).create(run_id, request))

@router.get('/skills')
def available_skills(run_id: str, flow: Flow):
    from services.skill_registry import RESEARCH_SKILLS
    def catalog():
        flow.store.load(run_id)
        return {'items': RESEARCH_SKILLS.catalog()}
    return invoke(catalog)

@router.get('/{task_id}', response_model=ResearchTask)
def get_task(run_id: str, task_id: str, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).get(run_id, task_id))

@router.get('/{task_id}/report')
def task_report(run_id: str, task_id: str, flow: Flow, format: Literal['json', 'markdown'] = 'json'):
    def export():
        task = ResearchTaskExecutor(flow.store).snapshot(run_id, task_id)
        report = build_task_report(task, flow.store.load(run_id))
        suffix = 'md' if format == 'markdown' else 'json'
        headers = {'Content-Disposition': f'attachment; filename="research-task-{task.id}.{suffix}"',
                   'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
        if format == 'markdown':
            return Response(render_task_report(report), media_type='text/markdown', headers=headers)
        return JSONResponse(report, headers=headers)
    return invoke(export)

@router.post('/{task_id}/next', response_model=ResearchTask)
def next_task(run_id: str, task_id: str, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).next(run_id, task_id))

@router.post('/{task_id}/cancel', response_model=ResearchTask)
def cancel_task(run_id: str, task_id: str, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).cancel(run_id, task_id))

@router.post('/{task_id}/budget', response_model=ResearchTask)
def increase_budget(run_id: str, task_id: str, request: TaskBudget, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).increase_budget(run_id, task_id, request))
