"""Strict, bounded model research working-note contracts."""
from typing import Annotated, Literal
from schemas.generated_prose import GeneratedProse
from pydantic import Field
from schemas.research import Contract

Text = Annotated[GeneratedProse, Field(min_length=1, max_length=3000)]
References = Annotated[list[str], Field(min_length=1, max_length=40)]

class ReasoningRequest(Contract):
    question: str = Field(min_length=1, max_length=2000)
    allow_model: bool = Field(default=False, strict=True)
    max_output_tokens: int = Field(default=3000, ge=256, le=4000, strict=True)

class MatrixRow(Contract):
    source_id: str
    research_question: Text
    method: Text
    results: Text
    limitations: Text
    evidence_ids: References
    uncertainty: Text

class Hypothesis(Contract):
    kind: Literal['hypothesis']
    text: Text
    evidence_ids: References
    validation_experiment: Text
    uncertainty: Text

class ReviewTheme(Contract):
    theme: Text
    text: Text
    kind: Literal['author_claim', 'synthesis']
    evidence_ids: References
    uncertainty: Text

class ReasoningReport(Contract):
    matrix: list[MatrixRow] = Field(min_length=1, max_length=20)
    hypotheses: list[Hypothesis] = Field(max_length=6)
    review: list[ReviewTheme] = Field(min_length=1, max_length=10)
    uncertainties: list[Text] = Field(min_length=1, max_length=20)
