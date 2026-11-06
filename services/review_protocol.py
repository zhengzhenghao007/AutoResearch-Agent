"""Versioned review protocol snapshots with optimistic concurrency."""
import sqlite3
from contextlib import contextmanager
from schemas.review_protocol import ReviewProtocol, ReviewProtocolState
from services.sqlite_store import ConflictError

@contextmanager
def database(store):
    store.root.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(store.root / 'review_protocols.sqlite3', timeout=15) as db:
        db.execute('CREATE TABLE IF NOT EXISTS protocols(run_id TEXT NOT NULL, revision INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(run_id,revision))')
        yield db


def get_protocol(store, run_id):
    store.load(run_id)
    with database(store) as db:
        rows = db.execute('SELECT data FROM protocols WHERE run_id=? ORDER BY revision', (run_id,)).fetchall()
    return ReviewProtocolState(run_id=run_id, revisions=[ReviewProtocol.model_validate_json(row[0]) for row in rows])


def save_protocol(store, run_id, request):
    store.load(run_id)
    with database(store) as db:
        db.execute('BEGIN IMMEDIATE')
        revision = db.execute('SELECT COALESCE(MAX(revision),0) FROM protocols WHERE run_id=?', (run_id,)).fetchone()[0]
        if revision != request.expected_revision:
            raise ConflictError('Review protocol changed. Reload it before saving your edits.')
        if revision >= 50:
            raise ValueError('Review protocol has reached the 50 revision limit')
        protocol = ReviewProtocol(revision=revision+1, **request.model_dump(exclude={'expected_revision'}))
        db.execute('INSERT INTO protocols VALUES(?,?,?)', (run_id, protocol.revision, protocol.model_dump_json()))
    return protocol
