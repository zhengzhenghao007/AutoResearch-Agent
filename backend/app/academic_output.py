"""Publish generated text responses at semantic paragraph boundaries."""
import codecs
import json
from services import academic_humanizer


class AcademicOutputMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not scope['path'].startswith('/api/') or scope['method'] == 'HEAD':
            return await self.app(scope, receive, send)
        mode = None
        decoder = codecs.getincrementaldecoder('utf-8')('surrogateescape')
        paragraphs = academic_humanizer.ParagraphStream()
        deferred = None

        async def publish(event):
            nonlocal mode, deferred
            if event['type'] == 'http.response.start':
                headers = dict(event['headers'])
                mime = headers.get(b'content-type', b'').lower().replace(b' ', b'')
                if event['status'] == 200 and not any(key in headers for key in (b'content-disposition', b'content-encoding', b'etag', b'content-range')):
                    if mime in (b'text/plain', b'text/plain;charset=utf-8'):
                        mode = 'prose'
                        event = {**event, 'headers': [(k,v) for k,v in event['headers'] if k != b'content-length']}
                    elif mime == b'application/json':
                        deferred = event
                        return
            elif event['type'] == 'http.response.body':
                body = event.get('body', b'')
                more = event.get('more_body', False)
                if deferred is not None:
                    # Only bare string responses represent plain prose. Typed records have already
                    # classified their generated fields; never walk or rewrite arbitrary JSON.
                    if not more and body.startswith(b'"'):
                        original = json.loads(body)
                        revised = academic_humanizer.humanize(original)
                        if revised != original:
                            body = json.dumps(revised,ensure_ascii=False).encode('utf-8')
                            event = {**event,'body':body}
                            deferred = {**deferred,'headers':[(k,v) for k,v in deferred['headers'] if k!=b'content-length'] + [(b'content-length',str(len(body)).encode())]}
                    await send(deferred)
                    deferred = None
                if mode == 'prose':
                    text = decoder.decode(body,final=not more)
                    checked = ''.join(paragraphs.feed(text, final=not more))
                    if not checked and more:
                        return
                    event = {**event,'body':checked.encode('utf-8','surrogateescape')}
            await send(event)
        await self.app(scope, receive, publish)


async def prose_events(deltas):
    """Encode an async stream of generated text deltas as checked SSE paragraphs.

    Structured tool-call events belong on their own event channel. This encoder
    accepts only the prose channel, so a partial JSON argument cannot be edited.
    """
    paragraphs = academic_humanizer.ParagraphStream()
    async for delta in deltas:
        for paragraph in paragraphs.feed(delta):
            yield 'event: paragraph\ndata: ' + json.dumps(paragraph, ensure_ascii=False) + '\n\n'
    for paragraph in paragraphs.feed('', final=True):
        yield 'event: paragraph\ndata: ' + json.dumps(paragraph, ensure_ascii=False) + '\n\n'
