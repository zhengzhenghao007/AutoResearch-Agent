"""Advisory language cues, never a semantic approval or automatic correction."""
from typing import Literal
from schemas.research import Contract, Category, Evidence


class ClaimReviewFlag(Contract):
    code: Literal['planning_language_in_observation'] = 'planning_language_in_observation'
    claim_id: str
    source_id: str
    category: Category
    claim_text: str
    matched_text: str
    evidence: list[Evidence]
    message: str = ('Planning language occurs in an experiment/result claim. Inspect the full context '
                    'before treating this as a completed observation; mixed past and future statements may be legitimate.')


class ClaimReviewReport(Contract):
    schema_version: Literal[1] = 1
    rule_version: Literal['planning-language-en-v1'] = 'planning-language-en-v1'
    run_id: str
    claim_count: int
    checked_claim_count: int
    flagged_claim_count: int
    flags: list[ClaimReviewFlag]
    semantic_validation: Literal['not_assessed'] = 'not_assessed'
    scope: str = ('Advisory English phrase matching on saved experiment/result claims only. '
                  'No entailment, contradiction, scientific validity or other-language assessment. '
                  'Zero flags is not approval. No claims or categories are changed.')
