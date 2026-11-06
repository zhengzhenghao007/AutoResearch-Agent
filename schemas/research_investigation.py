"""Bounded evidence-led investigation report for selected papers."""
from pydantic import Field
from schemas.research import Contract, Evidence


class InvestigationRequest(Contract):
    source_ids: list[str] = Field(default_factory=list, max_length=100)


class InvestigationCandidate(Contract):
    claim_id: str
    source_id: str
    title: str
    quotation: Evidence
    related_passages: list[Evidence]
    question: str
    novelty: str = 'Unverified; similar-work search and scientific review required.'


class InvestigationReport(Contract):
    input_sha256: str
    goal: str
    source_ids: list[str]
    candidates: list[InvestigationCandidate]
    limitations: list[str]
    source_titles: dict[str, str]
    total_candidates: int
