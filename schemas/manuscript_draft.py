"""Read-only drafting material; approval and scientific validity are never inferred."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from schemas.research import Source, Evidence
from schemas.experiment_statistics import ColumnStatistics


class DraftContract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class PaperBinding(DraftContract):
    claim_id: str
    source: Source
    evidence: list[Evidence]
    parsed_pages: int
    total_pages: int
    truncated: bool


class ComputationBinding(DraftContract):
    dataset_id: str
    sha256: str
    title: str
    algorithm: Literal['descriptive-v1'] = 'descriptive-v1'
    column: ColumnStatistics


class DraftBlock(DraftContract):
    id: str
    kind: Literal['paper_claim', 'user_statistics', 'placeholder']
    text: str
    paper: PaperBinding | None = None
    computation: ComputationBinding | None = None


class DraftSection(DraftContract):
    id: str
    title: str
    purpose: str
    blocks: list[DraftBlock]


class ManuscriptDraft(DraftContract):
    schema_version: Literal[1] = 1
    builder: Literal['evidence-draft-v1'] = 'evidence-draft-v1'
    run_id: str
    topic: str
    input_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    sections: list[DraftSection]
    omitted_legacy_observation_claims: int = 0
    scientific_validation: Literal['not_assessed'] = 'not_assessed'
    contradiction_review: Literal['not_assessed'] = 'not_assessed'
    approval: Literal['not_requested'] = 'not_requested'
    statistics_scope: str
    scope: str = ('Read-only chapter material, not a finished manuscript or approved publication export. '
                  'Paper statements are saved quotations, not verified scientific facts. User results '
                  'are descriptive calculations, not causal claims or independent validation. '
                  'Placeholders identify missing material in this record, not gaps in the entire field. '
                  'No model, narrative rewriting, contradiction assessment or human approval is performed.')
