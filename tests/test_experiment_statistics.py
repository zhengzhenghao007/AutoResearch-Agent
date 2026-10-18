import importlib
import json
from decimal import Decimal, localcontext

import pytest

from schemas.research import ResearchRun
from services.experiments import parse_experiment
from services.research_store import ResearchStore


def build(run):
    return importlib.import_module('services.experiment_statistics').build_experiment_statistics(run)


def run_for(values):
    raw = json.dumps(dict(title='Measurements', columns=[dict(name='x', unit='m')],
                         rows=[dict(sample_id=f's{i}', values=dict(x=x)) for i, x in enumerate(values)])).encode()
    return ResearchRun(id='a'*32, topic='test', plan=[], experiments=[parse_experiment(raw)])


def column(values):
    return build(run_for(values)).datasets[0].columns[0]


def test_hand_calculated_statistics_and_references():
    result = column([0, 2, None, 4])
    assert (result.observed_count, result.missing_count) == (3, 1)
    assert (result.mean, result.minimum, result.maximum, result.sample_standard_deviation) == ('2', '0', '4', '2')
    assert result.status == 'computed'
    assert [r.model_dump() for r in result.references] == [
        dict(sample_id='s0', column='x', value='0'), dict(sample_id='s1', column='x', value='2'),
        dict(sample_id='s3', column='x', value='4')]


@pytest.mark.parametrize('values,status,mean', [([None, None], 'no_observations', None), ([0, None], 'insufficient_samples', '0')])
def test_missing_and_single_observation(values, status, mean):
    result = column(values)
    assert result.status == status and result.mean == mean
    assert result.sample_standard_deviation is None
    assert result.warnings
    if mean is None:
        assert result.minimum is None and result.maximum is None and result.references == []


def test_extreme_cancellation_and_finite_variance():
    result = column([1e308, 1, -1e308])
    assert result.mean == '0.3333333333333333333333333333'
    assert Decimal(result.sample_standard_deviation) == Decimal('1e308')
    assert result.references[0].value == '1E+308'


def test_huge_integers_keep_small_spread():
    big = 10**1000
    result = column([big, big+2, big+4])
    assert result.sample_standard_deviation == '2'
    assert result.minimum == str(big) and result.maximum == str(big+4)
    assert result.references[1].value == str(big+2)


def test_rounding_and_global_decimal_context_do_not_change_result():
    run = run_for([1, 2])
    expected = build(run).model_dump()
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.Emax = 2
        assert build(run).model_dump() == expected
    assert expected['datasets'][0]['columns'][0]['sample_standard_deviation'] == '0.7071067811865475244008443621'


def test_report_read_only_and_bound_to_sources(tmp_path):
    run = run_for([0.1, 0.2]*500)
    store = ResearchStore(tmp_path)
    store.save(run)
    path = store._path(run.id)
    before = path.read_bytes(), path.stat().st_mtime_ns, run.model_dump_json()
    report = build(run)
    assert report.algorithm == 'descriptive-v1' and report.scientific_validation == 'not_assessed'
    assert report.run_id == run.id and report.datasets[0].sha256 == run.experiments[0].sha256
    assert len(report.datasets[0].columns[0].references) == 1000
    assert (path.read_bytes(), path.stat().st_mtime_ns, run.model_dump_json()) == before


@pytest.mark.parametrize('target', ['hash', 'value', 'run'])
def test_tampered_input_rejected(target):
    run = run_for([1, 2])
    if target == 'hash':
        run.experiments[0].sha256 = '0'*64
    elif target == 'value':
        run.experiments[0].data.rows[0].values['x'] = 8
    else:
        run.selected_ids = ['nonexistent']
    with pytest.raises(ValueError):
        build(run)

@pytest.mark.parametrize('value,expected', [
    (10**28+5, '1E+28'),
    (10**28+15, '1.000000000000000000000000002E+28'),
    (-(10**28+15), '-1.000000000000000000000000002E+28'),
])
def test_mean_rounds_exact_ties_to_even(value, expected):
    assert column([value]).mean == expected


def test_subnormal_and_constant_values():
    result = column([5e-324, 5e-324])
    assert result.mean == '5E-324'
    assert result.sample_standard_deviation == '0'
    assert result.minimum == '5E-324'


def test_empty_run_reports_no_datasets():
    run = ResearchRun(id='a'*32, topic='empty', plan=[])
    assert build(run).datasets == []
