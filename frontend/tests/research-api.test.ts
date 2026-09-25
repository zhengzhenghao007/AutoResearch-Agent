import { afterEach, expect, test, vi } from 'vitest';
import { researchApi, REQUEST_TIMEOUT_MS } from '@/lib/research-api';
afterEach(() => {vi.unstubAllGlobals();vi.useRealTimers();});
test('uploads multipart with the existing record id and no forced content type', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 'record' })));
  vi.stubGlobal('fetch', fetcher);
  await researchApi.upload(new File(['pdf'], 'paper.pdf'), 'record');
  const [url, options] = fetcher.mock.calls[0];
  expect(url).toContain('/api/research/upload');
  expect(options.body.get('run_id')).toBe('record');
  expect(options.body.get('file').name).toBe('paper.pdf');
  expect(options.headers).toBeUndefined();
});
test('renders structured FastAPI validation errors as readable messages', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:[{loc:['body','topic'],msg:'Field required'}]}), {status:422})));
  await expect(researchApi.search('topic')).rejects.toThrow('body.topic: Field required');
});
test('analysis sends precisely the explicit selection', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response('{}'));
  vi.stubGlobal('fetch', fetcher);
  await researchApi.analyze('record', ['a','c']);
  expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({selected_ids:['a','c']});
});
test('a timeout never reports success or automatically resubmits a mutation', async () => {
  vi.useFakeTimers();
  const fetcher=vi.fn((_url: string,init: RequestInit)=>new Promise((_resolve,reject)=>init.signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')))));
  vi.stubGlobal('fetch',fetcher);
  const request=researchApi.analyze('record',['a']);
  const result=expect(request).rejects.toThrow('server may still be processing');
  await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);
  await result;expect(fetcher).toHaveBeenCalledTimes(1);
});
test('a new PDF record omits run_id',async()=>{
  const fetcher=vi.fn().mockResolvedValue(new Response('{}'));vi.stubGlobal('fetch',fetcher);
  await researchApi.upload(new File(['pdf'],'new.pdf'));expect(fetcher.mock.calls[0][1].body.has('run_id')).toBe(false);
});
