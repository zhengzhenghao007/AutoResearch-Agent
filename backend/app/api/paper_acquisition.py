"""Explicit acquisition and import; mounted under the existing writer middleware."""
from typing import Annotated
from fastapi import APIRouter, Depends
from backend.app.api.research import get_workflow, invoke
from workflow.evidence_workflow import EvidenceWorkflow
from schemas.paper_acquisition import AcquisitionRequest, AcquisitionOutcome
from schemas.research import ResearchRun
from services.paper_acquisition import acquire, history, import_acquired

router = APIRouter(prefix='/api/research', tags=['paper acquisition'])
Flow = Annotated[EvidenceWorkflow, Depends(get_workflow)]


@router.post('/runs/{run_id}/paper-acquisitions', response_model=list[AcquisitionOutcome])
def acquire_papers(run_id: str, request: AcquisitionRequest, flow: Flow):
    return invoke(lambda: acquire(flow.store, run_id, request))


@router.get('/runs/{run_id}/paper-acquisitions', response_model=list[AcquisitionOutcome])
def acquisition_history(run_id: str, flow: Flow):
    return invoke(lambda: history(flow.store, run_id))


@router.post('/runs/{run_id}/paper-acquisitions/{acquisition_id}/import', response_model=ResearchRun)
def import_paper(run_id: str, acquisition_id: str, flow: Flow):
    return invoke(lambda: import_acquired(flow, run_id, acquisition_id))
