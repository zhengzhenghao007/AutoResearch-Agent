import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.api.research import get_workflow, router
from services.original_pdf import original_path
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


def test_original_roundtrip_and_legacy_reattachment(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path))
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_workflow] = lambda: flow
    data = pdf_bytes(['We propose a scheduling method.'])
    with TestClient(app) as client:
        created = client.post('/api/research/upload', files={'file':('test.pdf',data)})
        assert created.status_code == 200
        run = flow.store.load(created.json()['id'])
        source = run.papers[0].document.source.id
        url = f'/api/research/runs/{run.id}/papers/{source}/original'
        assert client.get(url).content == data
        other = flow.create()
        assert client.get(url.replace(run.id, other.id)).status_code == 404
        original_path(flow.store, run, source).unlink()
        assert client.get(url).status_code == 404
        assert client.post(url, files={'file':('test.pdf',pdf_bytes(['A different study.']))}).status_code == 400
        assert client.post(url, files={'file':('renamed.pdf',data)}).status_code == 200
        assert client.get(url).content == data
        assert flow.store.load(run.id) == run
