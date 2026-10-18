"""Bounded offline import and deterministic completeness checks."""
import csv
import io
import re
import hashlib
import json

from schemas.experiments import (
    MAX_CSV_METADATA_BYTES, MAX_EXPERIMENT_BYTES, MAX_EXPERIMENT_ENVELOPE_BYTES, CsvMetadata, ExperimentInput, ExperimentDataset, ExperimentReport,
    DatasetCompleteness, ColumnCompleteness,
)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON object key')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('Nonfinite JSON number')


def parse_experiment(data: bytes) -> ExperimentDataset:
    if not data or len(data) > MAX_EXPERIMENT_ENVELOPE_BYTES:
        raise ValueError('Experiment JSON must be 1 byte to 1 MiB')
    try:
        text = data.decode('utf-8')
        value = json.loads(text.removeprefix('\ufeff'), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
        if isinstance(value, dict) and value.get('format') == 'csv':
            if set(value) != {'format', 'csv_text', 'metadata'} or not isinstance(value['csv_text'], str):
                raise ValueError('Invalid CSV envelope')
            dataset = parse_csv_experiment(value['csv_text'].encode('utf-8'), value['metadata'])
            if dataset.raw_json != text:
                raise ValueError('CSV envelope must use canonical encoding')
            return dataset
        if len(data) > MAX_EXPERIMENT_BYTES:
            raise ValueError('Experiment JSON exceeds 1 MiB')
        parsed = ExperimentInput.model_validate(value)
        # Reject escaped unpaired surrogates, which cannot round-trip as UTF-8.
        json.dumps(parsed.model_dump(), ensure_ascii=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError) as exc:
        raise ValueError('Invalid experiment JSON: check schema, unique keys, finite numeric values and UTF-8') from exc
    digest = hashlib.sha256(data).hexdigest()
    return ExperimentDataset(id=digest, sha256=digest, source_sha256=digest, raw_json=text, data=parsed)


def parse_csv_metadata(data: bytes) -> dict:
    if not data or len(data) > MAX_CSV_METADATA_BYTES:
        raise ValueError('CSV metadata must be 1 byte to 64 KiB')
    try:
        value = json.loads(data.decode('utf-8').removeprefix('\ufeff'),
                           object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        parsed = CsvMetadata.model_validate(value).model_dump()
        json.dumps(parsed, ensure_ascii=False).encode('utf-8')
        return parsed
    except (ValueError, TypeError, RecursionError) as exc:
        raise ValueError('Invalid CSV metadata JSON') from exc


def parse_csv_experiment(data: bytes, metadata: dict) -> ExperimentDataset:
    if not data or len(data) > MAX_EXPERIMENT_BYTES:
        raise ValueError('Experiment CSV must be 1 byte to 1 MiB')
    try:
        meta = CsvMetadata.model_validate(metadata)
        names = [column.name for column in meta.columns]
        if 'sample_id' in names:
            raise ValueError('sample_id is reserved in CSV')
        text = data.decode('utf-8')
        reader = csv.reader(io.StringIO(text.removeprefix('\ufeff'), newline=''), strict=True)
        if next(reader, None) != ['sample_id', *names]:
            raise ValueError('CSV header must match declared columns in order')
        rows = []
        for cells in reader:
            if len(cells) != len(names) + 1 or len(rows) >= 1000:
                raise ValueError('CSV rows must be rectangular; maximum 1000 rows')
            values = {}
            for name, cell in zip(names, cells[1:]):
                if cell == '':
                    values[name] = None
                else:
                    if re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?', cell) is None:
                        raise ValueError('CSV values must be finite JSON numbers or empty')
                    values[name] = json.loads(cell)
            rows.append({'sample_id': cells[0], 'values': values})
        parsed = ExperimentInput.model_validate(dict(meta.model_dump(), rows=rows))
        envelope = json.dumps({'format': 'csv', 'csv_text': text, 'metadata': meta.model_dump()},
                              sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        encoded = envelope.encode('utf-8')
        if len(encoded) > MAX_EXPERIMENT_ENVELOPE_BYTES:
            raise ValueError('CSV envelope exceeds 2 MiB')
    except (ValueError, TypeError, csv.Error, RecursionError) as exc:
        raise ValueError('Invalid experiment CSV: check metadata, header, rows, finite numeric values and UTF-8') from exc
    digest = hashlib.sha256(encoded).hexdigest()
    return ExperimentDataset(id=digest, sha256=digest, source_sha256=hashlib.sha256(data).hexdigest(),
                             input_format='csv', raw_json=envelope, data=parsed)


def validate_experiments(datasets):
    ids = set()
    for dataset in datasets:
        parsed = parse_experiment(dataset.raw_json.encode('utf-8'))
        if dataset.id != parsed.id or dataset.sha256 != parsed.sha256 or dataset.data != parsed.data:
            raise ValueError('Experiment input/hash binding mismatch')
        if (dataset.input_format != parsed.input_format or
                (dataset.source_sha256 != parsed.source_sha256 and
                 not (parsed.input_format == 'json' and dataset.source_sha256 is None))):
            raise ValueError('Experiment source hash/format binding mismatch')
        if dataset.id in ids:
            raise ValueError('Duplicate experiment dataset')
        ids.add(dataset.id)


def import_csv_experiment(store, run_id, data: bytes, metadata: dict):
    return _import_dataset(store, run_id, parse_csv_experiment(data, metadata))


def import_experiment(store, run_id, data: bytes):
    return _import_dataset(store, run_id, parse_experiment(data))


def _import_dataset(store, run_id, dataset):
    run = store.load(run_id)
    if len(run.experiments) >= 20:
        raise ValueError('Experiment limit is 20 datasets per run')
    if any(item.id == dataset.id for item in run.experiments):
        raise ValueError('This exact experiment input is already imported')
    run.experiments.append(dataset)
    store.save(run)
    return run


def build_experiment_report(run) -> ExperimentReport:
    # Import locally to keep schema/store dependencies acyclic.
    from schemas.research import ResearchRun
    from services.research_validation import validate_run
    run = ResearchRun.model_validate(run.model_dump())
    validate_run(run)
    summaries = []
    for dataset in run.experiments:
        data = dataset.data
        missing = [name for name in ('protocol', 'statistical_method') if getattr(data, name) is None]
        columns = []
        for column in data.columns:
            count = sum(row.values[column.name] is None for row in data.rows)
            columns.append(ColumnCompleteness(name=column.name, unit=column.unit,
                           observed_count=len(data.rows)-count, missing_count=count))
            if column.unit is None:
                missing.append(f'unit:{column.name}')
        summaries.append(DatasetCompleteness(dataset_id=dataset.id, sha256=dataset.sha256,
                         source_sha256=dataset.source_sha256, input_format=dataset.input_format,
                         title=data.title, protocol=data.protocol, statistical_method=data.statistical_method,
                         sample_count=len(data.rows), columns=columns, missing_metadata=missing))
    return ExperimentReport(run_id=run.id, datasets=summaries)
