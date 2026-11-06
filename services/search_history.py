"""Append-only search history scoped to the research store and run."""
import sqlite3
import time
from contextlib import contextmanager
from services.multi_source_search import multi_search
from schemas.multi_source_search import SearchBatch


@contextmanager
def database(store):
    store.root.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(store.root / 'metadata_searches.sqlite3', timeout=15) as db:
        db.execute('CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, created REAL NOT NULL, data TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS source_limits(source TEXT PRIMARY KEY, next_request REAL NOT NULL)')
        yield db


def search_and_save(store, run_id, request, search=multi_search):
    store.load(run_id)
    batch = SearchBatch(run_id=run_id, request=request, sources=[], groups=[],
                        scope='Search started. If interrupted, run a new search after the cooldown.')
    with database(store) as db:
        db.execute('BEGIN IMMEDIATE')
        count = db.execute('SELECT COUNT(*) FROM batches WHERE run_id=?', (run_id,)).fetchone()[0]
        if count >= 100:
            raise ValueError('This project has reached its 100 saved search batches limit')
        now = time.time()
        for source in request.sources:
            row = db.execute('SELECT next_request FROM source_limits WHERE source=?', (source,)).fetchone()
            if row and row[0] > now:
                raise ValueError('Search cooldown active. Wait 30 seconds before searching this source again.')
        for source in request.sources:
            db.execute('INSERT OR REPLACE INTO source_limits VALUES(?,?)', (source, now+30))
        db.execute('INSERT INTO batches VALUES(?,?,?,?)', (batch.id, run_id, now, batch.model_dump_json()))
    result = search(run_id, request)
    result.id = batch.id
    result.created_at = batch.created_at
    with database(store) as db:
        for outcome in result.sources:
            if outcome.retry_after_seconds:
                db.execute('UPDATE source_limits SET next_request=MAX(next_request,?) WHERE source=?',
                           (time.time()+outcome.retry_after_seconds, outcome.source))
        db.execute('UPDATE batches SET data=? WHERE id=? AND run_id=?', (result.model_dump_json(), batch.id, run_id))
    return result


def search_history(store, run_id):
    store.load(run_id)
    with database(store) as db:
        rows = db.execute('SELECT data FROM batches WHERE run_id=? ORDER BY created DESC LIMIT 100', (run_id,)).fetchall()
    return [SearchBatch.model_validate_json(row[0]) for row in rows]
