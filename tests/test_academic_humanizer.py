import asyncio
import json
import logging
import pytest
from backend.app.academic_output import AcademicOutputMiddleware
from services import academic_humanizer as skill
from services.humanizer_policy import set_profile

EN = 'It is worth noting that the estimate may reach 3.1% (95% CI [2, 4]) under $x=2$ [12]; DOI 10.1234/abc.'
ZH = '值得注意的是，方法可能改善 F1，结果为 3.1%（见式 2）。'


@pytest.fixture(autouse=True)
def isolated_policy(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTORESEARCH_HUMANIZER_POLICY_FILE',str(tmp_path/'policy.json'))


def test_source_conservation_and_idempotence():
    revised = skill.humanize(EN+'\n\n'+ZH)
    assert revised == 'The '+EN.split('the ',1)[1]+'\n\n'+ZH.split('，',1)[1]
    assert skill.humanize(revised) == revised
    assert skill.humanize('It is worth noting that p53 may decrease.') == 'It is worth noting that p53 may decrease.'


def test_stream_waits_for_paragraph_including_split_fences_and_preserves_bibliography():
    raw = EN+'\r\n\r\n```python\n\n'+EN+'\n\n```\n\n'+ZH+'\n\nReferences\n\n'+EN
    stream = skill.ParagraphStream()
    assert list(stream.feed('It is worth noting')) == []
    output = ''.join(part for char in raw[len('It is worth noting'):] for part in stream.feed(char))
    output += ''.join(stream.feed('',final=True))
    assert output == skill.humanize(raw)
    assert output.startswith('The estimate') and '```python\n\n'+EN in output
    assert '```\n\n'+ZH.split('，',1)[1] in output and output.endswith('References\n\n'+EN)


def test_consistency_and_exception_return_original_without_logging_manuscript(monkeypatch, caplog):
    for changed in ('The estimate DOES reach 3.1%.', 'The estimate may reach 8%.'):
        monkeypatch.setattr(skill, '_edit', lambda _: changed)
        assert skill.humanize(EN) == EN
    def fail(_): raise RuntimeError('private manuscript')
    monkeypatch.setattr(skill,'_edit',fail)
    assert skill.humanize(EN) == EN and 'private manuscript' not in caplog.text
    assert 'kept original' in caplog.text


def test_profiles_and_no_recursive_calls(monkeypatch):
    text='In order to estimate variance, we used Eq. (3).'
    assert skill.humanize(text).startswith('To estimate')
    set_profile('minimal')
    assert skill.humanize(text)==text and skill.humanize(EN)!=EN
    original=skill._edit
    def nested(value):
        assert skill.humanize(value)==value
        return original(value)
    monkeypatch.setattr(skill,'_edit',nested)
    assert skill.humanize(ZH)!=ZH


def test_transport_stream_and_machine_payloads(monkeypatch):
    async def run(mime,chunks,extra=()):
        events=[]
        async def app(scope,receive,send):
            await send({'type':'http.response.start','status':200,'headers':[(b'content-type',mime),*extra]})
            for i, chunk in enumerate(chunks):
                await send({'type':'http.response.body','body':chunk,'more_body':i+1<len(chunks)})
        async def send(event): events.append(event)
        await AcademicOutputMiddleware(app)({'type':'http','path':'/api/future-agent','method':'GET'},None,send)
        return [e['body'] for e in events if 'body' in e]
    data=(ZH+'\n\n'+EN).encode()
    result=asyncio.run(run(b'text/plain',[data[:1],data[1:3],data[3:data.index(b'\n\n')+2],data[data.index(b'\n\n')+2:]]))
    assert len(result)==2 and b''.join(result).decode()==skill.humanize(data.decode())
    obj=json.dumps({'tool_calls':[{'arguments':{'text':EN}}],'latex':'$x=2$','source':ZH}).encode()
    assert asyncio.run(run(b'application/json',[obj]))==[obj]
    encoded=json.dumps(EN).encode()
    assert json.loads(asyncio.run(run(b'application/json',[encoded]))[0])==skill.humanize(EN)
    assert asyncio.run(run(b'text/plain',[data],[(b'content-disposition',b'attachment')]))==[data]


def test_future_agent_defaults_to_prose_and_internal_tool_response_is_raw():
    from agents.base_agent import BaseAgent
    from services.llm_client import LLMResponse
    class Provider:
        def chat(self, **kwargs): return LLMResponse(EN,'offline',0,0,0,0)
    agent=BaseAgent(Provider())
    assert agent.chat('system','input').content == skill.humanize(EN)
    assert agent.chat('system','input',audience='internal').content == EN


def test_policy_api_persists_local_selection_and_rejects_deployment_write():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from backend.app.api.humanizer import router
    app=FastAPI();app.include_router(router);app.state.security_config=SimpleNamespace(deployment=False)
    client=TestClient(app);path='/api/research/settings/academic-humanizer'
    assert client.get(path).json()==dict(enabled=True,profile='standard',editable=True)
    assert client.put(path,json={'profile':'minimal'}).json()['profile']=='minimal'
    assert client.get(path).json()['profile']=='minimal'
    assert client.put(path,json={'profile':'disable'}).status_code==422
    app.state.security_config.deployment=True
    assert client.put(path,json={'profile':'standard'}).status_code==403


def test_sse_prose_channel_never_exposes_unedited_tokens_or_latex_blocks():
    from backend.app.academic_output import prose_events
    async def deltas():
        for chunk in [EN[:10], EN[10:], '\n\n', '\\[\n\n', EN, '\n\n\\]\n\n', ZH]:
            yield chunk
    async def read():
        return [json.loads(item.split('data: ',1)[1]) async for item in prose_events(deltas())]
    paragraphs=asyncio.run(read())
    assert paragraphs[0]==skill.humanize(EN)+'\n\n'
    assert ''.join(paragraphs)==skill.humanize(EN)+'\n\n\\[\n\n'+EN+'\n\n\\]\n\n'+skill.humanize(ZH)
