"""Reproducible, descriptive-only statistics and their observation references."""
from typing import Literal

from pydantic import Field

from schemas.experiments import ExperimentContract


class ObservationReference(ExperimentContract):
    sample_id: str
    column: str
    value: str


class ColumnStatistics(ExperimentContract):
    name: str
    unit: str | None
    observed_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    mean: str | None
    minimum: str | None
    maximum: str | None
    sample_standard_deviation: str | None
    references: list[ObservationReference]
    status: Literal['computed', 'no_observations', 'insufficient_samples']
    warnings: list[str]


class DatasetStatistics(ExperimentContract):
    dataset_id: str
    sha256: str
    title: str
    columns: list[ColumnStatistics]


class ExperimentStatisticsReport(ExperimentContract):
    schema_version: Literal[1] = 1
    run_id: str
    algorithm: Literal['descriptive-v1'] = 'descriptive-v1'
    scientific_validation: Literal['not_assessed'] = 'not_assessed'
    scope: str = (
        'Descriptive statistics of user-supplied observations only. Integers are exact; '
        'floats use their shortest round-trip decimal representation. References and '
        'extrema preserve those decimal values. Mean and sample standard deviation '
        '(n-1 denominator) are rounded to 28 significant digits, ROUND_HALF_EVEN, '
        'after exact rational arithmetic. Nulls are excluded without imputation. '
        'User-declared sample IDs are not verified independent replicates. Units and '
        'protocols are unverified. No grouping, p-values, causal claims, statistical '
        'inference, model-generated results or scientific validation.'
    )
    datasets: list[DatasetStatistics]
