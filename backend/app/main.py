from __future__ import annotations
from contextlib import asynccontextmanager
import asyncio

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
from backend.app.api.research import router as research_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.research_tasks import router as research_tasks_router
from backend.app.request_limits import RequestBodyLimit
from backend.app.security import load_config, SecurityMiddleware
from services.research_jobs import start_managers, stop_managers


@asynccontextmanager
async def lifespan(application):
    managers = await asyncio.to_thread(start_managers, application.state.security_config)
    try:
        yield
    finally:
        await asyncio.to_thread(stop_managers, managers)


app = FastAPI(
    lifespan=lifespan,
    title="AutoResearch Agent API",
    description=(
        "Backend API for academic paper search, "
        "PDF upload and multi-agent paper analysis."
    ),
    version="0.3.0",
)

app.state.security_config = load_config()
app.add_middleware(RequestBodyLimit)
app.add_middleware(SecurityMiddleware, config=app.state.security_config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app.state.security_config.origins,
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
app.include_router(research_router)
app.include_router(jobs_router)
app.include_router(research_tasks_router)


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
