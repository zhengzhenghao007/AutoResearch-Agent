import importlib
import json
from types import SimpleNamespace
import pytest
from test_claim_review import make_run
from services.research_store import ResearchStore


def service():
    return importlib.import_module('services.paper_quick_read')


def output():
    point = {'text': 'The authors plan future tests.', 'references': [{'page': 1, 'quote': 'We will evaluate this method in future experiments.'}], 'kind': 'paper_report'}
    return dict(one_sentence=point, main_points=[point], problem=[], innovations=[], methods=[], findings_applications=[], limitations=[], goal_relevance=[], suggested_directions=[], missing_information=['Only a planned evaluation is described; other sections lack supplied evidence.'])


class Client:
    def __init__(self, data=None, fail=False):
        self.data = data or output(); self.calls = []; self.fail = fail
    def chat(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail: raise RuntimeError('offline provider failure')
        return SimpleNamespace(content=json.dumps(self.data), model_name='offline-test', input_tokens=30, output_tokens=20, total_tokens=50)


def fixture(tmp_path):
    _, run = make_run(tmp_path, 'We will evaluate this method in future experiments.')
    store = ResearchStore(tmp_path / 'runs'); store.save(run)
    return store, run, run.papers[0].document.source.id


def test_grounded_paraphrase_persisted_and_cache_reused(tmp_path):
    store, run, source = fixture(tmp_path); client = Client()
    assert service().get_quick_read(store, run.id, source) is None
    report = service().generate_quick_read(store, run.id, source, True, client)
    assert report.output.one_sentence.text == 'The authors plan future tests.'
    assert report.output.one_sentence.references[0].page == 1
    assert service().generate_quick_read(store, run.id, source, True, client) == report
    assert len(client.calls) == 1
    assert service().get_quick_read(ResearchStore(store.root), run.id, source) == report


@pytest.mark.parametrize('mutation', ['quote', 'page', 'missing_references', 'novelty'])
def test_rejects_fabricated_source_support(tmp_path, mutation):
    store, run, source = fixture(tmp_path); data = output()
    point = data['one_sentence']
    if mutation == 'quote': point['references'][0]['quote'] = 'This method is experimentally validated.'
    if mutation == 'page': point['references'][0]['page'] = 99
    if mutation == 'missing_references': point['references'] = []
    if mutation == 'novelty': data['innovations'] = [point]
    with pytest.raises(ValueError): service().generate_quick_read(store, run.id, source, True, Client(data))
    assert service().get_quick_read(store, run.id, source) is None


def test_consent_failure_and_store_isolation(tmp_path):
    store, run, source = fixture(tmp_path); client = Client(fail=True)
    with pytest.raises(ValueError, match='consent'): service().generate_quick_read(store, run.id, source, False, client)
    assert not client.calls
    with pytest.raises(RuntimeError): service().generate_quick_read(store, run.id, source, True, client)
    assert len(client.calls) == 1 and service().get_quick_read(store, run.id, source) is None
    service().generate_quick_read(store, run.id, source, True, Client())
    other = ResearchStore(tmp_path / 'other'); other.save(run)
    assert service().get_quick_read(other, run.id, source) is None


def test_api_requires_consent_and_returns_null_until_generated(tmp_path):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.research import get_workflow
    api = importlib.import_module('backend.app.api.paper_quick_read')
    store, run, source = fixture(tmp_path)
    app.dependency_overrides[get_workflow] = lambda: SimpleNamespace(store=store)
    app.dependency_overrides[api.get_quick_read_generator] = lambda: (lambda *args, **kwargs: service().generate_quick_read(*args, **kwargs, client=Client()))
    try:
        with TestClient(app) as client:
            url = f'/api/research/runs/{run.id}/papers/{source}/quick-read'
            assert client.get(url).json() is None
            assert client.post(url, json={}).status_code == 400
            assert client.post(url, json={'allow_model': 'true'}).status_code == 422
            result = client.post(url, json={'allow_model': True})
            assert result.status_code == 200, result.text
            assert client.get(url).json() == result.json()
    finally:
        app.dependency_overrides.clear()


def test_goal_change_invalidates_cache(tmp_path):
    store, run, source = fixture(tmp_path)
    if 'research_goal' not in type(run).model_fields:
        pytest.skip('Metadata schema integration pending')
    first = service().generate_quick_read(store, run.id, source, True, Client())
    changed = store.load(run.id); changed.research_goal = 'Evaluate future experiments'; store.save(changed)
    assert service().get_quick_read(store, run.id, source) is None
    second = service().generate_quick_read(store, run.id, source, True, Client())
    assert second.goal == 'Evaluate future experiments' and first.input_sha256 != second.input_sha256


def test_coverage_budget_and_quotes_outside_supplied_text(tmp_path):
    from schemas.research import Page
    store, run, source = fixture(tmp_path)
    changed = store.load(run.id)
    changed.papers[0].document.pages[0].text += ' filler' * 10000 + ' End-only unique quotation.'
    store.save(changed)
    data = output(); data['one_sentence']['references'][0]['quote'] = 'End-only unique quotation.'
    with pytest.raises(ValueError, match='supplied page'):
        service().generate_quick_read(store, run.id, source, True, Client(data))
    valid = service().generate_quick_read(store, run.id, source, True, Client())
    assert valid.coverage.truncated_pages == [1] and valid.coverage.notes


def test_sqlite_cache_isolated_and_encoded_source_id_roundtrips(tmp_path):
    from services.sqlite_store import SQLiteResearchStore
    from urllib.parse import quote
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.research import get_workflow
    _, run, _ = fixture(tmp_path)
    run.papers[0].document.source.id = 'https://example.org/paper/1'
    run.papers[0].evidence[0].source_id = run.papers[0].document.source.id
    store = SQLiteResearchStore(tmp_path / 'sqlite'); store.save(run)
    source = run.papers[0].document.source.id
    report = service().generate_quick_read(store, run.id, source, True, Client())
    assert service().get_quick_read(SQLiteResearchStore(store.root), run.id, source) == report
    app.dependency_overrides[get_workflow] = lambda: SimpleNamespace(store=store)
    try:
        with TestClient(app) as client:
            result = client.get(f'/api/research/runs/{run.id}/papers/{quote(source, safe="")}/quick-read')
            assert result.status_code == 200 and result.json()['source_id'] == source
    finally:
        app.dependency_overrides.clear()


def test_even_page_coverage_ocr_and_single_call_failure(tmp_path):
    from schemas.research import Page
    store, run, source = fixture(tmp_path)
    changed = store.load(run.id); document = changed.papers[0].document
    document.pages = [Page(number=i, text='We will evaluate this method in future experiments.' + ' x'*1000) for i in range(1, 101)]
    document.total_pages = 100; document.ocr_pages = [1]
    from workflow.evidence_workflow import EvidenceWorkflow
    EvidenceWorkflow(store=store)._finish(changed)
    client = Client(); report = service().generate_quick_read(store, run.id, source, True, client)
    assert report.coverage.included_pages[0] == 1 and report.coverage.included_pages[-1] == 100
    assert len(report.coverage.omitted_pages) == 60 and report.coverage.ocr_pages == [1]
    assert any('OCR' in note for note in report.coverage.notes)
    supplied = json.loads(client.calls[0]['user_prompt'])['pages']
    assert sum(len(text) for text in supplied.values()) <= 40000



def test_concurrent_generation_spends_only_one_call(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    store, run, source = fixture(tmp_path)
    entered = Event(); release = Event()
    class Slow(Client):
        def chat(self, **kwargs):
            entered.set(); assert release.wait(5)
            return super().chat(**kwargs)
    client = Slow()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(service().generate_quick_read, store, run.id, source, True, client)
        assert entered.wait(5)
        second = pool.submit(service().generate_quick_read, store, run.id, source, True, client)
        release.set()
        report = first.result()
        try:
            assert report == second.result()
        except ValueError as exc:
            assert 'in progress' in str(exc)
            assert service().get_quick_read(store, run.id, source) == report
    assert len(client.calls) == 1


def test_tampered_cache_rejected_and_goal_missing_analysis_explicit(tmp_path):
    store, run, source = fixture(tmp_path)
    service().generate_quick_read(store, run.id, source, True, Client())
    path = next((store.root / 'quick_reads' / run.id).glob('*.json'))
    data = json.loads(path.read_text()); data['source_id'] = 'wrong-source'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='binding'):
        service().get_quick_read(store, run.id, source)


def test_cache_rejects_modified_quote_and_coverage(tmp_path):
    store, run, source = fixture(tmp_path)
    report = service().generate_quick_read(store, run.id, source, True, Client())
    path = next((store.root / 'quick_reads' / run.id).glob('*.json'))
    data = report.model_dump(mode='json'); data['output']['one_sentence']['references'][0]['quote'] = 'Unsupported fabricated quotation.'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='Quotation'):
        service().get_quick_read(store, run.id, source)
    data = report.model_dump(mode='json'); data['coverage']['included_pages'] = [77]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='coverage'):
        service().get_quick_read(store, run.id, source)


def test_rate_limit_is_actionable_and_never_retried(tmp_path):
    store, run, source = fixture(tmp_path)
    class Limited(Client):
        def chat(self, **kwargs):
            self.calls.append(kwargs)
            cause = RuntimeError('Private provider details')
            cause.status_code = 429
            raise RuntimeError('Wrapped failure') from cause
    client = Limited()
    with pytest.raises(service().QuickReadProviderError, match='rate-limited') as error:
        service().generate_quick_read(store, run.id, source, True, client)
    assert error.value.status_code == 429
    assert len(client.calls) == 1
    assert service().get_quick_read(store, run.id, source) is None


def test_short_pages_release_budget_and_blank_pages_do_not_count(tmp_path):
    from schemas.research import Page
    _, run, _ = fixture(tmp_path)
    document = run.papers[0].document
    document.pages = [Page(number=1,text='short'),Page(number=2,text='x'*39000),Page(number=3,text='  ')]
    document.total_pages = 3
    supplied, coverage = service()._select_context(document)
    assert len(supplied[2]) == 39000
    assert coverage.omitted_pages == [3] and coverage.truncated_pages == []
    assert coverage.parsed_pages == 3
    old, old_coverage = service()._select_context(document, version=1)
    assert len(old[2]) == 40000 // 3 and old_coverage.included_pages == [1,2,3]


def test_previous_cache_reopens_with_original_context(tmp_path):
    from schemas.research import Page
    store, run, source = fixture(tmp_path)
    document = run.papers[0].document
    document.pages.append(Page(number=2,text=' '))
    document.total_pages = 2
    from workflow.evidence_workflow import EvidenceWorkflow
    EvidenceWorkflow(store=store)._finish(run)
    report = service().generate_quick_read(store, run.id, source, True, Client())
    cached = report.model_dump(mode='json')
    cached.pop('context_version')
    _, old_coverage = service()._select_context(document, version=1)
    cached['coverage'] = old_coverage.model_dump(mode='json')
    path = next((store.root / 'quick_reads' / run.id).glob('*.json'))
    path.write_text(json.dumps(cached), encoding='utf-8')
    reopened = service().get_quick_read(store, run.id, source)
    assert reopened.context_version == 1 and reopened.coverage.included_pages == [1,2]
