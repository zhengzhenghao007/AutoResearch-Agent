"""Search metadata is separate from parsed, verified paper evidence."""
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import Field, model_validator
from schemas.research import Contract

Provider = Literal['arxiv', 'crossref', 'openalex', 'semantic_scholar']

class SearchRequest(Contract):
    query: str = Field(min_length=2, max_length=500)
    sources: list[Provider] = Field(default_factory=lambda: ['crossref', 'openalex'], min_length=1, max_length=4)
    limit: int = Field(default=5, ge=1, le=20, strict=True)

    @model_validator(mode='after')
    def unique_sources(self):
        if len(set(self.sources)) != len(self.sources):
            raise ValueError('Search sources must be distinct')
        return self

class SearchHit(Contract):
    source: Provider
    source_id: str
    title: str = Field(min_length=1, max_length=4000)
    authors: list[str] = Field(default_factory=list)
    doi: str | None = None
    doi_status: Literal['source_reported', 'crossref_registered', 'missing'] = 'missing'
    url: str = ''
    pdf_url: str = ''
    year: int | None = None
    rank: int

class SourceSearch(Contract):
    source: Provider
    status: Literal['success', 'failed']
    started_at: datetime
    finished_at: datetime
    error: str | None = None
    retry_after_seconds: int | None = None
    hits: list[SearchHit] = Field(default_factory=list)

class SearchGroup(Contract):
    key: str
    records: list[SearchHit]

class SearchBatch(Contract):
    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request: SearchRequest
    sources: list[SourceSearch]
    groups: list[SearchGroup]
    scope: str = 'First page per source; provider relevance order. Exact DOI groups retain all source records. Metadata identity and full-text permission require review.'
