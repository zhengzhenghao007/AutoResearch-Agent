import json
import subprocess
import sys

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.research import get_workflow
from test_experiments import flow_run, payload, raw


def test_offline_create_csv_stats_and_provenance(tmp_path):
    flow, _ = flow_run(tmp_path)
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            created = client.post('/api/research/runs', json={'topic':'My experiment'})
            assert created.status_code == 200, created.text
            run_id = created.json()['id']
            assert created.json()['candidates'] == []
            base = f'/api/research/runs/{run_id}'
            metadata = payload(); metadata.pop('rows')
            csv = b'sample_id,temperature,score\ns1,0,\ns2,4,2\n'
            response = client.post(base+'/experiments/csv', files={'file':('data.csv',csv)},
                                   data={'metadata':json.dumps(metadata)})
            assert response.status_code == 200, response.text
            dataset = response.json()['experiments'][0]
            report = client.get(base+'/experiment-statistics')
            assert report.status_code == 200, report.text
            column = report.json()['datasets'][0]['columns'][0]
            assert column['mean'] == '2'
            assert column['references'][0] == {'sample_id':'s1','column':'temperature','value':'0'}
            assert report.json()['datasets'][0]['dataset_id'] == dataset['id']
            assert report.json()['scientific_validation'] == 'not_assessed'
            assert client.post(base+'/experiments/csv', files={'file':('bad.csv',csv)},
                               data={'metadata':'{"title":"x","title":"y"}'}).status_code == 400
            assert client.post(base+'/experiments/csv', files={'file':('big.csv',b' '*(1024*1024+1))},
                               data={'metadata':json.dumps(metadata)}).status_code == 413
    finally:
        app.dependency_overrides.clear()


def test_cli_offline_create_and_csv_statistics(tmp_path):
    command = [sys.executable,'research_cli.py','--store',str(tmp_path/'runs')]
    created = subprocess.run(command+['create','Observations'],capture_output=True,text=True)
    assert created.returncode == 0, created.stderr
    run_id = json.loads(created.stdout)['id']
    metadata = payload(); metadata.pop('rows')
    meta_path = tmp_path/'metadata.json'; meta_path.write_text(json.dumps(metadata),encoding='utf-8')
    csv_path = tmp_path/'data.csv'; csv_path.write_bytes(b'sample_id,temperature,score\ns1,0,\ns2,4,2\n')
    imported = subprocess.run(command+['import-experiment-csv',run_id,str(csv_path),'--metadata',str(meta_path)],capture_output=True,text=True)
    assert imported.returncode == 0, imported.stderr
    result = subprocess.run(command+['experiment-statistics',run_id],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['datasets'][0]['columns'][0]['mean'] == '2'


def test_near_limit_csv_envelope_roundtrips_api_and_cli(tmp_path):
    from schemas.experiments import MAX_EXPERIMENT_BYTES
    from services.experiments import parse_csv_experiment
    csv = b'sample_id,x\n' + b''.join((f's{i},0.'+'1'*1038+'\n').encode() for i in range(1000))
    csv = csv.rstrip(b'\n') + b'1'*(MAX_EXPERIMENT_BYTES-len(csv)) + b'\n'
    dataset = parse_csv_experiment(csv, {'title':'Boundary','columns':[{'name':'x'}]})
    envelope = dataset.raw_json.encode('utf-8')
    assert MAX_EXPERIMENT_BYTES < len(envelope) < 2*MAX_EXPERIMENT_BYTES
    flow, run = flow_run(tmp_path/'api')
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        with TestClient(app) as client:
            response = client.post(f'/api/research/runs/{run.id}/experiments',files={'file':('envelope.json',envelope)})
            assert response.status_code == 200, response.text
            assert response.json()['experiments'][0]['id'] == dataset.id
    finally:
        app.dependency_overrides.clear()
    cli_flow, cli_run = flow_run(tmp_path/'cli')
    path = tmp_path/'envelope.json'; path.write_bytes(envelope)
    result = subprocess.run([sys.executable,'research_cli.py','--store',str(cli_flow.store.root),
                             'import-experiment',cli_run.id,str(path)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert cli_flow.store.load(cli_run.id).experiments[0].id == dataset.id
