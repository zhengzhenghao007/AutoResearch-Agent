"""Concise advisory synthesis with literal page references."""
from typing import Literal
from pydantic import Field, StrictBool
from schemas.research import Contract


class QuickReadRequest(Contract):
    allow_model: StrictBool = False


class QuickReadReference(Contract):
    page: int = Field(ge=1)
    quote: str = Field(min_length=12, max_length=1500)


class QuickReadPoint(Contract):
    text: str = Field(min_length=1, max_length=700)
    references: list[QuickReadReference] = Field(min_length=1, max_length=5)
    kind: Literal['paper_report', 'author_claim', 'hypothesis', 'goal_analysis'] = 'paper_report'


class QuickReadOutput(Contract):
    one_sentence: QuickReadPoint | None
    main_points: list[QuickReadPoint] = Field(max_length=5)
    problem: list[QuickReadPoint] = Field(max_length=3)
    innovations: list[QuickReadPoint] = Field(max_length=3)
    methods: list[QuickReadPoint] = Field(max_length=4)
    findings_applications: list[QuickReadPoint] = Field(max_length=4)
    limitations: list[QuickReadPoint] = Field(max_length=4)
    goal_relevance: list[QuickReadPoint] = Field(max_length=3)
    suggested_directions: list[QuickReadPoint] = Field(max_length=3)
    missing_information: list[str] = Field(max_length=12)


class QuickReadCoverage(Contract):
    total_pages: int
    parsed_pages: int
    included_pages: list[int]
    omitted_pages: list[int]
    truncated_pages: list[int]
    ocr_pages: list[int]
    notes: list[str]


class QuickReadUsage(Contract):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class PaperQuickRead(Contract):
    run_id: str
    source_id: str
    source_sha256: str
    input_sha256: str
    goal: str | None
    model: str
    usage: QuickReadUsage
    coverage: QuickReadCoverage
    output: QuickReadOutput
    advisory: str = 'Advisory synthesis; quotations support source attribution, not scientific validity or verified novelty. Innovations are author claims; suggested directions are hypotheses.'
