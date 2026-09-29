"""Read-only relationship clues, not verified paper equivalence."""
from typing import Literal
from pydantic import Field
from schemas.research import Contract


class DuplicateMember(Contract):
    entity_type: Literal['candidate', 'processed_source']
    entity_id: str
    title: str
    uri: str


class DuplicateGroup(Contract):
    kind: Literal['exact_arxiv_identifier', 'same_pdf_bytes', 'shared_user_supplied_doi']
    identity_value: str
    identity_status: Literal['explicit_identifier', 'exact_content_hash', 'user_supplied_unverified']
    members: list[DuplicateMember] = Field(min_length=2)


class CandidateSourceLink(Contract):
    candidate_id: str
    source_id: str
    arxiv_identifier: str


class SourceDuplicateReport(Contract):
    schema_version: Literal[1] = 1
    run_id: str
    groups: list[DuplicateGroup]
    candidate_source_links: list[CandidateSourceLink]
