import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ClaimReview from '@/components/ClaimReview';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{claimReview:vi.fn()}}));
const id='a'.repeat(32);
const empty={schema_version:1 as const,run_id:id,rule_version:'planning-language-en-v1' as const,claim_count:0,checked_claim_count:0,flagged_claim_count:0,flags:[],semantic_validation:'not_assessed' as const,scope:'Advisory only.'};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(researchApi.claimReview).mockResolvedValue(empty);});
test('displays flagged text, matched phrase and all source evidence safely',async()=>{
  vi.mocked(researchApi.claimReview).mockResolvedValue({...empty,claim_count:1,checked_claim_count:1,flagged_claim_count:1,flags:[{code:'planning_language_in_observation',claim_id:'c',source_id:'s',category:'experiment',claim_text:'We will evaluate <script>alert(1)</script>.',matched_text:'We will evaluate',message:'Inspect the full context.',evidence:[{id:'e1',source_id:'s',page:2,quote:'First original quotation.'},{id:'e2',source_id:'s',page:3,quote:'Second original quotation.'}]}]});
  render(<ClaimReview runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load claim review'}));
  expect(await screen.findByText('Inspect the full context.')).toBeInTheDocument();
  expect(screen.getByText('Source s · Page 2 · Evidence e1')).toBeInTheDocument();
  expect(screen.getByText('Second original quotation.')).toBeInTheDocument();
  expect(screen.getByText('We will evaluate <script>alert(1)</script>.')).toBeInTheDocument();
  expect(document.querySelector('script')).toBeNull();
});
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();});
test('loads on demand and downloads the exact saved report',async()=>{
  const create=vi.fn().mockReturnValue('blob:test');vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:create,revokeObjectURL:vi.fn()}));
  let name='';vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){name=this.download;});
  render(<ClaimReview runId={id} revision={0}/>);
  expect(researchApi.claimReview).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Load claim review'}));
  expect(await screen.findByText('No planning-language flags found. This is not semantic approval.')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button',{name:'Download claim review JSON'}));
  expect(name).toBe(`claim-review-${id}.json`);
  const blob=create.mock.calls[0][0] as Blob;
  expect(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsText(blob);})).toBe(JSON.stringify(empty,null,2)+'\n');
});
test.each(['record','revision'])('ignores late responses after changing %s',async(kind)=>{
  let resolve!:(r:typeof empty)=>void;vi.mocked(researchApi.claimReview).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  const {rerender}=render(<ClaimReview runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load claim review'}));
  rerender(<ClaimReview runId={kind==='record'?'b'.repeat(32):id} revision={kind==='revision'?1:0}/>);await act(async()=>resolve(empty));
  expect(screen.queryByRole('button',{name:'Download claim review JSON'})).not.toBeInTheDocument();
});
test('rejects a mismatched run and permits manual retry',async()=>{
  vi.mocked(researchApi.claimReview).mockResolvedValueOnce({...empty,run_id:'wrong'});
  render(<ClaimReview runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load claim review'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('different research record');
  await userEvent.click(screen.getByRole('button',{name:'Load claim review'}));expect(await screen.findByText('No planning-language flags found. This is not semantic approval.')).toBeInTheDocument();
});
