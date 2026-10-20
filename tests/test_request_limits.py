import asyncio
import importlib

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


def exchange(chunks, headers=(), limit=8):
    called, received, sent = [], [], []
    messages = iter(chunks)

    async def receive():
        return next(messages)

    async def downstream(scope, receive, send):
        called.append(True)
        while True:
            message = await receive()
            received.append(message)
            if not message.get('more_body', False):
                break
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok'})

    async def send(message):
        sent.append(message)

    middleware = importlib.import_module('backend.app.request_limits').RequestBodyLimit
    asyncio.run(middleware(downstream, max_bytes=limit)(
        {'type': 'http', 'headers': list(headers)}, receive, send))
    return called, received, sent


def test_chunked_body_rejected_before_downstream_parser():
    called, received, sent = exchange([
        {'type': 'http.request', 'body': b'12345', 'more_body': True},
        {'type': 'http.request', 'body': b'6789', 'more_body': True},
    ])
    assert not called and not received
    assert sent[0]['status'] == 413


def test_exact_limit_preserves_body_bytes():
    chunks = [
        {'type': 'http.request', 'body': b'123', 'more_body': True},
        {'type': 'http.request', 'body': b'45678', 'more_body': False},
    ]
    called, received, sent = exchange(chunks)
    assert called and b''.join(m['body'] for m in received) == b'12345678'
    assert sent[0]['status'] == 200


def test_declared_oversize_does_not_receive_body():
    called, _, sent = exchange([], [(b'content-length', b'9')])
    assert not called and sent[0]['status'] == 413


def test_extremely_large_declared_length_returns_413_not_conversion_error():
    called, _, sent = exchange([], [(b'content-length', b'9' * 5000)])
    assert not called and sent[0]['status'] == 413


def test_empty_body_and_leading_zero_length_are_accepted():
    called, received, sent = exchange([{'type': 'http.request', 'body': b''}],
                                     [(b'content-length', b'000')])
    assert called and received[0]['body'] == b'' and sent[0]['status'] == 200


@pytest.mark.parametrize('headers', [
    [(b'content-length', b'-1')],
    [(b'content-length', b'garbage')],
    [(b'content-length', b'1'), (b'content-length', b'2')],
])
def test_invalid_lengths_rejected_without_parsing(headers):
    called, _, sent = exchange([], headers)
    assert not called and sent[0]['status'] == 400


def test_false_small_length_cannot_bypass_limit():
    called, _, sent = exchange([{'type': 'http.request', 'body': b'123456789'}],
                              [(b'content-length', b'1')])
    assert not called and sent[0]['status'] == 413


def test_disconnect_does_not_run_parser():
    called, _, sent = exchange([{'type': 'http.disconnect'}])
    assert not called and not sent


def test_application_rejects_before_multipart_validation_and_preserves_cors():
    with TestClient(app) as client:
        response = client.post('/api/research/upload', content=b'',
                               headers={'content-length': str(23 * 1024 * 1024),
                                        'origin': 'http://localhost:3000'})
        assert response.status_code == 413
        assert response.headers['access-control-allow-origin'] == 'http://localhost:3000'
        assert client.get('/api/health').status_code == 200
