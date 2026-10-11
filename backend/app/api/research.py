"""Local evidence workspace API. Existing /api/papers contracts stay intact."""
from typing import Annotated
import requests
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query
from pydantic import Field
from schemas.research import CandidateDecisionRequest, Contract, ResearchRun, ResearchHistory
from workflow.evidence_workflow import EvidenceWorkflow
from schemas.citation_registry import CitationRegistry
from services.citation_registry import build_citation_registry
from schemas.bibtex_export import BibtexExport
from services.bibtex_export import build_bibtex_export
from schemas.source_identity import SourceIdentityRequest, SourceIdentities
from services.source_identity import build_source_identities
from schemas.source_duplicates import SourceDuplicateReport
from services.source_duplicates import build_source_duplicates

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


@router.post('/runs/{run_id}/candidate-decisions', response_model=ResearchRun)
def candidate_decision(run_id: str, request: CandidateDecisionRequest,
                       flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: flow.record_candidate_decision(
        run_id, request.candidate_id, request.decision, request.reason))


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


@router.get('/runs/{run_id}/citations', response_model=CitationRegistry)
def citations(run_id: str, flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: build_citation_registry(flow.store.load(run_id)))


@router.get('/runs/{run_id}/bibtex', response_model=BibtexExport)
def bibtex(run_id: str, flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: build_bibtex_export(flow.store.load(run_id)))


@router.get('/runs/{run_id}/source-identities', response_model=SourceIdentities)
def source_identities(run_id: str, flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: build_source_identities(flow.store.load(run_id)))


@router.post('/runs/{run_id}/source-identities', response_model=ResearchRun)
def record_source_identity(run_id: str, request: SourceIdentityRequest,
                           flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: flow.record_source_identity(run_id, **request.model_dump()))


@router.get('/runs/{run_id}/source-duplicates', response_model=SourceDuplicateReport)
def source_duplicates(run_id: str, flow: Annotated[EvidenceWorkflow, Depends(get_workflow)]):
    return invoke(lambda: build_source_duplicates(flow.store.load(run_id)))
