import importlib
import pytest
from workflow.evidence_workflow import EvidenceWorkflow
from services.sqlite_store import SQLiteResearchStore


def manager(tmp_path):
    module = importlib.import_module('services.research_jobs')
    return module.JobManager(SQLiteResearchStore(tmp_path), autostart=False)


def offline(request, baseline, directory):
    from services.research_store import ResearchStore
    flow = EvidenceWorkflow(store=ResearchStore(directory), search=lambda *a, **k: [])
    return flow.search(request['topic'])


def test_jobs_persist_and_commit_only_success(tmp_path):
    m = manager(tmp_path)
    job = m.submit({'kind':'search','topic':'Offline'})
    assert manager(tmp_path).get(job['id'])['status'] == 'queued'
    m.run_once(offline)
    done = m.get(job['id'])
    assert done['status'] == 'succeeded'
    assert m.store.load(done['run_id']).topic == 'Offline'


def test_cancellation_during_execution_never_commits(tmp_path):
    m = manager(tmp_path)
    job = m.submit({'kind':'search','topic':'Cancelled'})
    def cancel(request, baseline, directory):
        m.cancel(job['id'])
        return offline(request, baseline, directory)
    m.run_once(cancel)
    assert m.get(job['id'])['status'] == 'cancelled'
    assert m.store.history().total == 0


def test_stale_analysis_does_not_replace_concurrent_edit(tmp_path):
    m = manager(tmp_path)
    run = EvidenceWorkflow(store=m.store).create('Original')
    # Empty candidates must be rejected, even before scheduling.
    with pytest.raises(ValueError):
        m.submit({'kind':'analyze','run_id':run.id,'selected_ids':['missing']})
    from schemas.research import Candidate, ResearchRun
    run.candidates = [Candidate(id='candidate',title='Synthetic',pdf_url='https://arxiv.org/pdf/2401.00001')]
    m.store.save(run)
    job = m.submit({'kind':'analyze','run_id':run.id,'selected_ids':['candidate']})
    def concurrent_edit(request, baseline, directory):
        latest = m.store.load(run.id)
        latest.topic = 'Concurrent edit'
        m.store.save(latest)
        return ResearchRun.model_validate_json(baseline)
    m.run_once(concurrent_edit)
    assert m.get(job['id'])['status'] == 'failed'
    assert m.store.load(run.id).topic == 'Concurrent edit'


def test_failures_have_bounded_explicit_retry(tmp_path):
    m = manager(tmp_path)
    job = m.submit({'kind':'search','topic':'Failure'})
    def fail(*args):
        raise RuntimeError('secret provider credential')
    for attempt in range(1, 4):
        m.run_once(fail)
        failed = m.get(job['id'])
        assert failed['status'] == 'failed' and 'secret' not in failed['error']
        assert failed['attempt'] == attempt
        if attempt < 3:
            job = m.retry(job['id'])
    with pytest.raises(ValueError):
        m.retry(job['id'])


def test_queue_limit_and_cancel_before_start(tmp_path):
    m = manager(tmp_path)
    jobs = [m.submit({'kind':'search','topic':str(i)}) for i in range(4)]
    with pytest.raises(ValueError):
        m.submit({'kind':'search','topic':'Too many'})
    m.cancel(jobs[0]['id'])
    assert m.get(jobs[0]['id'])['status'] == 'cancelled'
    assert m.submit({'kind':'search','topic':'Slot freed'})['status'] == 'queued'


def test_expired_lease_needs_explicit_retry_and_retry_is_idempotent(tmp_path):
    import time
    m = manager(tmp_path)
    job = m.submit({'kind':'search','topic':'Interrupted'})
    with m.store.transaction() as db:
        db.execute("UPDATE jobs SET status='running',owner='dead',heartbeat=? WHERE id=?", (time.time()-60,job['id']))
    recovered = manager(tmp_path)
    assert recovered.get(job['id'])['status'] == 'interrupted'
    child = recovered.retry(job['id'])
    assert recovered.retry(job['id'])['id'] == child['id']
    recovered.cancel(child['id'])
    with pytest.raises(ValueError, match='previous attempt'):
        recovered.delete(child['id'])
    recovered.delete(job['id'])
    recovered.delete(child['id'])
    assert recovered.list()['items'] == []


def test_supervisor_reads_only_successful_subprocess_result(tmp_path, monkeypatch):
    import subprocess
    import sys
    import services.research_jobs as module
    m = manager(tmp_path)
    job = m.submit({'kind':'search','topic':'Synthetic child'})
    result = offline({'topic':'Synthetic child'},None,tmp_path/'fixture').model_dump_json()
    original = subprocess.Popen
    def spawn(command, **kwargs):
        # A real disposable process, with a synthetic result and no network.
        script = "from pathlib import Path; import sys; Path(sys.argv[1],'result.json').write_text(sys.argv[2],encoding='utf-8')"
        return original([sys.executable,'-c',script,command[-1],result], **kwargs)
    monkeypatch.setattr(module.subprocess, 'Popen', spawn)
    m.run_once()
    assert m.get(job['id'])['status'] == 'succeeded'


def test_supervisor_stops_real_child_without_committing(tmp_path, monkeypatch):
    import subprocess
    import sys
    import services.research_jobs as module
    m = manager(tmp_path)
    job = m.submit({'kind':'search','topic':'Cancelled child'})
    original = subprocess.Popen
    children = []
    def spawn(command, **kwargs):
        if '-m' not in command:
            return original(command, **kwargs)  # Windows taskkill.
        child = original([sys.executable,'-c','import time; time.sleep(60)'], **kwargs)
        children.append(child)
        m.cancel(job['id'])
        return child
    monkeypatch.setattr(module.subprocess, 'Popen', spawn)
    m.run_once()
    assert children[0].poll() is not None
    assert m.get(job['id'])['status'] == 'cancelled'
    assert m.store.history().total == 0
