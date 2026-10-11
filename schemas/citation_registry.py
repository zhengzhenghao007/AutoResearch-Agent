"""Read-only provenance export; independent of persisted ResearchRun v1."""
from typing import Literal
from schemas.research import Contract, Category


class CitationEvidenceRef(Contract):
    id: str
    page: int
    quote: str


class CitationClaimRef(Contract):
    id: str
    text: str
    category: Category
    claim_type: Literal['paper_report', 'user_observation', 'synthesis', 'hypothesis', 'suggestion']
    evidence_ids: list[str]


class CitationSourceEntry(Contract):
    source_id: str
    sha256: str
    title: str
    kind: Literal['paper', 'user_data']
    uri: str
    arxiv_revision_id: str | None
    evidence: list[CitationEvidenceRef]
    claims: list[CitationClaimRef]


class CitationRegistry(Contract):
    schema_version: Literal[1] = 1
    run_id: str
    topic: str
    sources: list[CitationSourceEntry]
