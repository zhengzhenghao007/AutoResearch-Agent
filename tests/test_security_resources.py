import asyncio
import json
import pytest
from backend.app import security
from backend.app.request_limits import RequestBodyLimit


def test_config_rejects_bad_token_without_disclosing_it(tmp_path, monkeypatch):
    monkeypatch.setattr(security, 'isolation_supported', lambda: True)
    path = tmp_path / 'users.json'
    path.write_text(json.dumps({'alice': {'token': 'secret', 'role': 'writer'}}))
    with pytest.raises(ValueError, match='Invalid deployment users'):
        security.load_config({'AUTORESEARCH_DEPLOYMENT': '1', 'AUTORESEARCH_DATA_ROOT': str(tmp_path), 'AUTORESEARCH_USERS_FILE': str(path)})


@pytest.mark.parametrize('token,method,path,status', [(None,'POST','/api/research/upload',401), ('r'*32,'POST','/api/research/runs',403), ('w'*32,'GET','/api/papers/search',403), (None,'GET','/docs',401)])
def test_security_rejects_before_body(token, method, path, status, tmp_path):
    cfg = security.SecurityConfig(True, tmp_path, {'alice': {'token':'w'*32,'role':'writer'}, 'bob': {'token':'r'*32,'role':'reader'}})
    sent = []
    async def forbidden(*args):
        pytest.fail('Unauthorized request reached body/downstream')
    async def send(message): sent.append(message)
    headers = [] if token is None else [(b'authorization', ('Bearer '+token).encode())]
    asyncio.run(security.SecurityMiddleware(forbidden, config=cfg)({'type':'http','method':method,'path':path,'headers':headers}, forbidden, send))
    assert sent[0]['status'] == status


def test_body_deadline():
    sent = []
    async def receive(): await asyncio.sleep(1)
    async def downstream(*args): pytest.fail('Timed out request reached parser')
    async def send(message): sent.append(message)
    asyncio.run(RequestBodyLimit(downstream, body_timeout=.01)({'type':'http','headers':[]}, receive, send))
    assert sent[0]['status'] == 408


def test_admission_limit():
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        async def downstream(scope, receive, send):
            entered.set()
            await release.wait()
        async def receive(): return {'type':'http.request','body':b''}
        sent = []
        async def send(message): sent.append(message)
        middleware = RequestBodyLimit(downstream, max_concurrent=1)
        first = asyncio.create_task(middleware({'type':'http','headers':[]}, receive, send))
        await entered.wait()
        await middleware({'type':'http','headers':[]}, receive, send)
        release.set()
        await first
        assert sent[0]['status'] == 503
    asyncio.run(scenario())


def test_users_cannot_access_other_users_records_manuscripts_or_jobs(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.app.api.research import router
    from backend.app.api import jobs
    from services.research_jobs import JobManager
    monkeypatch.setattr(jobs, 'manager_for', lambda store: JobManager(store, autostart=False))
    app = FastAPI()
    config = security.SecurityConfig(True,tmp_path,{'alice':{'token':'a'*32,'role':'writer'},'bob':{'token':'b'*32,'role':'writer'},'reader':{'token':'r'*32,'role':'reader'}},sqlite=True)
    app.state.security_config = config
    app.add_middleware(security.SecurityMiddleware,config=config)
    app.include_router(router);app.include_router(jobs.router)
    with TestClient(app) as client:
        alice={'Authorization':'Bearer '+'a'*32};bob={'Authorization':'Bearer '+'b'*32};reader={'Authorization':'Bearer '+'r'*32}
        created=client.post('/api/research/runs',json={'topic':'Alice private'},headers=alice)
        assert created.status_code == 200
        identity=created.json()['id']
        job=client.post('/api/research/jobs',json={'kind':'search','topic':'Private job'},headers=alice).json()
        for path in (f'/api/research/runs/{identity}',f'/api/research/runs/{identity}/manuscript',f"/api/research/jobs/{job['id']}"):
            assert client.get(path,headers=bob).status_code == 404
        assert client.post(f"/api/research/jobs/{job['id']}/cancel",headers=bob).status_code == 404
        assert client.get('/api/research/runs',headers=bob).json()['total'] == 0
        assert client.get('/api/research/jobs',headers=bob).json()['items'] == []
        assert client.get('/api/research/session',headers=reader).json()['role'] == 'reader'
        assert client.post('/api/research/runs',json={'topic':'Denied'},headers=reader).status_code == 403
        assert client.get('/api/research/runs').status_code == 401
        assert client.get('/api/health').status_code == 404  # Public but absent in this fixture.


@pytest.mark.parametrize('peer,host', [('192.0.2.1',b'localhost'),('127.0.0.1',b'evil.example'),('127.0.0.1',b'[evil]')])
def test_local_mode_rejects_remote_clients_and_untrusted_hosts(tmp_path,peer,host):
    sent=[]
    async def forbidden(*args): pytest.fail('Untrusted local request accepted')
    async def send(value): sent.append(value)
    asyncio.run(security.SecurityMiddleware(forbidden,security.SecurityConfig(False,tmp_path,{}))(
        {'type':'http','path':'/api/research/runs','client':(peer,123),'headers':[(b'host',host)]},forbidden,send))
    assert sent[0]['status']==403


def test_deployment_refuses_unsupported_parser_isolation(monkeypatch):
    monkeypatch.setattr(security,'isolation_supported',lambda:False)
    with pytest.raises(ValueError,match='Linux'):
        security.load_config({'AUTORESEARCH_DEPLOYMENT':'1'})


def test_linux_parser_limits_in_disposable_process():
    import sys
    import subprocess
    if not sys.platform.startswith('linux'):
        pytest.skip('OS resource limits are verified by Linux CI')
    code = """from services.parser_limits import apply_parser_limits
import resource
assert apply_parser_limits()
assert resource.getrlimit(resource.RLIMIT_AS) == (536870912,536870912)
assert resource.getrlimit(resource.RLIMIT_CPU) == (30,31)
assert resource.getrlimit(resource.RLIMIT_NOFILE) == (64,64)
"""
    subprocess.run([sys.executable,'-c',code],check=True,timeout=10)
