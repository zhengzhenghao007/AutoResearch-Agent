"""Optional paper quick reads: GET never invokes a provider."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from backend.app.api.research import get_workflow, invoke
from schemas.paper_quick_read import PaperQuickRead, QuickReadRequest
from services.paper_quick_read import generate_quick_read, get_quick_read, QuickReadProviderError
from workflow.evidence_workflow import EvidenceWorkflow

router = APIRouter(prefix='/api/research', tags=['paper quick read'])


def get_quick_read_generator():
    return generate_quick_read


@router.get('/runs/{run_id}/papers/{source_id:path}/quick-read', response_model=PaperQuickRead | None)
def cached_quick_read(run_id: str, source_id: str,
                      flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: get_quick_read(flow.store, run_id, source_id))


@router.post('/runs/{run_id}/papers/{source_id:path}/quick-read', response_model=PaperQuickRead)
def paper_quick_read(run_id: str, source_id: str, request: QuickReadRequest,
                     flow: Annotated[EvidenceWorkflow, Depends(get_workflow)],
                     generator=Depends(get_quick_read_generator)):
    try:
        return invoke(lambda: generator(flow.store, run_id, source_id, allow_model=request.allow_model))
    except QuickReadProviderError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, 'Quick-read provider failed; no report was saved. Check model configuration and retry.') from exc
