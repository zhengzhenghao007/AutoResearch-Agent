import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ScreeningReport from '@/components/ScreeningReport';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{screeningReport:vi.fn()}}));
const id='a'.repeat(32);
const empty={schema_version:1 as const,run_id:id,topic:'Test',counts:{total:0,include:0,exclude:0,undecided:0,selected:0},items:[],scope:'User annotations only.'};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(researchApi.screeningReport).mockResolvedValue(empty);});
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();});
test('loads on demand and downloads the exact saved report',async()=>{
  const create=vi.fn().mockReturnValue('blob:test');vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:create,revokeObjectURL:vi.fn()}));
  let name='';vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){name=this.download;});
  render(<ScreeningReport runId={id} revision={0}/>);
  expect(researchApi.screeningReport).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Load screening report'}));
  expect(await screen.findByText('No candidates in this saved record.')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button',{name:'Download screening JSON'}));
  expect(name).toBe(`screening-${id}.json`);
  const blob=create.mock.calls[0][0] as Blob;
  expect(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsText(blob);})).toBe(JSON.stringify(empty,null,2)+'\n');
});
test('shows decision history and independent saved selection',async()=>{
  const event={candidate_id:'x',decision:'exclude' as const,reason:'Outside scope',decided_at:'2026-10-12T00:00:00Z'};
  vi.mocked(researchApi.screeningReport).mockResolvedValue({...empty,counts:{total:1,include:0,exclude:1,undecided:0,selected:1},items:[{candidate:{id:'x',title:'Example',authors:[],summary:'',pdf_url:'javascript:alert(1)'},status:'exclude',selected_for_analysis:true,latest:event,history:[event],selection_notice:'excluded_but_selected'}]});
  render(<ScreeningReport runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load screening report'}));
  expect(await screen.findByText('Excluded but selected for analysis.')).toBeInTheDocument();
  expect(screen.getByText(/Outside scope/)).toBeInTheDocument();expect(screen.queryAllByRole('link')).toHaveLength(0);
});
test.each(['record','revision'])('ignores late responses after changing %s',async(kind)=>{
  let resolve!:(r:typeof empty)=>void;vi.mocked(researchApi.screeningReport).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  const {rerender}=render(<ScreeningReport runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load screening report'}));
  rerender(<ScreeningReport runId={kind==='record'?'b'.repeat(32):id} revision={kind==='revision'?1:0}/>);await act(async()=>resolve(empty));
  expect(screen.queryByRole('button',{name:'Download screening JSON'})).not.toBeInTheDocument();
});
test('rejects a mismatched run and permits manual retry',async()=>{
  vi.mocked(researchApi.screeningReport).mockResolvedValueOnce({...empty,run_id:'wrong'});
  render(<ScreeningReport runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load screening report'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('different research record');
  await userEvent.click(screen.getByRole('button',{name:'Load screening report'}));expect(await screen.findByText('No candidates in this saved record.')).toBeInTheDocument();
});
