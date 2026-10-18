import copy
import hashlib
import importlib
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


def service():
    return importlib.import_module('services.experiments')


def payload():
    return dict(title='Measurements', protocol=None, statistical_method=None,
                columns=[dict(name='temperature', unit='C'), dict(name='score', unit=None)],
                rows=[dict(sample_id='s1', values=dict(temperature=0, score=None)),
                      dict(sample_id='s2', values=dict(temperature=23.5, score=2))])


def raw(value=None):
    return json.dumps(payload() if value is None else value, ensure_ascii=False).encode('utf-8')


def flow_run(tmp_path):
    flow = EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [])
    return flow, flow.search('Observations')


def test_import_preserves_bytes_and_separates_observations(tmp_path):
    flow, run = flow_run(tmp_path)
    data = b'\xef\xbb\xbf' + raw()
    result = service().import_experiment(flow.store, run.id, data)
    dataset = result.experiments[0]
    assert dataset.raw_json.encode('utf-8') == data
    assert dataset.sha256 == hashlib.sha256(data).hexdigest()
    assert dataset.kind == 'user_data' and dataset.claim_type == 'user_observation'
    assert result.papers == run.papers and result.generated_claims == run.generated_claims
    assert result.artifacts == run.artifacts and result.review == run.review
    assert flow.store.load(run.id) == result
    path = flow.store._path(run.id)
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    report = service().build_experiment_report(result)
    assert report.scientific_validation == 'not_assessed'
    dataset_report = report.datasets[0]
    assert dataset_report.sample_count == 2
    assert dataset_report.columns[0].observed_count == 2
    assert dataset_report.columns[1].missing_count == 1
    assert set(dataset_report.missing_metadata) == {'protocol', 'statistical_method', 'unit:score'}
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize('mutation', [
    lambda p: p['rows'][0]['values'].update(score=True),
    lambda p: p['rows'][0]['values'].update(score='2'),
    lambda p: p['rows'][0]['values'].update(score=float('nan')),
    lambda p: p['rows'][0]['values'].update(score=float('inf')),
    lambda p: p['rows'][0]['values'].pop('score'),
    lambda p: p['rows'][0]['values'].update(unknown=1),
    lambda p: p['rows'].append(copy.deepcopy(p['rows'][0])),
    lambda p: p['columns'].append(copy.deepcopy(p['columns'][0])),
    lambda p: p.update(rows=[]),
    lambda p: p.update(title='  '),
    lambda p: p.update(protocol='  '),
    lambda p: p.update(claim_type='paper_report'),
])
def test_invalid_import_never_rewrites_snapshot(tmp_path, mutation):
    flow, run = flow_run(tmp_path)
    path = flow.store._path(run.id)
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    value = payload(); mutation(value)
    with pytest.raises(ValueError):
        service().import_experiment(flow.store, run.id, raw(value))
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize('data', [b'{"title":"a","title":"b"}', b'\xff', b'[]', b'{' , b' ' * (1024*1024+1)],
                         ids=['duplicate-key', 'invalid-utf8', 'array', 'invalid-json', 'oversize'])
def test_malformed_inputs_rejected(tmp_path, data):
    flow, run = flow_run(tmp_path)
    with pytest.raises(ValueError):
        service().import_experiment(flow.store, run.id, data)


def test_duplicate_and_budget_and_integrity(tmp_path):
    flow, run = flow_run(tmp_path)
    result = service().import_experiment(flow.store, run.id, raw())
    with pytest.raises(ValueError, match='already'):
        service().import_experiment(flow.store, run.id, raw())
    for field, value in [('sha256', 'a'*64), ('raw_json', '{}')]:
        corrupt = result.model_copy(deep=True)
        setattr(corrupt.experiments[0], field, value)
        with pytest.raises(ValueError):
            flow.store.save(corrupt)
    corrupt = result.model_copy(deep=True)
    corrupt.experiments[0].data.rows[0].values['score'] = 99
    with pytest.raises(ValueError):
        flow.store.save(corrupt)
    for index in range(19):
        p = payload(); p['title'] = str(index)
        service().import_experiment(flow.store, run.id, raw(p))
    with pytest.raises(ValueError, match='20'):
        service().import_experiment(flow.store, run.id, raw(dict(payload(), title='extra')))


def test_old_run_and_api_cli(tmp_path):
    flow, run = flow_run(tmp_path)
    old = run.model_dump(mode='json'); old.pop('experiments', None)
    flow.store._path(run.id).write_text(json.dumps(old), encoding='utf-8')
    assert flow.store.load(run.id).experiments == []
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            url = f'/api/research/runs/{run.id}/experiments'
            assert client.get(url).json()['datasets'] == []
            response = client.post(url, files={'file':('../../private.json',raw(),'application/json')})
            assert response.status_code == 200, response.text
            assert response.json()['experiments'][0]['data']['title'] == 'Measurements'
            assert client.get(url).json()['datasets'][0]['sample_count'] == 2
            assert client.post(url, files={'file':('bad.json',b'{}')}).status_code == 400
            assert client.post(url, files={'file':('big.json',b' '*(2*1024*1024+1))}).status_code == 413
            assert client.get('/api/research/runs/'+'0'*32+'/experiments').status_code == 404
    finally:
        app.dependency_overrides.clear()
    p = payload(); p['title'] = 'CLI import'
    path = tmp_path / 'input.json'; path.write_bytes(raw(p))
    command = [sys.executable,'research_cli.py','--store',str(tmp_path)]
    imported = subprocess.run(command+['import-experiment',run.id,str(path)],capture_output=True,text=True)
    assert imported.returncode == 0, imported.stderr
    exported = subprocess.run(command+['experiments',run.id],capture_output=True,text=True)
    assert exported.returncode == 0, exported.stderr
    assert len(json.loads(exported.stdout)['datasets']) == 2


def test_disk_tampering_rejected_and_atomic_failure_preserves_run(tmp_path, monkeypatch):
    flow, run = flow_run(tmp_path)
    service().import_experiment(flow.store, run.id, raw())
    path = flow.store._path(run.id)
    before = path.read_bytes()
    corrupt = json.loads(before)
    corrupt['experiments'][0]['data']['rows'][0]['values']['score'] = 50
    path.write_text(json.dumps(corrupt), encoding='utf-8')
    with pytest.raises(ValueError, match='binding'):
        flow.store.load(run.id)
    path.write_bytes(before)

    def fail_replace(*args):
        raise OSError('simulated atomic replacement failure')

    monkeypatch.setattr('services.research_store.os.replace', fail_replace)
    with pytest.raises(OSError, match='replacement'):
        service().import_experiment(flow.store, run.id, raw(dict(payload(), title='Another dataset')))
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]
    assert len(flow.store.load(run.id).experiments) == 1


def test_existing_paper_derivatives_unchanged(tmp_path):
    from test_claim_review import make_run
    flow, run = make_run(tmp_path, 'We report an experiment with measured observations.')
    result = service().import_experiment(flow.store, run.id, raw())
    expected = run.model_dump(); expected['experiments'] = result.model_dump()['experiments']
    assert result.model_dump() == expected


@pytest.mark.parametrize('mutation', [
    lambda p: p.update(columns=[dict(name='v'+str(i)) for i in range(51)]),
    lambda p: p.update(rows=[dict(sample_id=str(i), values=dict(temperature=1, score=2)) for i in range(1001)]),
    lambda p: p['columns'][0].update(name=' bad'),
    lambda p: p['columns'][0].update(unit=' '),
    lambda p: p['rows'][0].update(sample_id=' '),
])
def test_schema_limits(mutation):
    value = payload(); mutation(value)
    with pytest.raises(ValueError):
        service().parse_experiment(raw(value))


def test_duplicate_nested_keys_and_invalid_unicode():
    valid = raw()
    for data in [valid.replace(b'"score": null', b'"score": 1, "score": null'),
                 valid.replace(b'Measurements', b'\\ud800'),
                 valid.replace(b'23.5', b'1e999')]:
        with pytest.raises(ValueError):
            service().parse_experiment(data)
