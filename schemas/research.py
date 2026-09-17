"""Versioned evidence contracts. A citation is support, not proof of truth."""
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Category = Literal['problem', 'method', 'dataset', 'experiment', 'result', 'limitation', 'future_work']
CATEGORIES = ('problem', 'method', 'dataset', 'experiment', 'result', 'limitation', 'future_work')


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Source(Contract):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    kind: Literal['paper', 'user_data'] = 'paper'
    uri: str = Field(min_length=1)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Page(Contract):
    number: int = Field(ge=1)
    text: str


class Document(Contract):
    source: Source
    pages: list[Page]
    total_pages: int = Field(ge=1)
    truncated: bool = False


class Evidence(Contract):
    id: str = Field(min_length=1)
    source_id: str
    page: int = Field(ge=1)
    quote: str = Field(min_length=12)


class Claim(Contract):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    category: Category
    claim_type: Literal['paper_report', 'user_observation', 'synthesis', 'hypothesis', 'suggestion'] = 'paper_report'
    evidence_ids: list[str] = Field(min_length=1)
    created_by: str = 'extractor'
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaperEvidence(Contract):
    document: Document
    evidence: list[Evidence] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    missing_fields: list[Category] = Field(default_factory=list)
    extractor: str = 'literal-rules-v1'


class Review(Contract):
    approved: bool
    issues: list[str]
    scope: str = 'Literal source support only; scientific validity and categorization require human review.'


class Candidate(Contract):
    id: str
    title: str
    pdf_url: str
    summary: str = ''
    authors: list[str] = Field(default_factory=list)


class Artifact(Contract):
    kind: Literal['literature_summary', 'method_comparison', 'research_ideas', 'coverage_gaps']
    title: str
    content: str
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ResearchRun(Contract):
    schema_version: Literal[1] = 1
    id: str = Field(pattern=r'^[a-f0-9]{32}$')
    topic: str = Field(min_length=1, max_length=2000)
    plan: list[str]
    candidates: list[Candidate] = Field(default_factory=list)
    selected_ids: list[str] = Field(default_factory=list)
    papers: list[PaperEvidence] = Field(default_factory=list)
    generated_claims: list[Claim] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    review: Review = Field(default_factory=lambda: Review(approved=False, issues=['No papers processed']))
