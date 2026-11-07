"""Tenant-local acquisition journal and verified original cache; never rewrites a run."""
import hashlib
import os
import re
import sqlite3
import tempfile
import time
from contextlib import contextmanager
import requests
from services.academic_humanizer import humanize
from schemas.paper_acquisition import AcquisitionOutcome
from services.search_history import search_history
from services.arxiv_identity import canonical_arxiv_pdf_url
from services.paper_processing import PaperProcessor
from services.original_pdf import MAX_BYTES, verify_original

_URL = re.compile(r'https://arxiv\.org/pdf/(?:[0-9]{4}\.[0-9]{4,5}|[a-z-]+(?:\.[A-Z]{2})?/[0-9]{7})(?:v[0-9]+)?(?:\.pdf)?')


@contextmanager
def database(store):
    store.root.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(store.root / 'paper_acquisitions.sqlite3', timeout=15) as db:
        db.execute('CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, created REAL NOT NULL, data TEXT NOT NULL)')
        yield db


def history(store, run_id):
    store.load(run_id)
    with database(store) as db:
        rows = db.execute('SELECT data FROM attempts WHERE run_id=? ORDER BY created DESC LIMIT 500', (run_id,)).fetchall()
    return [AcquisitionOutcome.model_validate_json(row[0]) for row in rows]


def _record(store, item, *, new=False):
    with database(store) as db:
        if new:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT COUNT(*) FROM attempts WHERE run_id=?', (item.run_id,)).fetchone()[0] >= 500:
                raise ValueError('Acquisition attempt budget exhausted (500 per project)')
            db.execute('INSERT INTO attempts VALUES(?,?,?,?)', (item.id, item.run_id, time.time(), item.model_dump_json()))
        else:
            db.execute('UPDATE attempts SET data=? WHERE id=? AND run_id=?', (item.model_dump_json(), item.id, item.run_id))


def _path(store, digest):
    if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('Invalid cached PDF identity')
    return store.root / 'acquired_originals' / (digest + '.pdf')


def _read(store, digest):
    path = _path(store, digest)
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    verify_original(path, data)
    return data


def _save(store, data):
    digest = hashlib.sha256(data).hexdigest()
    path = _path(store, digest)
    verify_original(path, data)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            name = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)
    return digest


def _reserve_download(store, now):
    # Shared across concurrent runs in this store, including separate API workers.
    with database(store) as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS download_clock(id INTEGER PRIMARY KEY, next_at REAL NOT NULL)')
        row = db.execute('SELECT next_at FROM download_clock WHERE id=1').fetchone()
        start = max(now, row[0]) if row else now
        if start - now > 15:
            raise ValueError('Download queue is full; retry this selection later')
        db.execute('INSERT OR REPLACE INTO download_clock VALUES(1,?)', (start + 3,))
        return start - now


def download(url, transport=None):
    if not _URL.fullmatch(url):
        raise ValueError('Only canonical HTTPS arXiv PDFs are supported')
    started = time.monotonic()
    with (transport or requests.get)(url, timeout=(5, 15), stream=True, allow_redirects=False) as response:
        if response.status_code != 200:
            raise ValueError('PDF download failed or redirect was rejected')
        if int(response.headers.get('Content-Length', '0')) > MAX_BYTES:
            raise ValueError('PDF exceeds size limit')
        data = bytearray()
        for chunk in response.iter_content(65536):
            if time.monotonic() - started > 30 or len(data) + len(chunk) > MAX_BYTES:
                raise ValueError('PDF exceeds download size or time limit')
            data.extend(chunk)
    if not data.startswith(b'%PDF-'):
        raise ValueError('Expected PDF content')
    return bytes(data)


def acquire(store, run_id, request, *, transport=None, processor=None):
    batches = {batch.id: batch for batch in search_history(store, run_id)}
    selected = []
    for selection in request.selections:
        batch = batches.get(selection.batch_id)
        hits = [] if batch is None else [hit for source in batch.sources for hit in source.hits
                if hit.source == selection.source and hit.source_id == selection.source_id]
        if len(hits) != 1:
            raise ValueError('Selection must identify exactly one saved hit in this project')
        selected.append((selection, hits[0]))
    prior = history(store, run_id)
    result = []
    processor = processor or PaperProcessor(max_pages=50, max_bytes=MAX_BYTES)
    for selection, hit in selected:
        item = AcquisitionOutcome(scope=humanize(AcquisitionOutcome.model_fields['scope'].default), run_id=run_id, selection=selection, metadata=hit)
        _record(store, item, new=True)  # An interrupted pending attempt is retained; resubmit to retry.
        item.url = canonical_arxiv_pdf_url(hit.pdf_url)
        if not _URL.fullmatch(item.url):
            item.status, item.error = 'unsupported', 'No supported canonical arXiv PDF URL in this saved hit'
        else:
            try:
                cached = next((old for old in prior if old.url == item.url and old.status in ('downloaded', 'cached')), None)
                if cached:
                    try:
                        _read(store, cached.sha256)
                        item.sha256, item.status = cached.sha256, 'cached'
                    except (OSError, ValueError):
                        cached = None
                if not cached:
                    if transport is None:
                        time.sleep(_reserve_download(store, time.time()))
                    data = download(item.url, transport)
                    processor.parse_bytes(data, hit.title, item.url)
                    item.sha256, item.status = _save(store, data), 'downloaded'
            except (requests.RequestException, ValueError, OSError):
                item.status, item.error = 'failed', 'PDF unavailable, invalid, or exceeded processing limits; resubmit this selection to retry'
        _record(store, item)
        prior.insert(0, item)
        result.append(item)
    return result


def import_acquired(flow, run_id, acquisition_id):
    # Existing import loads fresh state under its mutation lock and saves original bytes.
    item = next((x for x in history(flow.store, run_id) if x.id == acquisition_id), None)
    if item is None:
        raise FileNotFoundError('Acquisition not found in this project')
    if item.status not in ('downloaded', 'cached'):
        raise ValueError('Acquire a valid PDF before importing')
    if getattr(flow.extractor, 'mode', 'rule') != 'rule':
        raise ValueError('Acquisition import requires deterministic extraction')
    return flow.import_pdf(_read(flow.store, item.sha256), item.metadata.title, run_id=run_id)
