"""Bounded, versioned manuscript sidecar contracts."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from schemas.manuscript_draft import ManuscriptDraft

Identifier = Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9:_-]{1,160}$')]
Digest = Annotated[str, StringConstraints(pattern=r'^[a-f0-9]{64}$')]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Sentence(Contract):
    id: Identifier
    text: Text
    kind: Literal['paper_report', 'user_observation', 'hypothesis', 'suggestion', 'placeholder']
    reference_ids: list[str] = Field(default_factory=list, max_length=100)


class Section(Contract):
    id: Identifier
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    sentences: list[Sentence] = Field(max_length=200)


class RevisionRequest(Contract):
    expected_revision: Identifier | None
    expected_input_sha256: Digest
    reason: Text
    sections: list[Section] | None = Field(default=None, min_length=1, max_length=30)


class Revision(Contract):
    id: Identifier
    number: int = Field(ge=1, le=20)
    created_at: datetime
    reason: Text
    content_sha256: Digest
    input_sha256: Digest
    sections: list[Section] = Field(min_length=1, max_length=30)
    source: ManuscriptDraft


class Finding(Contract):
    sentence_id: Identifier
    status: Literal['supported', 'unsupported', 'uncertain']
    rationale: Text


class Contradiction(Contract):
    sentence_ids: tuple[Identifier, Identifier]
    rationale: Text


class ReviewOutput(Contract):
    findings: list[Finding] = Field(max_length=500)
    contradictions: list[Contradiction] = Field(max_length=500)


class Review(ReviewOutput):
    id: Identifier
    revision_id: Identifier
    content_sha256: Digest
    input_sha256: Digest
    model: Text
    created_at: datetime
    scientific_validation: Literal['not_assessed'] = 'not_assessed'


class ReviewRequest(Contract):
    revision_id: Identifier
    allow_model: Literal[True]

    @field_validator('allow_model', mode='before')
    @classmethod
    def explicit_consent(cls, value):
        if value is not True:
            raise ValueError('Explicit boolean true consent is required')
        return value


class ApprovalRequest(Contract):
    revision_id: Identifier
    expected_review_count: int = Field(ge=0, le=100, strict=True)
    reviewer: Text
    note: Text
    confirm: Literal[True]

    @field_validator('confirm', mode='before')
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError('Explicit boolean true confirmation is required')
        return value


class Approval(Contract):
    revision_id: Identifier
    content_sha256: Digest
    input_sha256: Digest
    reviewer: Text
    note: Text
    created_at: datetime
    review_count: int = Field(default=0, ge=0, le=100)


class ManuscriptState(Contract):
    run_id: str
    current_input_sha256: Digest
    revisions: list[Revision] = Field(default_factory=list, max_length=20)
    reviews: list[Review] = Field(default_factory=list, max_length=100)
    approvals: list[Approval] = Field(default_factory=list, max_length=100)


class ManuscriptExport(Contract):
    filename: str
    markdown: str
    revision_id: Identifier
    content_sha256: Digest
