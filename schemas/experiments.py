"""Numeric user observations, separate from paper quotations and generated claims."""
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

MAX_CSV_METADATA_BYTES = 65536
MAX_EXPERIMENT_BYTES = 1024 * 1024
MAX_EXPERIMENT_ENVELOPE_BYTES = 2 * MAX_EXPERIMENT_BYTES
Number = StrictInt | Annotated[float, Field(strict=True, allow_inf_nan=False)]


class ExperimentContract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ExperimentColumn(ExperimentContract):
    name: str = Field(pattern=r'^[A-Za-z][A-Za-z0-9_]{0,63}$')
    unit: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator('unit')
    @classmethod
    def nonblank_unit(cls, value):
        if value is not None and not value.strip():
            raise ValueError('Use null for unknown units')
        return value


class ObservationRow(ExperimentContract):
    sample_id: str = Field(min_length=1, max_length=100)
    values: dict[str, Number | None]

    @field_validator('sample_id')
    @classmethod
    def nonblank_sample(cls, value):
        if not value.strip() or value != value.strip():
            raise ValueError('Sample IDs must be nonblank with no surrounding whitespace')
        return value


class CsvMetadata(ExperimentContract):
    title: str = Field(min_length=1, max_length=200)
    protocol: str | None = Field(default=None, min_length=1, max_length=10000)
    statistical_method: str | None = Field(default=None, min_length=1, max_length=2000)
    columns: list[ExperimentColumn] = Field(min_length=1, max_length=50)

    @field_validator('title', 'protocol', 'statistical_method')
    @classmethod
    def nonblank_metadata(cls, value):
        if value is not None and not value.strip():
            raise ValueError('Metadata must be nonblank; use null when unknown')
        return value

    @model_validator(mode='after')
    def unique_columns(self):
        names = [column.name for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate column names')
        return self


class ExperimentInput(CsvMetadata):
    rows: list[ObservationRow] = Field(min_length=1, max_length=1000)

    @model_validator(mode='after')
    def rectangular_unique_data(self):
        names = [column.name for column in self.columns]
        ids = [row.sample_id for row in self.rows]
        if len(names) != len(set(names)) or len(ids) != len(set(ids)):
            raise ValueError('Duplicate column names or sample IDs')
        if any(set(row.values) != set(names) for row in self.rows):
            raise ValueError('Every row must contain exactly the declared columns; use null for missing values')
        return self


class ExperimentDataset(ExperimentContract):
    id: str = Field(pattern=r'^[a-f0-9]{64}$')
    kind: Literal['user_data'] = 'user_data'
    claim_type: Literal['user_observation'] = 'user_observation'
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    input_format: Literal['json', 'csv'] = 'json'
    raw_json: str = Field(max_length=MAX_EXPERIMENT_ENVELOPE_BYTES)
    data: ExperimentInput
    imported_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ColumnCompleteness(ExperimentContract):
    name: str
    unit: str | None
    observed_count: int
    missing_count: int


class DatasetCompleteness(ExperimentContract):
    source_sha256: str | None = None
    input_format: Literal['json', 'csv'] = 'json'
    dataset_id: str
    sha256: str
    title: str
    protocol: str | None
    statistical_method: str | None
    sample_count: int
    columns: list[ColumnCompleteness]
    missing_metadata: list[str]


class ExperimentReport(ExperimentContract):
    schema_version: Literal[1] = 1
    run_id: str
    datasets: list[DatasetCompleteness]
    scientific_validation: Literal['not_assessed'] = 'not_assessed'
    scope: str = ('User-supplied numeric observations only. Sample count is the number of unique '
                  'user-declared sample IDs, not verified independent replicates. Units, protocols '
                  'and statistical methods are unverified metadata. No imputation, statistical '
                  'inference, paper claims or model-generated results.')
