"""Research task routes inherit principal isolation and writer middleware."""
from typing import Annotated
from fastapi import APIRouter, Depends
from backend.app.api.research import get_workflow, invoke
from schemas.research_tasks import ResearchTask, ResearchTaskCreate, TaskBudget
from services.research_tasks import ResearchTaskExecutor
from workflow.evidence_workflow import EvidenceWorkflow

router = APIRouter(prefix='/api/research/runs/{run_id}/tasks', tags=['research tasks'])
Flow = Annotated[EvidenceWorkflow, Depends(get_workflow)]

@router.get('')
def list_tasks(run_id: str, flow: Flow):
    return invoke(lambda: {'items': ResearchTaskExecutor(flow.store).list(run_id)})

@router.post('', response_model=ResearchTask)
def create_task(run_id: str, request: ResearchTaskCreate, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).create(run_id, request))

@router.get('/{task_id}', response_model=ResearchTask)
def get_task(run_id: str, task_id: str, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).get(run_id, task_id))

@router.post('/{task_id}/next', response_model=ResearchTask)
def next_task(run_id: str, task_id: str, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).next(run_id, task_id))

@router.post('/{task_id}/cancel', response_model=ResearchTask)
def cancel_task(run_id: str, task_id: str, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).cancel(run_id, task_id))

@router.post('/{task_id}/budget', response_model=ResearchTask)
def increase_budget(run_id: str, task_id: str, request: TaskBudget, flow: Flow):
    return invoke(lambda: ResearchTaskExecutor(flow.store).increase_budget(run_id, task_id, request))
