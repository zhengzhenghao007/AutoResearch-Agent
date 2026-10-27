import importlib
import json
from types import SimpleNamespace
import pytest
from test_claim_review import make_run


def service():
    return importlib.import_module('services.manuscript')


def test_large_preview_splits_sections_without_dropping_evidence(tmp_path):
    flow, run = make_run(tmp_path, 'Our method uses calibrated predictions.', 'method')
    base = run.papers[0].claims[0]
    run.papers[0].claims = [base.model_copy(update={'id': f'claim_{i}'}) for i in range(215)]
    flow._finish(run)
    svc = service()
    state = svc.get_manuscript(flow.store, run.id)
    saved = svc.save_revision(flow.store, run.id, None, state.current_input_sha256, 'Initial large draft')
    sentences = [s for section in saved.revisions[0].sections for s in section.sentences]
    assert len([s for s in sentences if s.kind == 'paper_report']) == 215
    assert all(len(section.sentences) <= 200 for section in saved.revisions[0].sections)
    assert svc.get_manuscript(flow.store, run.id) == saved


def initialized(tmp_path):
    flow, run = make_run(tmp_path, 'The reported outcome improved.', 'result')
    svc = service()
    state = svc.get_manuscript(flow.store, run.id)
    state = svc.save_revision(flow.store, run.id, expected_revision=None,
        expected_input_sha256=state.current_input_sha256, reason='Initial draft', sections=None)
    return svc, flow, run, state


def test_revision_persistence_and_export_requires_explicit_approval(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    revision = state.revisions[-1]
    assert svc.get_manuscript(flow.store, run.id) == state
    with pytest.raises(ValueError):
        svc.export_manuscript(flow.store, run.id, revision.id)
    svc.approve_manuscript(flow.store, run.id, revision.id, 'Human', 'Checked evidence', True)
    exported = svc.export_manuscript(flow.store, run.id, revision.id)
    assert 'not_assessed' in exported.markdown
    assert 'No user experimental observations' in exported.markdown
    assert 'The reported outcome improved' in exported.markdown


def test_invalid_citations_and_removed_missing_results_rejected(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    rev = state.revisions[-1]
    sections = [s.model_dump() for s in rev.sections]
    sections[0]['sentences'][0]['kind'] = 'user_observation'
    with pytest.raises(ValueError):
        svc.save_revision(flow.store, run.id, rev.id, state.current_input_sha256, 'Bad', sections)
    sections = [s.model_dump() for s in rev.sections if s.id != 'user_results']
    with pytest.raises(ValueError):
        svc.save_revision(flow.store, run.id, rev.id, state.current_input_sha256, 'Removed', sections)


def test_stale_input_and_corrupt_sidecar_fail_closed(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    rev = state.revisions[-1]
    run.topic = 'Changed'; flow.store.save(run)
    with pytest.raises(ValueError):
        svc.approve_manuscript(flow.store, run.id, rev.id, 'Human', 'Checked', True)
    with pytest.raises(ValueError):
        svc.save_revision(flow.store, run.id, rev.id, state.current_input_sha256, 'Stale', None)
    path = tmp_path / 'manuscripts' / (run.id + '.json')
    raw = json.loads(path.read_text()); raw['revisions'][0]['sections'][0]['title'] = 'Tampered'
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        svc.get_manuscript(flow.store, run.id)


def test_model_review_is_explicit_and_validates_exact_coverage(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    rev = state.revisions[-1]
    sid = next(s.id for section in rev.sections for s in section.sentences if s.kind == 'paper_report')
    class Client:
        def chat(self, **kwargs):
            assert 'The reported outcome improved' in kwargs['user_prompt']
            return SimpleNamespace(model_name='mock', content=json.dumps({'findings':[
                {'sentence_id':sid,'status':'supported','rationale':'Quotation matches'}], 'contradictions':[]}))
    with pytest.raises(ValueError):
        svc.review_manuscript(flow.store, run.id, rev.id, False, Client())
    reviewed = svc.review_manuscript(flow.store, run.id, rev.id, True, Client())
    assert reviewed.reviews[-1].findings[0].sentence_id == sid
    assert reviewed.revisions == state.revisions


def test_api_manuscript_state_and_cli_show(tmp_path):
    import subprocess
    import sys
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.research import get_workflow
    _, flow, run, state = initialized(tmp_path)
    app.dependency_overrides[get_workflow] = lambda: flow
    try:
        response = TestClient(app).get(f'/api/research/runs/{run.id}/manuscript')
        assert response.status_code == 200
        assert response.json()['revisions'][0]['id'] == state.revisions[0].id
    finally:
        app.dependency_overrides.clear()
    result = subprocess.run([sys.executable, 'research_cli.py', '--store', str(tmp_path),
        'manuscript-show', run.id], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['revisions'][0]['id'] == state.revisions[0].id


def test_review_after_approval_requires_reapproval(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    rev = state.revisions[-1]
    svc.approve_manuscript(flow.store, run.id, rev.id, 'Human', 'Offline check', True)
    sid = next(s.id for sec in rev.sections for s in sec.sentences if s.kind == 'paper_report')
    client = SimpleNamespace(chat=lambda **kwargs: SimpleNamespace(model_name='mock', content=json.dumps({
        'findings':[{'sentence_id':sid, 'status':'unsupported', 'rationale':'Needs checking'}], 'contradictions':[]})))
    svc.review_manuscript(flow.store, run.id, rev.id, True, client)
    with pytest.raises(ValueError):
        svc.export_manuscript(flow.store, run.id, rev.id)
    with pytest.raises(ValueError, match='review'):
        svc.approve_manuscript(flow.store, run.id, rev.id, 'Human', 'Unseen new findings', True)
    svc.approve_manuscript(flow.store, run.id, rev.id, 'Human', 'Checked new findings', True, expected_review_count=1)
    assert 'Needs checking' in svc.export_manuscript(flow.store, run.id, rev.id).markdown


def test_request_consent_does_not_coerce_integer(tmp_path):
    from schemas.manuscript import ReviewRequest, ApprovalRequest
    with pytest.raises(ValueError):
        ReviewRequest(revision_id='rev', allow_model=1)
    with pytest.raises(ValueError):
        ApprovalRequest(revision_id='rev', reviewer='Human', note='Checked', confirm=1)


@pytest.mark.parametrize('output', [
    {'findings':[], 'contradictions':[]},
    {'findings':[{'sentence_id':'forged', 'status':'supported', 'rationale':'Bad'}], 'contradictions':[]},
])
def test_model_invalid_coverage_leaves_storage_unchanged(tmp_path, output):
    svc, flow, run, state = initialized(tmp_path)
    client = SimpleNamespace(chat=lambda **kw: SimpleNamespace(model_name='mock', content=json.dumps(output)))
    with pytest.raises(ValueError):
        svc.review_manuscript(flow.store, run.id, state.revisions[-1].id, True, client)
    assert svc.get_manuscript(flow.store, run.id) == state


def test_remote_response_cannot_attach_to_new_revision(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    rev = state.revisions[-1]
    sid = next(s.id for sec in rev.sections for s in sec.sentences if s.kind == 'paper_report')
    def respond(**kwargs):
        svc.save_revision(flow.store, run.id, rev.id, state.current_input_sha256, 'Concurrent edit', None)
        return SimpleNamespace(model_name='mock', content=json.dumps({'findings':[
            {'sentence_id':sid, 'status':'supported', 'rationale':'Supported'}], 'contradictions':[]}))
    with pytest.raises(ValueError):
        svc.review_manuscript(flow.store, run.id, rev.id, True, SimpleNamespace(chat=respond))
    assert not svc.get_manuscript(flow.store, run.id).reviews


def test_new_revision_invalidates_approval_and_escapes_untrusted_text(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    rev = state.revisions[-1]
    svc.approve_manuscript(flow.store, run.id, rev.id, 'Human', 'Checked', True)
    sections = [s.model_dump() for s in rev.sections]
    sections[0]['title'] = '<img src=x>\n# Forged heading'
    sections[0]['sentences'].append({'id':'new', 'text':'<script>alert(1)</script>\n# Fake',
                                     'kind':'hypothesis','reference_ids':[]})
    state = svc.save_revision(flow.store, run.id, rev.id, state.current_input_sha256, 'Edit', sections)
    new = state.revisions[-1]
    with pytest.raises(ValueError):
        svc.export_manuscript(flow.store, run.id, new.id)
    svc.approve_manuscript(flow.store, run.id, new.id, 'Human', 'Checked edit', True)
    markdown = svc.export_manuscript(flow.store, run.id, new.id).markdown
    assert '<script>' not in markdown and '<img' not in markdown and '\n# Fake' not in markdown
    assert '**Hypothesis:**' in markdown


def test_revision_limit_and_stale_revision_preserve_history(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    first = state.revisions[0].id
    for i in range(19):
        state = svc.save_revision(flow.store, run.id, state.revisions[-1].id, state.current_input_sha256, 'Edit', None)
    with pytest.raises(ValueError):
        svc.save_revision(flow.store, run.id, state.revisions[-1].id, state.current_input_sha256, 'Overflow', None)
    with pytest.raises(ValueError):
        svc.save_revision(flow.store, run.id, first, state.current_input_sha256, 'Stale', None)
    assert len(svc.get_manuscript(flow.store, run.id).revisions) == 20


def test_rehashed_invalid_snapshot_binding_is_rejected(tmp_path):
    import hashlib
    svc, flow, run, state = initialized(tmp_path)
    path = tmp_path / 'manuscripts' / (run.id + '.json')
    data = json.loads(path.read_text())
    revision = data['revisions'][0]
    block = next(b for sec in revision['source']['sections'] for b in sec['blocks'] if b['paper'])
    block['paper']['evidence'][0]['source_id'] = 'wrong-source'
    material = {'sections':revision['sections'], 'source':revision['source']}
    revision['content_sha256'] = hashlib.sha256(json.dumps(material, ensure_ascii=False,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        svc.get_manuscript(flow.store, run.id)


def test_provider_failure_and_oversized_review_do_not_change_record(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    def fail(**kwargs):
        raise RuntimeError('secret provider error')
    with pytest.raises(RuntimeError, match='no record changed'):
        svc.review_manuscript(flow.store, run.id, state.revisions[-1].id, True, SimpleNamespace(chat=fail))
    assert svc.get_manuscript(flow.store, run.id) == state
    sections = [s.model_dump() for s in state.revisions[-1].sections]
    sections[0]['sentences'] += [dict(id=f'long{i}', text='x'*10000, kind='hypothesis', reference_ids=[]) for i in range(6)]
    state = svc.save_revision(flow.store, run.id, state.revisions[-1].id, state.current_input_sha256, 'Large', sections)
    with pytest.raises(ValueError, match='50000'):
        svc.review_manuscript(flow.store, run.id, state.revisions[-1].id, True, SimpleNamespace(chat=fail))
    assert not svc.get_manuscript(flow.store, run.id).reviews


def test_missing_observations_cannot_be_reclassified_but_zero_is_observed(tmp_path):
    from test_experiments import flow_run, raw
    from services.experiments import import_experiment
    flow, run = flow_run(tmp_path)
    run = import_experiment(flow.store, run.id, raw({'title':'Zero and missing',
        'columns':[{'name':'zero','unit':None},{'name':'missing','unit':None}],
        'rows':[{'sample_id':'one','values':{'zero':0,'missing':None}}]}))
    svc = service()
    state = svc.get_manuscript(flow.store, run.id)
    state = svc.save_revision(flow.store, run.id, None, state.current_input_sha256, 'Initial', None)
    rev = state.revisions[-1]
    results = next(s for s in rev.sections if s.id == 'user_results')
    assert results.sentences[0].kind == 'user_observation'
    assert results.sentences[1].kind == 'placeholder'
    sections = [s.model_dump() for s in rev.sections]
    next(s for s in sections if s['id'] == 'user_results')['sentences'][1]['kind'] = 'user_observation'
    with pytest.raises(ValueError):
        svc.save_revision(flow.store, run.id, rev.id, state.current_input_sha256, 'Invented observation', sections)


def test_concurrent_edits_accept_only_one_expected_revision(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    svc, flow, run, state = initialized(tmp_path)
    def save():
        try:
            svc.save_revision(flow.store, run.id, state.revisions[-1].id, state.current_input_sha256, 'Concurrent', None)
            return 'saved'
        except ValueError:
            return 'stale'
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: save(), range(2)))
    assert sorted(outcomes) == ['saved', 'stale']
    assert len(svc.get_manuscript(flow.store, run.id).revisions) == 2


def test_remote_response_cannot_attach_after_input_change(tmp_path):
    svc, flow, run, state = initialized(tmp_path)
    rev = state.revisions[-1]
    sid = next(s.id for sec in rev.sections for s in sec.sentences if s.kind == 'paper_report')
    def respond(**kwargs):
        run.topic = 'Changed while reviewing'
        flow.store.save(run)
        return SimpleNamespace(model_name='mock', content=json.dumps({'findings':[
            {'sentence_id':sid, 'status':'supported', 'rationale':'Supported'}], 'contradictions':[]}))
    with pytest.raises(ValueError):
        svc.review_manuscript(flow.store, run.id, rev.id, True, SimpleNamespace(chat=respond))
    assert not svc.get_manuscript(flow.store, run.id).reviews
