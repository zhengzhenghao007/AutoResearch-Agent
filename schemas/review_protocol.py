"""User-authored review scope and reproducible eligibility criteria."""
from datetime import datetime, timezone
from pydantic import Field
from schemas.research import Contract

class ReviewProtocolFields(Contract):
    question: str = Field(default='', max_length=2000)
    inclusion_criteria: str = Field(default='', max_length=5000)
    exclusion_criteria: str = Field(default='', max_length=5000)
    publication_range: str = Field(default='', max_length=500)
    search_strategy: str = Field(default='', max_length=5000)

class ReviewProtocolRequest(ReviewProtocolFields):
    expected_revision: int = Field(ge=0, strict=True)

class ReviewProtocol(ReviewProtocolFields):
    revision: int = Field(ge=1)
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewProtocolState(Contract):
    run_id: str
    revisions: list[ReviewProtocol]
