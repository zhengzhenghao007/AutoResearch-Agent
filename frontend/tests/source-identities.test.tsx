import {beforeEach,expect,test,vi} from 'vitest';
import {act,render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SourceIdentities from '@/components/SourceIdentities';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{sourceIdentities:vi.fn(),get:vi.fn()}}));
const run:ResearchRun={schema_version:1,id:'a'.repeat(32),topic:'Test',plan:[],candidates:[],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,issues:[],scope:''}};
const source={id:'source',title:'Source A',uri:'upload:example',sha256:'0'.repeat(64)};
const view={run_id:run.id,sources:[{source,active:true,doi:null,provenance:null}],conflicts:[]};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(researchApi.get).mockResolvedValue(run);researchApi.sourceIdentities=vi.fn().mockResolvedValue(view);});
async function load(){await userEvent.click(screen.getByRole('button',{name:'Load DOI annotations'}));await screen.findByRole('group',{name:'DOI for Source A'});}
test('set and clear send only explicit inputs and failures preserve drafts',async()=>{
  const save=vi.fn().mockRejectedValueOnce(new Error('Unsupported DOI syntax')).mockResolvedValue(true);
  render(<SourceIdentities run={run} revision={1} busy={false} onRecord={save}/>);await load();
  await userEvent.type(screen.getByLabelText('DOI'),'10.1234/test');await userEvent.type(screen.getByLabelText('DOI reason'),'Printed in paper');
  await userEvent.click(screen.getByRole('button',{name:'Record DOI annotation'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Unsupported DOI syntax');
  expect(screen.getByLabelText('DOI')).toHaveValue('10.1234/test');expect(save).toHaveBeenCalledTimes(1);
  await userEvent.selectOptions(screen.getByLabelText('DOI action'),'clear');
  await userEvent.click(screen.getByRole('button',{name:'Record DOI annotation'}));
  expect(save).toHaveBeenLastCalledWith({source_id:'source',action:'clear',reason:'Printed in paper'});
});
test('inactive history is read only and duplicate notices keep distinct sources',async()=>{
  const past={...source,id:'old',title:'Historical source'};
  const annotated={...run,source_identity_annotations:[{source_id:'old',action:'clear' as const,doi:null,reason:'Wrong association',source:past,provenance:'user_supplied' as const,recorded_at:'2026-09-28T00:00:00Z'}]};
  vi.mocked(researchApi.sourceIdentities).mockResolvedValue({run_id:run.id,sources:[{source,active:true,doi:'10.1234/test',provenance:'user_supplied'},{source:{...source,id:'two',title:'Source B'},active:true,doi:'10.1234/test',provenance:'user_supplied'},{source:past,active:false,doi:null,provenance:null}],conflicts:[{doi:'10.1234/test',source_ids:['source','two']}]});
  vi.mocked(researchApi.get).mockResolvedValue(annotated);
  render(<SourceIdentities run={annotated} revision={1} busy={false} onRecord={vi.fn()}/>);await load();
  expect(screen.getByText(/Sources remain separate/)).toBeInTheDocument();
  const old=within(screen.getByRole('group',{name:'DOI for Historical source'}));
  expect(old.queryByRole('button')).not.toBeInTheDocument();expect(old.getByText(/Cleared DOI/)).toBeInTheDocument();
});
test('refresh preserves drafts but rejects an old read after a mutation starts',async()=>{
  let resolve!:(value:typeof view)=>void;
  const save=vi.fn();const rendered=render(<SourceIdentities run={run} revision={1} busy={false} onRecord={save}/>);await load();
  await userEvent.type(screen.getByLabelText('DOI reason'),'Unsent draft');
  vi.mocked(researchApi.sourceIdentities).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  await userEvent.click(screen.getByRole('button',{name:'Refresh DOI annotations'}));
  rendered.rerender(<SourceIdentities run={run} revision={1} busy={true} onRecord={save}/>);
  await act(async()=>resolve({...view,sources:[]}));
  rendered.rerender(<SourceIdentities run={run} revision={2} busy={false} onRecord={save}/>);
  await screen.findByLabelText('DOI reason');expect(screen.getByLabelText('DOI reason')).toHaveValue('Unsent draft');
});

test('obsolete reads are ignored when the record panel is replaced',async()=>{
  let resolve!:(value:typeof view)=>void;vi.mocked(researchApi.sourceIdentities).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  const rendered=render(<SourceIdentities key={run.id} run={run} revision={1} busy={false} onRecord={vi.fn()}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load DOI annotations'}));
  rendered.rerender(<SourceIdentities key="other" run={{...run,id:'b'.repeat(32)}} revision={1} busy={false} onRecord={vi.fn()}/>);
  await act(async()=>resolve(view));expect(screen.queryByRole('group',{name:'DOI for Source A'})).not.toBeInTheDocument();
});

test('manual refresh loads externally added reason history with the current DOI',async()=>{
  render(<SourceIdentities run={run} revision={1} busy={false} onRecord={vi.fn()}/>);await load();
  vi.mocked(researchApi.get).mockResolvedValue({...run,source_identity_annotations:[{source_id:source.id,action:'set',doi:'10.1234/external',reason:'Added through CLI',source,provenance:'user_supplied',recorded_at:'2026-09-28T00:00:00Z'}]});
  vi.mocked(researchApi.sourceIdentities).mockResolvedValue({...view,sources:[{source,active:true,doi:'10.1234/external',provenance:'user_supplied'}]});
  await userEvent.click(screen.getByRole('button',{name:'Refresh DOI annotations'}));
  expect(await screen.findByText(/Added through CLI/)).toBeInTheDocument();
});
