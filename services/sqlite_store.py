"""Single-host transactional storage with optimistic snapshot revisions."""
import argparse
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import local

from schemas.research import ResearchRun, ResearchRunSummary, ResearchHistory
from services.research_store import ResearchStore
from services.research_validation import validate_run


class ConflictError(ValueError):
    pass


class SQLiteResearchStore(ResearchStore):
    def __init__(self, root):
        super().__init__(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / 'research.sqlite3'
        self._local = local()
        with self.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, data TEXT NOT NULL, updated TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS manuscripts (id TEXT PRIMARY KEY REFERENCES runs(id), data BLOB NOT NULL)')

    @contextmanager
    def transaction(self):
        current = getattr(self._local, 'connection', None)
        if current is not None:
            yield current
            return
        db = sqlite3.connect(self.database, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            self._local.connection = db
            self._local.snapshots = []
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            # A snapshot may contain uncommitted data from either save or load.
            # It must be reloaded, even if a later commit reuses its revision.
            for snapshot in getattr(self._local, 'snapshots', []):
                snapshot._store_revision = -1
            raise
        finally:
            self._local.connection = None
            self._local.snapshots = []
            db.close()

    def save(self, run):
        expected = run._store_revision
        validated = ResearchRun.model_validate(run.model_dump())
        validate_run(validated)
        self._path(validated.id)
        payload = validated.model_dump_json()
        if len(payload.encode('utf-8')) > 64 * 1024 * 1024:
            raise ValueError('Research record exceeds 64 MiB storage limit')
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as db:
            if expected is None:
                try:
                    db.execute('INSERT INTO runs VALUES (?,1,?,?)', (run.id, payload, now))
                except sqlite3.IntegrityError as exc:
                    raise ConflictError('Research record changed; reload before saving') from exc
                revision = 1
            else:
                from services.workspace import validate_append_only
                previous = db.execute('SELECT data FROM runs WHERE id=?', (run.id,)).fetchone()
                if previous is not None:
                    validate_append_only(ResearchRun.model_validate_json(previous['data']), validated)
                cursor = db.execute('UPDATE runs SET revision=revision+1,data=?,updated=? WHERE id=? AND revision=?',
                                    (payload, now, run.id, expected))
                if cursor.rowcount != 1:
                    raise ConflictError('Research record changed; reload before saving')
                revision = expected + 1
            self._local.snapshots.append(run)
            run._store_revision = revision

    def load(self, run_id):
        self._path(run_id)
        with self.transaction() as db:
            row = db.execute('SELECT revision,data FROM runs WHERE id=?', (run_id,)).fetchone()
            if row is None:
                raise FileNotFoundError('Research run not found')
            run = ResearchRun.model_validate_json(row['data'])
            if run.id != run_id:
                raise ValueError('Stored run ID mismatch')
            validate_run(run)
            run._store_revision = row['revision']
            self._local.snapshots.append(run)
        return run

    def history(self, page=1, page_size=10):
        if page < 1 or not 1 <= page_size <= 50:
            raise ValueError('Invalid history pagination')
        with self.transaction() as db:
            total = db.execute('SELECT count(*) FROM runs').fetchone()[0]
            rows = db.execute('SELECT id,updated FROM runs ORDER BY updated DESC,id DESC LIMIT ? OFFSET ?',
                              (page_size, (page - 1) * page_size)).fetchall()
            items = []
            for row in rows:
                run = self.load(row['id'])
                items.append(ResearchRunSummary(id=run.id, topic=run.topic, candidate_count=len(run.candidates),
                    selected_count=len(run.selected_ids), paper_count=len(run.papers),
                    updated_at=datetime.fromisoformat(row['updated']), source_support_passed=run.review.approved))
        return ResearchHistory(items=items, total=total, page=page, page_size=page_size)

    def read_manuscript(self, run_id):
        self._path(run_id)
        with self.transaction() as db:
            row = db.execute('SELECT data FROM manuscripts WHERE id=?', (run_id,)).fetchone()
        return row['data'] if row else None

    def write_manuscript(self, run_id, data):
        self._path(run_id)
        with self.transaction() as db:
            db.execute('INSERT INTO manuscripts VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data', (run_id, data))


def migrate_json(source, target):
    """Explicit all-or-nothing import, including validated manuscript history."""
    from services.manuscript import get_manuscript
    runs = [source.load(p.stem) for p in source.root.glob('*.json') if len(p.stem) == 32]
    manuscripts = {r.id: get_manuscript(source, r.id) for r in runs}
    with target.transaction():
        for run in runs:
            target.save(run)
            if manuscripts[run.id].revisions:
                target.write_manuscript(run.id, manuscripts[run.id].model_dump_json().encode())
    return len(runs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate and import JSON runs into SQLite without overwriting')
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(f'Imported {migrate_json(ResearchStore(args.source), SQLiteResearchStore(args.destination))} records')
