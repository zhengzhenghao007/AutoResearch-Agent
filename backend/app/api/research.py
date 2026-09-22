"""Local evidence workspace API. Existing /api/papers contracts stay intact."""
from typing import Annotated
import requests
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query
from pydantic import Field
from schemas.research import Contract, ResearchRun, ResearchHistory
from workflow.evidence_workflow import EvidenceWorkflow

router = APIRouter(prefix='/api/research', tags=['research evidence'])


def get_workflow():
    return EvidenceWorkflow()


class SearchRequest(Contract):
    topic: str = Field(min_length=1, max_length=2000)
    max_results: int = Field(default=5, ge=1, le=20)


class SelectionRequest(Contract):
    selected_ids: list[str] = Field(min_length=1, max_length=20)


def invoke(operation):
    try:
        return operation()
    except FileNotFoundError as exc:
        raise HTTPException(404, 'Research run not found') from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(502, 'Paper source unavailable; retry later') from exc


@router.post('/search', response_model=ResearchRun)
def search(request: SearchRequest, flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: flow.search(request.topic, request.max_results))


@router.get('/runs', response_model=ResearchHistory)
def history(flow: Annotated[EvidenceWorkflow, Depends(get_workflow)],
            page: int = Query(default=1, ge=1),
            page_size: int = Query(default=10, ge=1, le=50)):
    return invoke(lambda: flow.store.history(page, page_size))


@router.get('/runs/{run_id}', response_model=ResearchRun)
def get_run(run_id: str, flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: flow.store.load(run_id))


@router.post('/runs/{run_id}/analyze', response_model=ResearchRun)
def analyze(run_id: str, request: SelectionRequest, flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: flow.analyze(run_id, request.selected_ids))


@router.post('/upload', response_model=ResearchRun)
def upload(flow: Annotated[EvidenceWorkflow, Depends(get_workflow)], file: UploadFile = File(...), run_id: str | None = Form(None)):
    try:
        data = file.file.read(flow.processor.max_bytes + 1)
        if len(data) > flow.processor.max_bytes:
            raise HTTPException(413, 'PDF exceeds size limit')
        # Never persist client-provided paths, even when a client sends one as filename.
        title = (file.filename or 'Uploaded paper').replace('\\', '/').split('/')[-1][:200]
        return invoke(lambda: flow.import_pdf(data, title or 'Uploaded paper', run_id))
    finally:
        file.file.close()
