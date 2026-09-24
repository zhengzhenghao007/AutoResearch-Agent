"""Synthetic metric tests never confer human-review status on shipped fixtures."""
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent / 'fixtures' / 'evidence'


def api():
    assert importlib.util.find_spec('evaluation.evaluate_evidence'), 'Evidence evaluator is missing'
    return importlib.import_module('evaluation.evaluate_evidence')


def copy_corpus(tmp_path):
    shutil.copytree(ROOT, tmp_path / 'corpus')
    return tmp_path / 'corpus' / 'manifest.json'


def test_pending_corpus_has_no_scientific_metrics_and_runs_regressions():
    result = api().evaluate(ROOT / 'manifest.json')
    assert result['reviewed_count'] == 0
    assert result['metrics'] is None
    assert result['regressions']['passed'] == 7
    assert result['regressions']['failed'] == []


@pytest.mark.parametrize('mutation', ['hash', 'path', 'license', 'reviewer', 'date', 'unknown_status', 'duplicate'])
def test_rejects_invalid_manifest_and_provenance(tmp_path, mutation):
    module = api()
    path = copy_corpus(tmp_path)
    data = json.loads(path.read_text())
    record = data['records'][0]
    if mutation == 'hash': record['sha256'] = '0' * 64
    if mutation == 'path': record['file'] = '../outside.pdf'
    if mutation == 'license': record['license'] = ''
    if mutation == 'reviewer': record['status'] = 'human_reviewed'
    if mutation == 'date': record.update(status='human_reviewed', reviewer='Unit test simulation', reviewed_at='bad')
    if mutation == 'unknown_status': record['status'] = 'approved'
    if mutation == 'duplicate': data['records'].append(record.copy())
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError): module.evaluate(path)


def test_metric_math_counts_wrong_category_false_positive_and_missing(tmp_path):
    module = api()
    path = copy_corpus(tmp_path)
    data = json.loads(path.read_text())
    record = data['records'][0]
    # TEST-ONLY review provenance; this is not a human evaluation result.
    record.update(status='human_reviewed', reviewer='TEST ONLY simulated reviewer', reviewed_at='2026-09-18')
    record['annotations'] = [
        {'page': 1, 'quote': 'We propose a compact algorithm.', 'category': 'method', 'supported': True},
        {'page': 1, 'quote': 'Results show a measured increase.', 'category': 'method', 'supported': False},
        {'page': 1, 'quote': 'A second method is described here.', 'category': 'method', 'supported': True},
    ]
    path.write_text(json.dumps(data))
    result = module.evaluate(path)
    metrics = result['metrics']
    assert result['reviewed_count'] == 1
    assert metrics['categories']['method']['precision'] == 1
    assert metrics['categories']['method']['recall'] == pytest.approx(1 / 3)
    assert metrics['categories']['result']['precision'] == 0
    assert metrics['categories']['method']['missingness'] == pytest.approx(2 / 3)
    assert metrics['quote_location_rate'] == 1
    assert metrics['support_rate'] == 0.5


def test_reviewed_annotation_cannot_contain_fabricated_quote(tmp_path):
    module = api()
    path = copy_corpus(tmp_path)
    data = json.loads(path.read_text())
    data['records'][0]['annotations'][0]['quote'] = 'This invented quote does not exist in the document.'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='annotation quote'):
        module.evaluate(path)


def test_metrics_count_false_positives_and_undefined_denominators(tmp_path):
    module = api()
    path = copy_corpus(tmp_path)
    data = json.loads(path.read_text())
    for record in (data['records'][0], data['records'][-1]):
        record.update(status='human_reviewed', reviewer='TEST ONLY simulated reviewer', reviewed_at='2026-09-18')
    data['records'][-1]['annotations'] = []
    path.write_text(json.dumps(data))
    result = module.evaluate(path)
    assert result['reviewed_count'] == 2
    assert result['metrics']['categories']['method']['precision'] == 0.5
    assert result['metrics']['categories']['method']['recall'] == 1
    assert result['metrics']['categories']['experiment']['recall'] is None
    assert result['metrics']['categories']['experiment']['precision'] is None
    assert result['metrics']['support_rate'] == pytest.approx(2 / 3)


@pytest.mark.parametrize('mutation', ['wrong_page', 'pending_reviewer', 'duplicate_annotation', 'unknown_field'])
def test_annotation_and_review_boundary_rejects_invalid_records(tmp_path, mutation):
    module = api()
    path = copy_corpus(tmp_path)
    data = json.loads(path.read_text())
    record = data['records'][0]
    if mutation == 'wrong_page': record['annotations'][0]['page'] = 2
    if mutation == 'pending_reviewer': record['reviewer'] = 'Unverified identity'
    if mutation == 'duplicate_annotation': record['annotations'].append(record['annotations'][0].copy())
    if mutation == 'unknown_field': record['approved'] = True
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError): module.evaluate(path)


def test_cli_fails_when_synthetic_regression_expectation_is_not_met(tmp_path):
    path = copy_corpus(tmp_path)
    data = json.loads(path.read_text())
    data['records'][0]['expected_categories'] = ['experiment']
    path.write_text(json.dumps(data))
    result = subprocess.run([sys.executable, '-m', 'evaluation.evaluate_evidence', str(path)],
                            capture_output=True, text=True,
                            cwd=Path(__file__).resolve().parents[1])
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report['regressions'] == {'passed': 6, 'failed': ['normal']}
    assert report['metrics'] is None
