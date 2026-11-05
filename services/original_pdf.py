"""Store an uploaded original beside its research record, keyed by content hash."""
import hashlib
import os
import tempfile

MAX_BYTES = 20 * 1024 * 1024


def original_path(store, run, source_id):
    source = next((p.document.source for p in run.papers
                   if p.document.source.id == source_id and p.document.source.uri.startswith('upload:')), None)
    if source is None:
        raise FileNotFoundError('Uploaded paper not found')
    return store.root / 'originals' / run.id / (source.sha256 + '.pdf')


def verify_original(path, data):
    if len(data) > MAX_BYTES or not data.startswith(b'%PDF-') or hashlib.sha256(data).hexdigest() != path.stem:
        raise ValueError('The PDF does not match the original file imported for this paper')


def save_original(store, run, source_id, data):
    path = original_path(store, run, source_id)
    verify_original(path, data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary_path = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def read_original(store, run, source_id):
    path = original_path(store, run, source_id)
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    verify_original(path, data)
    return data
