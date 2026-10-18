import {afterEach,expect,test,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Experiments from '@/components/Experiments';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{experiments:vi.fn(),experimentStatistics:vi.fn()}}));
const run:ResearchRun={schema_version:1,id:'a'.repeat(32),topic:'Study',plan:[],candidates:[],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,issues:[],scope:'Unverified'}};
const report={schema_version:1 as const,run_id:run.id,datasets:[],scientific_validation:'not_assessed' as const,scope:'No scientific validation.'};
const stats={...report,algorithm:'descriptive-v1' as const,datasets:[{dataset_id:'b'.repeat(64),sha256:'b'.repeat(64),title:'Measurements',columns:[{name:'x',unit:null,observed_count:1,missing_count:1,mean:'9007199254740993',minimum:'9007199254740993',maximum:'9007199254740993',sample_standard_deviation:null,references:[{sample_id:'s1',column:'x',value:'9007199254740993'}],status:'insufficient_samples' as const,warnings:['At least two observations required for sample SD.']}]}]};
afterEach(()=>{vi.resetAllMocks();vi.restoreAllMocks();vi.unstubAllGlobals();});

test('upload preserves file and metadata on failure and serializes explicit CSV metadata',async()=>{
  const save=vi.fn().mockRejectedValueOnce(new Error('Upload failed')).mockResolvedValue(true);
  render(<Experiments run={run} revision={0} busy={false} onImport={save}/>);
  await userEvent.selectOptions(screen.getByLabelText('Observation file format'),'csv');
  await userEvent.type(screen.getByLabelText('Dataset title'),'My measurements');
  await userEvent.type(screen.getByLabelText('Columns and units'),'temperature=C\nscore=');
  const file=new File(['sample_id,temperature,score\ns1,0,\n'],'data.csv',{type:'text/csv'});
  await userEvent.upload(screen.getByLabelText('Observation file'),file);
  await userEvent.click(screen.getByRole('button',{name:'Import observations'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Upload failed');
  expect(screen.getByLabelText('Dataset title')).toHaveValue('My measurements');
  expect((screen.getByLabelText('Observation file') as HTMLInputElement).files?.[0]).toBe(file);
  await userEvent.click(screen.getByRole('button',{name:'Import observations'}));
  expect(save).toHaveBeenLastCalledWith(file,'csv',{title:'My measurements',protocol:null,statistical_method:null,columns:[{name:'temperature',unit:'C'},{name:'score',unit:null}]});
  expect((screen.getByLabelText('Observation file') as HTMLInputElement).value).toBe('');
});

test('explicit statistics preserve decimal strings and show references and missing SD',async()=>{
  vi.mocked(researchApi.experiments).mockResolvedValue(report);
  vi.mocked(researchApi.experimentStatistics).mockResolvedValue(stats);
  render(<Experiments run={run} revision={0} busy={false} onImport={vi.fn()}/>);
  expect(researchApi.experimentStatistics).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Load data checks and statistics'}));
  expect(await screen.findByText('Measurements')).toBeInTheDocument();
  expect(screen.getAllByText('9007199254740993').length).toBeGreaterThan(0);
  expect(screen.getByText(/At least two observations/)).toBeInTheDocument();
  expect(screen.getByText('s1 / x: 9007199254740993')).toBeInTheDocument();
  expect(screen.getByText(/No scientific validation/)).toBeInTheDocument();
});

test('successful revision discards stale report but preserves import draft',async()=>{
  let resolve!:(value:typeof stats)=>void;
  vi.mocked(researchApi.experiments).mockResolvedValue(report);
  vi.mocked(researchApi.experimentStatistics).mockReturnValue(new Promise(r=>{resolve=r;}));
  const {rerender}=render(<Experiments run={run} revision={0} busy={false} onImport={vi.fn()}/>);
  await userEvent.selectOptions(screen.getByLabelText('Observation file format'),'csv');
  await userEvent.type(screen.getByLabelText('Dataset title'),'Draft');
  await userEvent.click(screen.getByRole('button',{name:'Load data checks and statistics'}));
  rerender(<Experiments run={run} revision={1} busy={false} onImport={vi.fn()}/>);
  await act(async()=>resolve(stats));
  expect(screen.queryByText('Measurements')).not.toBeInTheDocument();
  expect(screen.getByLabelText('Dataset title')).toHaveValue('Draft');
});

test('rejects report for another record',async()=>{
  vi.mocked(researchApi.experiments).mockResolvedValue({...report,run_id:'other'});
  vi.mocked(researchApi.experimentStatistics).mockResolvedValue(stats);
  render(<Experiments run={run} revision={0} busy={false} onImport={vi.fn()}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load data checks and statistics'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('different record');
  expect(screen.queryByText('Measurements')).not.toBeInTheDocument();
});

test('accepts a CSV metadata envelope above 1 MiB through JSON import',async()=>{
  const save=vi.fn().mockResolvedValue(true);
  render(<Experiments run={run} revision={0} busy={false} onImport={save}/>);
  const file=new File([' '.repeat(1024*1024+100)],'envelope.json',{type:'application/json'});
  await userEvent.upload(screen.getByLabelText('Observation file'),file);
  await userEvent.click(screen.getByRole('button',{name:'Import observations'}));
  expect(save).toHaveBeenCalledWith(file,'json',undefined);
});

test('exports original numeric JSON without browser rounding and resets on record change',async()=>{
  const create=vi.fn().mockReturnValue('blob:test');vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:create,revokeObjectURL:vi.fn()}));
  vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
  const raw='\ufeff{"value":9007199254740993}\r\n';
  const dataset={id:'b'.repeat(64),sha256:'b'.repeat(64),kind:'user_data' as const,claim_type:'user_observation' as const,raw_json:raw,imported_at:'2026-10-17T00:00:00Z',data:{title:'Exact source',protocol:null,statistical_method:null,columns:[],rows:[]}};
  const {rerender}=render(<Experiments run={{...run,experiments:[dataset]}} revision={0} busy={false} onImport={vi.fn()}/>);
  await userEvent.click(screen.getByRole('button',{name:'Download original input'}));
  const blob=create.mock.calls[0][0] as Blob;
  const buffer=await new Promise<ArrayBuffer>(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result as ArrayBuffer);reader.readAsArrayBuffer(blob);});
  expect(Array.from(new Uint8Array(buffer))).toEqual(Array.from(new TextEncoder().encode(raw)));
  await userEvent.selectOptions(screen.getByLabelText('Observation file format'),'csv');
  await userEvent.type(screen.getByLabelText('Dataset title'),'Old draft');
  rerender(<Experiments run={{...run,id:'c'.repeat(32)}} revision={0} busy={false} onImport={vi.fn()}/>);
  expect(screen.queryByText('Exact source')).not.toBeInTheDocument();
  expect(screen.getByLabelText('Observation file format')).toHaveValue('json');
});
