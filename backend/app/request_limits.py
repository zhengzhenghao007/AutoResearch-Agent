"""Bound HTTP input before JSON/multipart parsing or upload spooling."""
import json
import asyncio
from threading import Lock
from starlette.types import ASGIApp, Receive, Scope, Send

MAX_REQUEST_BYTES = 22 * 1024 * 1024  # 20 MiB PDF plus multipart overhead.


class RequestBodyLimit:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_REQUEST_BYTES, body_timeout=30, max_concurrent=8):
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
            raise ValueError('max_bytes must be a positive integer')
        self.app, self.max_bytes = app, max_bytes
        if body_timeout <= 0 or max_concurrent < 1:
            raise ValueError('Invalid request resource limits')
        self.body_timeout, self.max_concurrent = body_timeout, max_concurrent
        self.active, self.lock = 0, Lock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        with self.lock:
            admitted = self.active < self.max_concurrent
            if admitted:
                self.active += 1
        if not admitted:
            return await self.reject(send, 503, 'Request capacity reached; retry later')
        try:
            return await self.handle(scope, receive, send)
        finally:
            with self.lock:
                self.active -= 1

    async def handle(self, scope, receive, send):
        lengths = [value for name, value in scope.get('headers', [])
                   if name.lower() == b'content-length']
        if len(lengths) > 1 or (lengths and (not lengths[0] or not lengths[0].isdigit())):
            return await self.reject(send, 400, 'Invalid Content-Length')
        if lengths:
            value = lengths[0].lstrip(b'0') or b'0'
            if len(value) > len(str(self.max_bytes)) or int(value) > self.max_bytes:
                return await self.reject(send, 413, f'Request body exceeds {self.max_bytes} byte limit')
        # A single bytearray avoids per-chunk object amplification for tiny chunks.
        # Nothing reaches multipart parsing until the entire input fits the cap.
        body = bytearray()
        deadline = asyncio.get_running_loop().time() + self.body_timeout
        while True:
            try:
                message = await asyncio.wait_for(receive(), max(0, deadline - asyncio.get_running_loop().time()))
            except TimeoutError:
                return await self.reject(send, 408, 'Request body deadline exceeded')
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            if len(body) + len(chunk) > self.max_bytes:
                return await self.reject(send, 413, f'Request body exceeds {self.max_bytes} byte limit')
            body.extend(chunk)
            if not message.get('more_body', False):
                break
        replayed = False

        async def replay():
            nonlocal replayed, body
            if replayed:
                return await receive()
            replayed = True
            data = bytes(body)
            body.clear()
            return {'type': 'http.request', 'body': data, 'more_body': False}

        await self.app(scope, replay, send)

    @staticmethod
    async def reject(send: Send, status: int, detail: str):
        body = json.dumps({'detail': detail}).encode('utf-8')
        await send({'type': 'http.response.start', 'status': status,
                    'headers': [(b'content-type', b'application/json'),
                                (b'content-length', str(len(body)).encode('ascii'))]})
        await send({'type': 'http.response.body', 'body': body})
