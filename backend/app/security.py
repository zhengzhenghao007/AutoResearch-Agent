"""Server-managed credentials and tenant roots; never expose configured tokens."""
import hmac
import ipaddress
import json
import os
import re
from urllib.parse import urlsplit
from dataclasses import dataclass, field
from pathlib import Path

from services.parser_limits import isolation_supported
from backend.app.request_limits import RequestBodyLimit


@dataclass(frozen=True)
class SecurityConfig:
    deployment: bool
    root: Path
    users: dict
    sqlite: bool = False
    origins: list[str] = field(default_factory=lambda: ['http://localhost:3000', 'http://127.0.0.1:3000'])


def load_config(env=None):
    env = os.environ if env is None else env
    if env.get('AUTORESEARCH_DEPLOYMENT', '0') not in ('0', '1'):
        raise ValueError('AUTORESEARCH_DEPLOYMENT must be 0 or 1')
    deployment = env.get('AUTORESEARCH_DEPLOYMENT') == '1'
    root = Path(env.get('AUTORESEARCH_DATA_ROOT', Path(__file__).resolve().parents[2] / 'data/deployment'))
    storage = env.get('AUTORESEARCH_STORAGE', 'json')
    if storage not in ('json', 'sqlite'):
        raise ValueError('AUTORESEARCH_STORAGE must be json or sqlite')
    users = {}
    if deployment:
        if not isolation_supported():
            raise ValueError('Deployment requires Linux parser CPU/memory isolation')
        if not env.get('AUTORESEARCH_DATA_ROOT') or not env.get('AUTORESEARCH_USERS_FILE'):
            raise ValueError('Deployment requires data root and users file configuration')
        try:
            path = Path(env['AUTORESEARCH_USERS_FILE'])
            with path.open('rb') as stream:
                data = stream.read(65537)
            if len(data) > 65536:
                raise ValueError()
            users = json.loads(data)
            if not isinstance(users, dict) or not 1 <= len(users) <= 100:
                raise ValueError()
            tokens = set()
            for name, user in users.items():
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name) or not isinstance(user, dict) or set(user) != {'token','role'}:
                    raise ValueError()
                token = user['token']
                if (not isinstance(token, str) or not 32 <= len(token) <= 256
                        or not token.isascii() or not token.isprintable() or any(c.isspace() for c in token)
                        or user['role'] not in ('reader','writer') or token in tokens):
                    raise ValueError()
                tokens.add(token)
        except (OSError, ValueError, TypeError) as exc:
            raise ValueError('Invalid deployment users configuration') from None
    origins = [x.strip() for x in env.get('AUTORESEARCH_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if x.strip()]
    if not origins or any(not (x.startswith('https://') or x in ('http://localhost:3000','http://127.0.0.1:3000')) for x in origins):
        raise ValueError('Allowed origins require HTTPS or the local development origin')
    return SecurityConfig(deployment, root, users, deployment or storage == 'sqlite', origins)


class SecurityMiddleware:
    def __init__(self, app, config):
        self.app, self.config = app, config

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        config = self.config
        if scope.get('path') == '/api/health':
            return await self.app(scope, receive, send)
        principal = {'id':'local', 'role':'writer'}
        if config.deployment:
            headers = [v for k,v in scope.get('headers', []) if k.lower() == b'authorization']
            token = headers[0][7:] if len(headers) == 1 and headers[0].startswith(b'Bearer ') else b''
            principal = None
            for user_id, user in config.users.items():
                if hmac.compare_digest(token, user['token'].encode('ascii')):
                    principal = {'id':user_id, 'role':user['role']}
            if principal is None:
                return await RequestBodyLimit.reject(send, 401, 'Authentication required')
            if scope.get('path', '').startswith('/api/papers'):
                return await RequestBodyLimit.reject(send, 403, 'Legacy endpoints are disabled in deployment mode')
            path = scope.get('path', '')
            if path == '/api/research/search' or re.fullmatch(r'/api/research/runs/[^/]+/analyze', path):
                return await RequestBodyLimit.reject(send, 403, 'Use bounded background jobs for search and analysis in deployment mode')
            if principal['role'] == 'reader' and scope.get('method') not in ('GET','HEAD','OPTIONS'):
                return await RequestBodyLimit.reject(send, 403, 'Writer permission required')
        else:
            host = (scope.get('client') or ('',0))[0]
            try:
                allowed = ipaddress.ip_address(host).is_loopback
            except ValueError:
                allowed = host == 'testclient'
            hosts = [v for k,v in scope.get('headers',[]) if k.lower() == b'host']
            try:
                hostname = urlsplit('//' + hosts[0].decode('ascii')).hostname if len(hosts) == 1 else None
            except (ValueError, UnicodeError):
                hostname = None
            if not allowed or hostname not in ('localhost','127.0.0.1','::1','testserver'):
                return await RequestBodyLimit.reject(send, 403, 'Local mode accepts loopback clients only')
        scope.setdefault('state', {})['principal'] = principal
        await self.app(scope, receive, send)


def workflow_for_request(request):
    from workflow.evidence_workflow import EvidenceWorkflow
    config = request.app.state.security_config
    if config.sqlite:
        from services.sqlite_store import SQLiteResearchStore
        user_id = request.state.principal['id']
        return EvidenceWorkflow(store=SQLiteResearchStore(config.root / 'users' / user_id))
    return EvidenceWorkflow()


def session_info(request):
    config = request.app.state.security_config
    principal = request.state.principal
    return {'mode':'deployment' if config.deployment else 'local',
            'user_id':principal['id'], 'role':principal['role'], 'jobs_enabled':config.sqlite}
