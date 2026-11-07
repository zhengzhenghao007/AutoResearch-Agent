import json
from types import SimpleNamespace
from uuid import uuid4
import pytest
from schemas.research import CATEGORIES, Review, ResearchRun, PaperEvidence, Document, Source, Page, Evidence
from services.research_store import ResearchStore


def setup(tmp_path):
    store = ResearchStore(tmp_path)
    quote = 'The method improves coverage on this dataset.'
    paper = PaperEvidence(missing_fields=list(CATEGORIES), document=Document(source=Source(id='s1', title='Paper', uri='upload:p', sha256='a'*64), pages=[Page(number=1,text=quote)],total_pages=1), evidence=[Evidence(id='e1',source_id='s1',page=1,quote=quote)])
    run = ResearchRun(id=uuid4().hex,topic='coverage',plan=[],papers=[paper],review=Review(approved=False,issues=['Paper: No supported claims extracted']))
    store.save(run)
    return store, run


def output():
    return dict(matrix=[dict(source_id='s1',research_question='Coverage?',method='Method',results='Reported improvement',limitations='Single dataset',evidence_ids=['e1'],uncertainty='Scope uncertain')], hypotheses=[dict(kind='hypothesis',text='May generalize',evidence_ids=['e1'],validation_experiment='Test on held-out datasets',uncertainty='Not tested')], review=[dict(theme='Coverage',text='Authors report improvement',kind='author_claim',evidence_ids=['e1'],uncertainty='Single source')], uncertainties=['Scientific validity unassessed'])


class Fake:
    def __init__(self, data=None, callback=None): self.data=data or output(); self.calls=0; self.callback=callback
    def chat(self, **kwargs):
        self.calls += 1
        if self.callback: self.callback()
        return SimpleNamespace(content=json.dumps(self.data),model_name='fake',input_tokens=100,output_tokens=50,total_tokens=150)


def test_consent_cache_and_usage(tmp_path):
    from services.research_reasoning import ResearchReasoner
    store, run=setup(tmp_path); fake=Fake(); ex=ResearchReasoner(store,client_factory=lambda **kw:fake)
    fake.data['matrix'][0]['results'] = 'It is important to note that the sample includes 27 trials.'
    with pytest.raises(ValueError): ex.generate(run.id,dict(question='Compare',allow_model=False))
    result=ex.generate(run.id,dict(question='Compare',allow_model=True))
    assert result['status']=='completed' and result['usage']['input_tokens']==100
    assert result['report']['matrix'][0]['results'] == 'The sample includes 27 trials.'
    assert result['report']['hypotheses'][0]['kind']=='hypothesis'
    assert ex.generate(run.id,dict(question='Compare',allow_model=False))['id']==result['id']
    assert fake.calls==1
    assert ex.history(run.id)[0]['current'] is True


@pytest.mark.parametrize('bad', ['empty','quote','source','page'])
def test_invalid_input_never_calls(tmp_path,bad):
    from services.research_reasoning import ResearchReasoner
    store,run=setup(tmp_path); fake=Fake()
    if bad=='empty': run.papers=[]
    elif bad=='quote': run.papers[0].evidence[0].quote='Fabricated quotation here'
    elif bad=='source': run.papers[0].evidence[0].source_id='absent'
    else: run.papers[0].evidence[0].page=2
    store.load = lambda run_id: run
    with pytest.raises(ValueError): ResearchReasoner(store,client_factory=lambda **kw:fake).generate(run.id,dict(question='Compare',allow_model=True))
    assert fake.calls==0


@pytest.mark.parametrize('bad', ['ids','kind','provider'])
def test_failed_generation_is_sanitized_and_not_retried(tmp_path,bad):
    from services.research_reasoning import ResearchReasoner
    store,run=setup(tmp_path); data=output()
    if bad=='ids': data['review'][0]['evidence_ids']=['madeup']
    if bad=='kind': data['hypotheses'][0]['kind']='author_claim'
    def fail(): raise RuntimeError('secret api-key')
    fake=Fake(data,fail if bad=='provider' else None); ex=ResearchReasoner(store,client_factory=lambda **kw:fake)
    first=ex.generate(run.id,dict(question='Compare',allow_model=True))
    assert first['status']=='failed' and 'secret' not in json.dumps(first)
    if bad=='provider': assert first['usage']['total_tokens'] is None
    assert ex.generate(run.id,dict(question='Compare',allow_model=True))['id']==first['id']
    assert fake.calls==1


def test_goal_change_marks_response_stale(tmp_path):
    from services.research_reasoning import ResearchReasoner
    store,run=setup(tmp_path)
    def change():
        current=store.load(run.id); current.research_goal='Different goal';store.save(current)
    ex=ResearchReasoner(store,client_factory=lambda **kw:Fake(callback=change))
    result=ex.generate(run.id,dict(question='Compare',allow_model=True))
    assert result['current'] is False and result['status']=='stale'


def test_call_limit_and_crash_reservation(tmp_path):
    from services.research_reasoning import ResearchReasoner
    store,run=setup(tmp_path)
    def crash(): raise KeyboardInterrupt()
    fake=Fake(callback=crash); ex=ResearchReasoner(store,client_factory=lambda **kw:fake)
    with pytest.raises(KeyboardInterrupt): ex.generate(run.id,dict(question='Compare',allow_model=True))
    assert ResearchReasoner(store).generate(run.id,dict(question='Compare',allow_model=True))['status']=='reserved'
    fake.callback=None
    for q in ['Second','Third']: ex.generate(run.id,dict(question=q,allow_model=True))
    with pytest.raises(ValueError,match='limit'): ex.generate(run.id,dict(question='Fourth',allow_model=True))
    assert fake.calls==3


def test_concurrent_claims_send_once(tmp_path):
    from services.research_reasoning import ResearchReasoner
    from threading import Event, Thread
    store,run=setup(tmp_path); entered=Event(); release=Event()
    def block(): entered.set(); assert release.wait(5)
    fake=Fake(callback=block); ex=ResearchReasoner(store,client_factory=lambda **kw:fake)
    thread=Thread(target=lambda:ex.generate(run.id,dict(question='Compare',allow_model=True)));thread.start()
    assert entered.wait(5)
    second=ResearchReasoner(store).generate(run.id,dict(question='Compare',allow_model=True))
    assert second['status']=='reserved'
    release.set();thread.join(5)
    assert fake.calls==1 and ex.history(run.id)[0]['status']=='completed'




def test_bounded_real_corpus_reports_coverage_and_includes_each_paper():
    from pathlib import Path
    from services.research_reasoning import validated_evidence
    run = ResearchRun.model_validate_json(Path('examples/conformal-prediction/outputs/run.json').read_text(encoding='utf-8'))
    items = validated_evidence(run, 'conformal coverage')
    assert len(items) <= 40
    assert {r['source_id'] for r in items} == {p.document.source.id for p in run.papers}
    assert all(r['quote'] for r in items)


def test_local_configuration_error_does_not_reserve_provider_call(tmp_path):
    from services.research_reasoning import ResearchReasoner
    store,run=setup(tmp_path)
    def missing(**kwargs): raise ValueError('missing credential')
    ex=ResearchReasoner(store,client_factory=missing)
    with pytest.raises(ValueError,match='Configure'): ex.generate(run.id,dict(question='Compare',allow_model=True))
    assert ex.history(run.id)==[]
