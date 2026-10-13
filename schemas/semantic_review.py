from datetime import datetime, timezone
from typing import Literal
from pydantic import Field
from schemas.research import Contract, Claim, Source, Evidence, Page


class SemanticReviewRequest(Contract):
    claim_ids: list[str] = Field(min_length=1,max_length=20)
    allow_model: Literal[True]


class SemanticClaimInput(Contract):
    claim: Claim
    source: Source
    evidence: list[Evidence]
    pages: list[Page]


class SemanticClaimFinding(Contract):
    claim_id: str
    verdict: Literal['supported','unsupported','uncertain']
    evidence_ids: list[str] = Field(min_length=1,max_length=200)
    rationale: str = Field(min_length=1,max_length=2000)


class ContradictionFinding(Contract):
    claim_ids: list[str] = Field(min_length=2,max_length=2)
    rationale: str = Field(min_length=1,max_length=2000)


class SemanticOutput(Contract):
    claims: list[SemanticClaimFinding] = Field(max_length=20)
    contradictions: list[ContradictionFinding] = Field(max_length=50)


class SemanticReviewReport(Contract):
    schema_version: Literal[1] = 1
    run_id: str
    input_sha256: str
    input_claims: list[SemanticClaimInput]
    omitted_claim_count: int
    model: str
    generated_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    output: SemanticOutput
    scientific_validation: Literal['not_assessed'] = 'not_assessed'
    scope: str = ('Unverified model judgments on selected claims and their cited pages only. '
                  'Support refers to contextual meaning and category, not scientific truth. '
                  'Contradictions are potential conflicts requiring matching methods and conditions. '
                  'No findings does not prove absence of contradictions. No automatic revisions.')
