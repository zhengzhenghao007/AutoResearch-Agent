from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.app.api.analysis import (
    router as analysis_router,
)
from backend.app.api.papers import (
    router as papers_router,
)


app = FastAPI(
    title="AutoResearch Agent API",
    description=(
        "Backend API for academic paper search, "
        "PDF upload and multi-agent paper analysis."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    papers_router
)

app.include_router(
    analysis_router
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "name": "AutoResearch Agent API",
        "status": "running",
        "version": "0.3.0",
    }


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }