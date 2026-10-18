import hashlib
import json
import pytest
from services import experiments as service
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


def metadata():
    return {'title': 'CSV observations', 'columns': [{'name': 'x', 'unit': 'm'}]}


def test_csv_preserves_original_and_metadata_identity():
    raw = b'\xef\xbb\xbfsample_id,x\r\n"s,1",0\r\ns2,\r\ns3,-1.25e2\r\n'
    dataset = service.parse_csv_experiment(raw, metadata())
    assert dataset.input_format == 'csv'
    assert dataset.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert dataset.sha256 == hashlib.sha256(dataset.raw_json.encode()).hexdigest()
    assert json.loads(dataset.raw_json)['csv_text'].encode() == raw
    assert [r.values['x'] for r in dataset.data.rows] == [0, None, -125]
    assert dataset.data.rows[0].sample_id == 's,1'
    restored = service.parse_experiment(dataset.raw_json.encode())
    assert restored.data == dataset.data and restored.id == dataset.id
    changed = service.parse_csv_experiment(raw, dict(metadata(), title='Other'))
    assert changed.id != dataset.id and changed.source_sha256 == dataset.source_sha256


@pytest.mark.parametrize('raw', [
    b'', b'\xff', b'sample_id,x\n', b'sample_id,y\ns,1',
    b'x,sample_id\n1,s', b'sample_id,x\ns,1,2', b'sample_id,x\ns',
    b'sample_id,x\n\ns,1', b'sample_id,x\ns,1\ns,2',
    b'sample_id,x\n"s,1', b'sample_id,x\n s,1',
    b'sample_id,x\ns,NaN', b'sample_id,x\ns,Infinity', b'sample_id,x\ns,true',
    b'sample_id,x\ns,=1+2', b'sample_id,x\ns,+1', b'sample_id,x\ns,01',
    b'sample_id,x\ns,1e999', b'sample_id,x\ns, 1', b'sample_id,x\ns,null',
    b'sample_id,x\ns,1\n\n', b'x' * (1024 * 1024 + 1),
    b'sample_id,x\n' + b''.join(f's{i},1\n'.encode() for i in range(1001)),
], ids=[str(i) for i in range(23)])
def test_invalid_csv_rejected(raw):
    with pytest.raises(ValueError):
        service.parse_csv_experiment(raw, metadata())


@pytest.mark.parametrize('meta', [dict(title=' ', columns=[{'name':'x'}]),
    dict(title='x', columns=[{'name':'x'}, {'name':'x'}]),
    dict(title='x', columns=[]), dict(title='x', columns=[{'name':'sample_id'}]),
    dict(title='x', columns=[{'name':f'x{i}'} for i in range(51)])])
def test_invalid_metadata_rejected(meta):
    with pytest.raises(ValueError):
        service.parse_csv_experiment(b'sample_id,x\ns,1', meta)


def test_csv_import_persistence_report_and_binding(tmp_path):
    store = ResearchStore(tmp_path)
    flow = EvidenceWorkflow(store=store, search=lambda *a, **k: [])
    run = flow.search('CSV')
    raw = b'sample_id,x\ns,2\n'
    result = service.import_csv_experiment(store, run.id, raw, metadata())
    assert store.load(run.id) == result
    summary = service.build_experiment_report(result).datasets[0]
    assert summary.input_format == 'csv' and summary.source_sha256 == hashlib.sha256(raw).hexdigest()
    before = store._path(run.id).read_bytes()
    with pytest.raises(ValueError):
        service.import_csv_experiment(store, run.id, raw, metadata())
    assert store._path(run.id).read_bytes() == before
    for field, value in [('source_sha256', '0' * 64), ('source_sha256', None), ('input_format', 'json')]:
        altered = result.experiments[0].model_copy(update={field: value})
        with pytest.raises(ValueError):
            service.validate_experiments([altered])


def test_json_legacy_provenance_supported():
    raw = json.dumps(dict(metadata(), rows=[{'sample_id':'s', 'values':{'x':1}}])).encode()
    dataset = service.parse_experiment(raw)
    assert dataset.input_format == 'json'
    assert dataset.source_sha256 == hashlib.sha256(raw).hexdigest()
    service.validate_experiments([dataset.model_copy(update={'source_sha256':None})])



def test_metadata_decode_validates_unique_keys_and_bounds():
    assert service.parse_csv_metadata(json.dumps(metadata()).encode())['title'] == 'CSV observations'
    for raw in [b'{"title":"a","title":"b","columns":[{"name":"x"}]}', b'\xff', b'{}', b' ' * 65537]:
        with pytest.raises(ValueError):
            service.parse_csv_metadata(raw)
