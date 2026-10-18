"""Offline descriptive-v1: exact rational accumulation and correctly rounded output."""
from decimal import Context, Decimal, MAX_EMAX, MIN_EMIN, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from math import isqrt

from schemas.experiment_statistics import (
    ColumnStatistics, DatasetStatistics, ExperimentStatisticsReport, ObservationReference,
)


def _rounded(value: Fraction, *, square_root=False) -> str:
    """28 significant digits, ties to even, using exact integer rounding tests.

    Decimal only formats the final rounded coefficient. Even square roots are
    rounded by comparing the exact rational radicand with the squared midpoint,
    so neither cancellation nor intermediate Decimal rounding loses information.
    """
    if not value:
        return '0'
    negative = value < 0
    value = abs(value)
    numerator, denominator = value.numerator, value.denominator
    exponent = Decimal(numerator).adjusted() - Decimal(denominator).adjusted()
    threshold = Fraction(10**exponent) if exponent >= 0 else Fraction(1, 10**-exponent)
    if value < threshold:
        exponent -= 1
    if square_root:
        exponent //= 2
    scale = 27 - exponent
    power = scale * (2 if square_root else 1)
    if power >= 0:
        numerator *= 10**power
    else:
        denominator *= 10**-power
    coefficient = isqrt(numerator // denominator) if square_root else numerator // denominator
    if square_root:
        comparison = 4*numerator - denominator*(2*coefficient+1)**2
    else:
        comparison = 2*numerator - denominator*(2*coefficient+1)
    if comparison > 0 or (comparison == 0 and coefficient % 2):
        coefficient += 1
    with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN, Emax=MAX_EMAX, Emin=MIN_EMIN)):
        result = Decimal(-coefficient if negative else coefficient).scaleb(-scale)
        return str(result.normalize())


def build_experiment_statistics(run) -> ExperimentStatisticsReport:
    from schemas.research import ResearchRun
    from services.research_validation import validate_run

    run = ResearchRun.model_validate(run.model_dump())
    validate_run(run)
    datasets = []
    for dataset in run.experiments:
        columns = []
        for column in dataset.data.columns:
            observations = [(row.sample_id, Decimal(str(row.values[column.name])))
                            for row in dataset.data.rows if row.values[column.name] is not None]
            count = len(observations)
            values = [Fraction(value) for _, value in observations]
            mean = sum(values, Fraction()) / count if count else None
            variance = (sum((value*value for value in values), Fraction()) - count*mean*mean) / (count-1) if count > 1 else None
            warnings = []
            if not count:
                warnings.append('No nonmissing observations; all statistics are unavailable.')
            elif count == 1:
                warnings.append('Sample standard deviation requires at least two observations.')
            if count < len(dataset.data.rows):
                warnings.append('Missing observations were excluded; no values were imputed.')
            if column.unit is None:
                warnings.append('Measurement unit is unspecified.')
            columns.append(ColumnStatistics(
                name=column.name, unit=column.unit, observed_count=count,
                missing_count=len(dataset.data.rows)-count,
                mean=_rounded(mean) if mean is not None else None,
                minimum=str(min(value for _, value in observations)) if count else None,
                maximum=str(max(value for _, value in observations)) if count else None,
                sample_standard_deviation=_rounded(variance, square_root=True) if variance is not None else None,
                references=[ObservationReference(sample_id=sample_id, column=column.name, value=str(value))
                            for sample_id, value in observations],
                status='computed' if count > 1 else 'insufficient_samples' if count else 'no_observations',
                warnings=warnings,
            ))
        datasets.append(DatasetStatistics(dataset_id=dataset.id, sha256=dataset.sha256,
                                          title=dataset.data.title, columns=columns))
    return ExperimentStatisticsReport(run_id=run.id, datasets=datasets)
