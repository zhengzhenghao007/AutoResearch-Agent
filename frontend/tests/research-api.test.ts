import { afterEach, expect, test, vi } from 'vitest';
import { researchApi, REQUEST_TIMEOUT_MS, setResearchToken } from '@/lib/research-api';
afterEach(() => {setResearchToken('');vi.unstubAllGlobals();vi.useRealTimers();});
test('credentials are headers only and cleared before another session',async()=>{
  const fetcher=vi.fn().mockImplementation(()=>Promise.resolve(new Response('{}')));
  vi.stubGlobal('fetch',fetcher);
  setResearchToken('synthetic-token');
  await researchApi.session();
  expect(fetcher.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer synthetic-token');
  expect(fetcher.mock.calls[0][0]).not.toContain('synthetic-token');
  setResearchToken('');
  await researchApi.session();
  expect(fetcher.mock.calls[1][1].headers.has('Authorization')).toBe(false);
});
test('experiment import preserves multipart CSV metadata and statistics route',async()=>{
  const fetcher=vi.fn().mockImplementation(()=>Promise.resolve(new Response('{}')));vi.stubGlobal('fetch',fetcher);
  const metadata={title:'Study',protocol:null,statistical_method:null,columns:[{name:'x',unit:'m'}]};
  const file=new File(['sample_id,x\ns1,0\n'],'data.csv');
  await researchApi.importExperiment('a/b',file,'csv',metadata);
  expect(fetcher.mock.calls[0][0]).toContain('/runs/a%2Fb/experiments/csv');
  expect(fetcher.mock.calls[0][1].body.get('file')).toBe(file);
  expect(JSON.parse(fetcher.mock.calls[0][1].body.get('metadata'))).toEqual(metadata);
  expect(fetcher.mock.calls[0][1].headers.has('Content-Type')).toBe(false);
  await researchApi.experimentStatistics('a/b');
  expect(fetcher.mock.calls[1][0]).toContain('/runs/a%2Fb/experiment-statistics');
  await researchApi.create('Offline');
  expect(JSON.parse(fetcher.mock.calls[2][1].body)).toEqual({topic:'Offline'});
});
test('screening posts only annotation fields to the encoded route',async()=>{
  const payload={id:'record',candidate_decisions:[]};
  const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));
  vi.stubGlobal('fetch',fetcher);
  const body={candidate_id:'paper',decision:'exclude' as const,reason:'Different protocol'};
  expect(await researchApi.candidateDecision('a/b',body)).toEqual(payload);
  expect(fetcher.mock.calls[0][0]).toContain('/runs/a%2Fb/candidate-decisions');
  expect(fetcher.mock.calls[0][1].method).toBe('POST');
  expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual(body);
});
test('screening timeout never retries a non-idempotent annotation',async()=>{
  vi.useFakeTimers();
  const fetcher=vi.fn((_url: string,init: RequestInit)=>new Promise((_resolve,reject)=>init.signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')))));
  vi.stubGlobal('fetch',fetcher);
  const result=expect(researchApi.candidateDecision('record',{candidate_id:'a',decision:'include',reason:'Relevant'})).rejects.toThrow('server may still be processing');
  await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);await result;
  expect(fetcher).toHaveBeenCalledTimes(1);
});
test('export reads use encoded routes and preserve backend payloads', async () => {
  const payload={run_id:'a/b',bibtex:'exact\n',skipped_sources:[]};
  const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));
  vi.stubGlobal('fetch',fetcher);
  expect(await researchApi.bibtex('a/b')).toEqual(payload);
  expect(fetcher.mock.calls[0][0]).toContain('/runs/a%2Fb/bibtex');
  fetcher.mockResolvedValue(new Response(JSON.stringify({detail:'Corrupt snapshot'}),{status:400}));
  await expect(researchApi.citations('a/b')).rejects.toThrow('Corrupt snapshot');
  expect(fetcher.mock.calls[1][0]).toContain('/runs/a%2Fb/citations');
});
test('uploads multipart with the existing record id and no forced content type', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 'record' })));
  vi.stubGlobal('fetch', fetcher);
  await researchApi.upload(new File(['pdf'], 'paper.pdf'), 'record');
  const [url, options] = fetcher.mock.calls[0];
  expect(url).toContain('/api/research/upload');
  expect(options.body.get('run_id')).toBe('record');
  expect(options.body.get('file').name).toBe('paper.pdf');
  expect(options.headers.has('Content-Type')).toBe(false);
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

test('DOI routes preserve server views and omit DOI on clear',async()=>{
  const fetcher=vi.fn().mockImplementation(()=>Promise.resolve(new Response(JSON.stringify({run_id:'a/b',sources:[],conflicts:[]}))));vi.stubGlobal('fetch',fetcher);
  expect(await researchApi.sourceIdentities('a/b')).toEqual({run_id:'a/b',sources:[],conflicts:[]});
  await researchApi.sourceIdentity('a/b',{source_id:'s',action:'set',doi:'10.1234/test',reason:'Printed'});
  await researchApi.sourceIdentity('a/b',{source_id:'s',action:'clear',reason:'Incorrect'});
  expect(fetcher.mock.calls[0][0]).toContain('/runs/a%2Fb/source-identities');
  expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({source_id:'s',action:'set',doi:'10.1234/test',reason:'Printed'});
  expect(JSON.parse(fetcher.mock.calls[2][1].body)).toEqual({source_id:'s',action:'clear',reason:'Incorrect'});
});

test('duplicate clues use the encoded read-only route and preserve payloads',async()=>{
  const payload={schema_version:1,run_id:'a/b',groups:[],candidate_source_links:[]};
  const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));vi.stubGlobal('fetch',fetcher);
  expect(await researchApi.sourceDuplicates('a/b')).toEqual(payload);
  expect(fetcher.mock.calls[0][0]).toContain('/runs/a%2Fb/source-duplicates');
  expect(fetcher.mock.calls[0][1].method).toBeUndefined();
});

test('screening export uses an encoded read-only route',async()=>{
  const payload={schema_version:1,run_id:'a/b',counts:{total:0,include:0,exclude:0,undecided:0,selected:0},items:[],scope:'Annotations only',topic:'Test'};
  const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));vi.stubGlobal('fetch',fetcher);
  expect(await researchApi.screeningReport('a/b')).toEqual(payload);
  expect(fetcher.mock.calls[0][0]).toContain('/runs/a%2Fb/screening-report');
  expect(fetcher.mock.calls[0][1].method).toBeUndefined();
});

test('claim review uses an encoded read-only route',async()=>{
  const payload={schema_version:1,run_id:'a/b',rule_version:'planning-language-en-v1',claim_count:0,checked_claim_count:0,flagged_claim_count:0,flags:[],semantic_validation:'not_assessed',scope:'Advisory only'};
  const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));vi.stubGlobal('fetch',fetcher);
  expect(await researchApi.claimReview('a/b')).toEqual(payload);
  expect(fetcher.mock.calls[0][0]).toContain('/runs/a%2Fb/claim-review');
  expect(fetcher.mock.calls[0][1].method).toBeUndefined();
});
