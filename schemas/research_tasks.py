"""Bounded offline research execution contracts."""
from datetime import datetime
from typing import Literal
from pydantic import Field
from schemas.research import Contract

class TaskBudget(Contract):
    max_steps: int = Field(default=24, ge=0, le=200, strict=True)
    max_seconds: float = Field(default=60, ge=0, le=3600, allow_inf_nan=False, strict=True)
    max_evidence: int = Field(default=30, ge=0, le=500, strict=True)

class ResearchTaskCreate(Contract):
    question: str = Field(min_length=1, max_length=2000)
    subquestions: list[str] = Field(default_factory=list, max_length=6)
    budget: TaskBudget = Field(default_factory=TaskBudget)

class TaskUsage(Contract):
    steps: int = 0
    seconds: float = 0
    evidence: int = 0
    input_tokens: Literal[0] = 0
    output_tokens: Literal[0] = 0
    cost_usd: Literal[0] = 0

class TaskQuestion(Contract):
    id: str
    question: str
    requirements: list[str]

class TaskResult(Contract):
    evidence_ids: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    summary: str

class TaskStep(Contract):
    id: str
    question_id: str
    title: str
    tool: Literal['lexical_retrieve', 'inspect_sources']
    depends_on: list[str]
    status: Literal['pending','running','completed','failed'] = 'pending'
    attempts: int = 0
    input_sha256: str
    result: TaskResult | None = None

class TaskEvent(Contract):
    at: datetime
    type: str
    message: str

class ResearchTask(Contract):
    id: str
    run_id: str
    question: str
    source_sha256: str
    created_at: datetime
    updated_at: datetime
    status: Literal['ready','running','paused','completed','incomplete','cancelled','budget_exhausted','stale','failed'] = 'ready'
    stop_reason: str | None = None
    budget: TaskBudget
    usage: TaskUsage = Field(default_factory=TaskUsage)
    subquestions: list[TaskQuestion]
    steps: list[TaskStep]
    events: list[TaskEvent] = Field(default_factory=list)
