"""Persistent bounded jobs. Only the supervisor may commit staged results."""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from schemas.research import ResearchRun
from schemas.research_jobs import JobRequest
from services.sqlite_store import SQLiteResearchStore

_slots = threading.BoundedSemaphore(2)
_managers, _managers_lock = {}, threading.Lock()
ACTIVE = ('queued','running','cancel_requested')
TERMINAL = ('succeeded','failed','cancelled','interrupted')


def _stamp(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


class JobManager:
    def __init__(self, store, autostart=True):
        if not isinstance(store, SQLiteResearchStore):
            raise ValueError('Background jobs require SQLite storage')
        self.store, self.stop = store, threading.Event()
        with store.transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, request TEXT NOT NULL, baseline TEXT, revision INTEGER,
                status TEXT NOT NULL, attempt INTEGER NOT NULL, child_id TEXT,
                created REAL NOT NULL, updated REAL NOT NULL, heartbeat REAL,
                owner TEXT, result_id TEXT, error TEXT)''')
        self.thread = None
        if autostart:
            self.thread = threading.Thread(target=self._loop, daemon=True, name='research-jobs')
            self.thread.start()

    def _loop(self):
        while not self.stop.is_set():
            try:
                self.run_once()
            except Exception:
                # DB failure leaves the lease to expire; never report success.
                pass
            self.stop.wait(1)

    def _recover(self, db):
        db.execute("UPDATE jobs SET status='interrupted',error='Worker interrupted; explicit retry required',updated=? WHERE status IN ('running','cancel_requested') AND heartbeat<?",
                   (time.time(), time.time() - 30))

    def _row(self, db, identity):
        if not re.fullmatch(r'[a-f0-9]{32}', identity):
            raise ValueError('Invalid job ID')
        row = db.execute('SELECT * FROM jobs WHERE id=?', (identity,)).fetchone()
        if row is None:
            raise FileNotFoundError('Job not found')
        return row

    def _public(self, row):
        request = json.loads(row['request'])
        return {'id':row['id'], 'kind':request['kind'], 'status':row['status'], 'attempt':row['attempt'],
                'run_id':row['result_id'] or request.get('run_id'), 'error':row['error'],
                'created_at':_stamp(row['created']), 'updated_at':_stamp(row['updated']),
                'progress':{'queued':'Waiting for a worker', 'running':'Processing selected operation',
                            'cancel_requested':'Stopping operation', 'succeeded':'Result committed',
                            'failed':'No result committed', 'cancelled':'No result committed',
                            'interrupted':'Worker interrupted'}[row['status']]}

    def get(self, identity):
        with self.store.transaction() as db:
            self._recover(db)
            return self._public(self._row(db, identity))

    def list(self):
        with self.store.transaction() as db:
            self._recover(db)
            return {'items':[self._public(row) for row in db.execute('SELECT * FROM jobs ORDER BY created DESC,id DESC')]}

    def submit(self, value, attempt=1):
        request = JobRequest.model_validate(value)
        with self.store.transaction() as db:
            self._recover(db)
            if db.execute('SELECT count(*) FROM jobs').fetchone()[0] >= 200:
                raise ValueError('Job history limit reached; remove finished jobs')
            if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running','cancel_requested')").fetchone()[0] >= 4:
                raise ValueError('Job queue capacity reached (4 per user)')
            baseline, revision = None, None
            if request.kind == 'analyze':
                run = self.store.load(request.run_id)
                if not set(request.selected_ids) <= {c.id for c in run.candidates}:
                    raise ValueError('Unknown selected candidates')
                baseline, revision = run.model_dump_json(), run._store_revision
            identity, now = uuid4().hex, time.time()
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (identity, request.model_dump_json(), baseline, revision, 'queued', attempt, None,
                        now, now, None, None, None, None))
            return self._public(self._row(db, identity))

    def cancel(self, identity):
        with self.store.transaction() as db:
            row = self._row(db, identity)
            if row['status'] in ('queued','running'):
                status = 'cancelled' if row['status'] == 'queued' else 'cancel_requested'
                db.execute('UPDATE jobs SET status=?,updated=? WHERE id=?', (status, time.time(), identity))
            return self._public(self._row(db, identity))

    def retry(self, identity):
        with self.store.transaction() as db:
            self._recover(db)
            row = self._row(db, identity)
            if row['child_id']:
                return self._public(self._row(db, row['child_id']))
            if row['status'] not in ('failed','cancelled','interrupted') or row['attempt'] >= 3:
                raise ValueError('Only unsuccessful jobs below three attempts can be retried')
            child = self.submit(json.loads(row['request']), row['attempt'] + 1)
            db.execute('UPDATE jobs SET child_id=? WHERE id=?', (child['id'], identity))
            return child

    def delete(self, identity):
        with self.store.transaction() as db:
            if self._row(db, identity)['status'] not in TERMINAL:
                raise ValueError('Cancel an active job before removing it')
            if db.execute('SELECT 1 FROM jobs WHERE child_id=?', (identity,)).fetchone():
                raise ValueError('Remove the previous attempt first')
            db.execute('DELETE FROM jobs WHERE id=?', (identity,))

    def _alive(self, identity, owner):
        with self.store.transaction() as db:
            row = self._row(db, identity)
            if row['status'] != 'running' or row['owner'] != owner:
                return False
            db.execute('UPDATE jobs SET heartbeat=?,updated=? WHERE id=?', (time.time(), time.time(), identity))
            return True

    @staticmethod
    def _terminate(process):
        if process.poll() is not None:
            return
        if sys.platform == 'win32':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'], capture_output=True,
                           timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=10)

    def _process(self, request, baseline, directory, identity, owner):
        (directory / 'input.json').write_text(json.dumps({'request':request,'baseline':baseline}), encoding='utf-8')
        options = {'creationflags':subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == 'win32' else {'start_new_session':True}
        process = subprocess.Popen([sys.executable,'-m','services.job_worker',str(directory)],
                                   cwd=Path(__file__).resolve().parents[1],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)
        deadline = time.monotonic() + 300
        try:
            while process.poll() is None:
                if self.stop.is_set() or time.monotonic() > deadline or not self._alive(identity, owner):
                    raise RuntimeError('Operation stopped')
                time.sleep(.25)
            if process.returncode:
                raise RuntimeError('Worker failed')
            with (directory / 'result.json').open('rb') as stream:
                data = stream.read(64 * 1024 * 1024 + 1)
            if len(data) > 64 * 1024 * 1024:
                raise ValueError('Job result too large')
            return ResearchRun.model_validate_json(data)
        finally:
            self._terminate(process)

    def run_once(self, runner=None):
        if not _slots.acquire(blocking=False):
            return False
        identity = owner = None
        try:
            with self.store.transaction() as db:
                self._recover(db)
                row = db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created,id LIMIT 1").fetchone()
                if row is None:
                    return False
                identity, owner = row['id'], uuid4().hex
                db.execute("UPDATE jobs SET status='running',owner=?,heartbeat=?,updated=? WHERE id=?",
                           (owner, time.time(), time.time(), identity))
            request = json.loads(row['request'])
            with tempfile.TemporaryDirectory(prefix='research-job-') as stage:
                directory = Path(stage)
                result = (runner(request, row['baseline'], directory) if runner
                          else self._process(request, row['baseline'], directory, identity, owner))
            with self.store.transaction() as db:
                current = self._row(db, identity)
                if current['status'] == 'cancel_requested':
                    db.execute("UPDATE jobs SET status='cancelled',updated=? WHERE id=?", (time.time(), identity))
                    return True
                if current['status'] != 'running' or current['owner'] != owner:
                    return True
                result._store_revision = row['revision']
                if request['kind'] == 'analyze' and result.id != request['run_id']:
                    raise ValueError('Result identity mismatch')
                self.store.save(result)
                db.execute("UPDATE jobs SET status='succeeded',result_id=?,updated=? WHERE id=?",
                           (result.id, time.time(), identity))
            return True
        except Exception:
            if identity:
                with self.store.transaction() as db:
                    current = self._row(db, identity)
                    if current['owner'] == owner and current['status'] in ('running','cancel_requested'):
                        status = 'cancelled' if current['status'] == 'cancel_requested' else 'failed'
                        db.execute('UPDATE jobs SET status=?,error=?,updated=? WHERE id=?',
                                   (status, 'Operation did not commit; check sources or refresh the record before retrying.',
                                    time.time(), identity))
            return True
        finally:
            _slots.release()


def manager_for(store):
    if not isinstance(store, SQLiteResearchStore):
        raise ValueError('Background jobs require AUTORESEARCH_STORAGE=sqlite')
    key = str(store.database.resolve())
    with _managers_lock:
        if key not in _managers:
            _managers[key] = JobManager(store)
        return _managers[key]


def start_managers(config):
    """Recover queued work on API startup, without needing a browser request."""
    if not config.sqlite:
        return []
    users = config.users if config.deployment else {'local': None}
    return [manager_for(SQLiteResearchStore(config.root / 'users' / name)) for name in users]


def stop_managers(managers):
    for manager in managers:
        manager.stop.set()
    for manager in managers:
        if manager.thread:
            manager.thread.join(timeout=12)
    with _managers_lock:
        for manager in managers:
            key = str(manager.store.database.resolve())
            if _managers.get(key) is manager:
                del _managers[key]
