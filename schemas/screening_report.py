"""Read-only screening annotations, separate from analysis selection."""
from typing import Literal
from pydantic import Field
from schemas.research import Contract, Candidate, CandidateDecision


class ScreeningCounts(Contract):
    total: int = Field(ge=0)
    include: int = Field(ge=0)
    exclude: int = Field(ge=0)
    undecided: int = Field(ge=0)
    selected: int = Field(ge=0)


class ScreeningItem(Contract):
    candidate: Candidate
    status: Literal['include', 'exclude', 'undecided']
    selected_for_analysis: bool
    latest: CandidateDecision | None
    history: list[CandidateDecision]
    selection_notice: Literal['excluded_but_selected', 'included_but_not_selected', 'selected_without_decision'] | None


class ScreeningReport(Contract):
    schema_version: Literal[1] = 1
    run_id: str
    topic: str
    counts: ScreeningCounts
    items: list[ScreeningItem]
    scope: str = ('User annotations only; selected_for_analysis records explicit selection, not successful processing. '
                  'No eligibility, scientific validity or completeness assessment is performed.')
