"""Optional model reports; principal-scoped workflow and writer middleware apply."""
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from backend.app.api.research import get_workflow, invoke
from schemas.research_reasoning import ReasoningRequest
from services.research_reasoning import ResearchReasoner
from workflow.evidence_workflow import EvidenceWorkflow

router = APIRouter(prefix='/api/research/runs/{run_id}/reasoning', tags=['research reasoning'])
Flow = Annotated[EvidenceWorkflow, Depends(get_workflow)]

@router.get('')
def reasoning_history(run_id: str, flow: Flow):
    return invoke(lambda: {'items': ResearchReasoner(flow.store).history(run_id)})

@router.post('')
def generate_reasoning(run_id: str, request: ReasoningRequest, flow: Flow):
    return invoke(lambda: ResearchReasoner(flow.store).generate(run_id, request))

@router.get('/{generation_id}/report')
def export_reasoning(run_id: str, generation_id: str, flow: Flow):
    def export():
        report = ResearchReasoner(flow.store).get(run_id, generation_id)
        return JSONResponse(report, headers={'Content-Disposition': f'attachment; filename="research-reasoning-{report["id"]}.json"',
                                             'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})
    return invoke(export)
