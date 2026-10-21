import importlib
import pytest
from workflow.evidence_workflow import EvidenceWorkflow
from services.manuscript import get_manuscript, save_revision, approve_manuscript, export_manuscript


def store(path):
    return importlib.import_module('services.sqlite_store').SQLiteResearchStore(path)


def test_independent_stores_cannot_overwrite_stale_snapshot(tmp_path):
    a, b = store(tmp_path), store(tmp_path)
    run = EvidenceWorkflow(store=a).create('Original')
    first, stale = a.load(run.id), b.load(run.id)
    first.topic = 'First edit'; a.save(first)
    stale.topic = 'Stale edit'
    with pytest.raises(ValueError, match='changed'):
        b.save(stale)
    assert b.load(run.id).topic == 'First edit'
    assert b.history().total == 1


def test_transaction_rolls_back_run_and_manuscript(tmp_path):
    s = store(tmp_path)
    run = EvidenceWorkflow(store=s).create('Original')
    with pytest.raises(RuntimeError):
        with s.transaction():
            current = s.load(run.id); current.topic = 'Uncommitted'; s.save(current)
            state = get_manuscript(s, run.id)
            save_revision(s, run.id, None, state.current_input_sha256, 'Draft')
            raise RuntimeError('Rollback')
    assert s.load(run.id).topic == 'Original'
    assert not get_manuscript(s, run.id).revisions


def test_sqlite_manuscript_approval_invalidated_by_source_change(tmp_path):
    a, b = store(tmp_path), store(tmp_path)
    run = EvidenceWorkflow(store=a).create('Original')
    state = get_manuscript(a, run.id)
    state = save_revision(a, run.id, None, state.current_input_sha256, 'Draft')
    revision = state.revisions[-1]
    approve_manuscript(a, run.id, revision.id, 'Synthetic', 'Test only', True)
    assert export_manuscript(b, run.id, revision.id).revision_id == revision.id
    changed = b.load(run.id); changed.topic = 'Changed'; b.save(changed)
    with pytest.raises(ValueError):
        export_manuscript(a, run.id, revision.id)


def test_migration_is_atomic_and_never_overwrites(tmp_path):
    from services.research_store import ResearchStore
    from services.sqlite_store import migrate_json
    source = ResearchStore(tmp_path / 'old')
    run = EvidenceWorkflow(store=source).create('Legacy')
    draft = get_manuscript(source, run.id)
    save_revision(source, run.id, None, draft.current_input_sha256, 'Legacy draft')
    target = store(tmp_path / 'new')
    assert migrate_json(source, target) == 1
    assert target.load(run.id).topic == 'Legacy'
    assert get_manuscript(target, run.id).revisions[0].reason == 'Legacy draft'
    with pytest.raises(ValueError):
        migrate_json(source, target)


def test_rolled_back_snapshots_cannot_reuse_a_later_committed_revision(tmp_path):
    a,b=store(tmp_path),store(tmp_path)
    run=EvidenceWorkflow(store=a).create('Original')
    with pytest.raises(RuntimeError):
        with a.transaction():
            changed=a.load(run.id)
            changed.topic='Rolled back'
            a.save(changed)
            loaded_uncommitted=a.load(run.id)
            raise RuntimeError('Rollback')
    other=b.load(run.id)
    other.topic='Committed other writer'
    b.save(other)
    for invalid in (changed,loaded_uncommitted):
        with pytest.raises(ValueError,match='changed'):
            a.save(invalid)
    assert b.load(run.id).topic=='Committed other writer'


def test_two_processes_cannot_silently_overwrite(tmp_path):
    import subprocess
    import sys
    import time
    database=tmp_path/'db'
    run=EvidenceWorkflow(store=store(database)).create('Original')
    script="""
import sys,time
from pathlib import Path
from services.sqlite_store import SQLiteResearchStore,ConflictError
s=SQLiteResearchStore(sys.argv[1]);r=s.load(sys.argv[2]);r.topic=sys.argv[3]
Path(sys.argv[4]).touch()
deadline=time.monotonic()+10
while not Path(sys.argv[5]).exists():
    if time.monotonic()>deadline: raise RuntimeError('gate timeout')
    time.sleep(.01)
try:
    s.save(r); print('saved')
except ConflictError:
    print('conflict')
"""
    gate=tmp_path/'go'
    processes=[]
    try:
        for i in range(2):
            processes.append(subprocess.Popen([sys.executable,'-c',script,str(database),run.id,f'Writer {i}',str(tmp_path/f'ready{i}'),str(gate)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
        deadline=time.monotonic()+10
        while not all((tmp_path/f'ready{i}').exists() for i in range(2)):
            assert time.monotonic()<deadline
            time.sleep(.01)
        gate.touch()
        output=[p.communicate(timeout=10) for p in processes]
        assert all(p.returncode==0 for p in processes),output
        assert sorted(out.strip() for out,err in output)==['conflict','saved']
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill();process.wait(timeout=5)
