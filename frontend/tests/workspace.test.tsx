import { beforeEach, expect, test, vi } from 'vitest';
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EvidenceWorkspace from '@/components/EvidenceWorkspace';
import { researchApi } from '@/lib/research-api';
import type { ResearchRun } from '@/types/research';
vi.mock('@/lib/research-api', () => ({ researchApi: { list:vi.fn(), get:vi.fn(), search:vi.fn(), analyze:vi.fn(), upload:vi.fn() } }));
const run: ResearchRun = {schema_version:1,id:'a'.repeat(32),topic:'Navigation',plan:['Read sources'],candidates:[{id:'a',title:'Paper A',pdf_url:'https://arxiv.org/pdf/2401.12345',authors:[],summary:''},{id:'b',title:'Paper B',pdf_url:'',authors:[],summary:''}],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,issues:[],scope:'Literal support only'}};
beforeEach(() => {
  vi.resetAllMocks(); window.history.replaceState({}, '', '/');
  vi.mocked(researchApi.list).mockResolvedValue({items:[],total:0,page:1,page_size:10});
  vi.mocked(researchApi.search).mockResolvedValue(run);
  vi.mocked(researchApi.get).mockResolvedValue(run);
  vi.mocked(researchApi.analyze).mockResolvedValue(run);
  vi.mocked(researchApi.upload).mockResolvedValue(run);
});
async function search() { await userEvent.type(screen.getByLabelText('Research topic'), 'Navigation'); await userEvent.click(screen.getByRole('button',{name:'Find papers'})); await screen.findByLabelText('Select Paper A'); }
test('requires explicit selection and sends both checked IDs', async () => {
  render(<EvidenceWorkspace/>); await search();
  expect(researchApi.analyze).not.toHaveBeenCalled();
  expect(screen.getByRole('button',{name:'Analyze selected papers'})).toBeDisabled();
  await userEvent.click(screen.getByLabelText('Select Paper A')); await userEvent.click(screen.getByLabelText('Select Paper B'));
  await userEvent.click(screen.getByRole('button',{name:'Analyze selected papers'}));
  expect(researchApi.analyze).toHaveBeenCalledWith(run.id,['a','b']);
  expect(window.location.search).toBe(`?run=${run.id}`);
});
test('restores URL record and handles back navigation', async () => {
  window.history.replaceState({}, '', `/?run=${run.id}`); render(<EvidenceWorkspace/>);
  await screen.findByLabelText('Select Paper A'); expect(researchApi.get).toHaveBeenCalledWith(run.id);
  act(() => { window.history.replaceState({}, '', '/'); window.dispatchEvent(new PopStateEvent('popstate')); });
  await waitFor(() => expect(screen.queryByLabelText('Select Paper A')).not.toBeInTheDocument());
});
test('uploads into current record, keeps it on duplicate failure, and resets explicitly', async () => {
  render(<EvidenceWorkspace/>); await search();
  vi.mocked(researchApi.upload).mockRejectedValueOnce(new Error('Duplicate document'));
  await userEvent.upload(screen.getByLabelText('PDF file'),new File(['%PDF'], 'paper.pdf',{type:'application/pdf'}));
  await userEvent.click(screen.getByRole('button',{name:'Add PDF'}));
  await screen.findByText(/Duplicate document/); expect(researchApi.upload).toHaveBeenCalledWith(expect.any(File),run.id);
  expect(screen.getByLabelText('Select Paper A')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button',{name:'New record'}));
  expect(window.location.search).toBe(''); expect(screen.queryByLabelText('Select Paper A')).not.toBeInTheDocument();
});
test('shows empty search and no evidence without inventing results', async () => {
  vi.mocked(researchApi.search).mockResolvedValue({...run,candidates:[]}); render(<EvidenceWorkspace/>);
  await userEvent.type(screen.getByLabelText('Research topic'),'Empty'); await userEvent.click(screen.getByRole('button',{name:'Find papers'}));
  await screen.findByText(/No candidate papers found/); expect(screen.getByText(/No evidence extracted/)).toBeInTheDocument();
});
test('loads paginated history and refreshes manually', async () => {
  vi.mocked(researchApi.list).mockResolvedValue({items:[{id:run.id,topic:'Saved topic',candidate_count:2,selected_count:0,paper_count:0,updated_at:'2026-01-01',source_support_passed:false}],total:11,page:1,page_size:10});
  render(<EvidenceWorkspace/>); await screen.findByText('Saved topic');
  await userEvent.click(screen.getByRole('button',{name:'Next history page'})); expect(researchApi.list).toHaveBeenLastCalledWith(2);
  await userEvent.click(screen.getByRole('button',{name:'Refresh history'})); expect(researchApi.list).toHaveBeenLastCalledWith(2);
});
test('ignores an old record response after URL changes', async () => {
  let resolve!: (value: ResearchRun) => void;
  vi.mocked(researchApi.get).mockReturnValueOnce(new Promise(r => {resolve=r;}));
  window.history.replaceState({},'',`/?run=${run.id}`); render(<EvidenceWorkspace/>);
  await waitFor(()=>expect(researchApi.get).toHaveBeenCalled());
  act(()=>{ window.history.replaceState({},'','/'); window.dispatchEvent(new PopStateEvent('popstate')); });
  await act(async()=>resolve(run)); expect(screen.queryByLabelText('Select Paper A')).not.toBeInTheDocument();
});
test('links claims to quotes to page text and separates suggestions', async () => {
  const rich: ResearchRun = {...run,papers:[{document:{source:{id:'arxiv:2401.12345',title:'Source paper',kind:'paper',uri:'https://arxiv.org/pdf/2401.12345',sha256:'0'.repeat(64),collected_at:''},pages:[{number:2,text:'The full extracted page text.'}],total_pages:10,truncated:true},evidence:[{id:'arxiv:2401.12345:p2:e1',source_id:'arxiv:2401.12345',page:2,quote:'The exact supported quotation.'}],claims:[{id:'arxiv:2401.12345:c1',text:'A reported result',category:'result',claim_type:'paper_report',evidence_ids:['arxiv:2401.12345:p2:e1'],created_by:'extractor',timestamp:''}],missing_fields:['dataset'],extractor:'literal'}],generated_claims:[{id:'idea',text:'Try a new experiment',category:'future_work',claim_type:'suggestion',evidence_ids:['arxiv:2401.12345:p2:e1'],created_by:'composer',timestamp:''}],artifacts:[{kind:'literature_summary',title:'Summary',content:'A supported summary',claim_ids:['arxiv:2401.12345:c1'],evidence_ids:['arxiv:2401.12345:p2:e1']} ]};
  vi.mocked(researchApi.get).mockResolvedValue(rich); window.history.replaceState({},'',`/?run=${run.id}`); render(<EvidenceWorkspace/>);
  await screen.findByText('A reported result');
  for(const link of screen.getAllByRole('link',{name:/Evidence arxiv:/})) expect(document.getElementById(decodeURIComponent(link.getAttribute('href')!.slice(1)))).toBeInTheDocument();
  const claimLink=screen.getByRole('link',{name:'Claim arxiv:2401.12345:c1'}); expect(document.getElementById(decodeURIComponent(claimLink.getAttribute('href')!.slice(1)))).toHaveTextContent('A reported result');
  const pageLink=screen.getByRole('link',{name:'Extracted page 2'}); expect(document.getElementById(decodeURIComponent(pageLink.getAttribute('href')!.slice(1)))).toHaveTextContent('The full extracted page text.');
  expect(screen.getByRole('link',{name:'Open source PDF at page 2'})).toHaveAttribute('href','https://arxiv.org/pdf/2401.12345#page=2');
  expect(within(screen.getByRole('region',{name:'Research suggestions'})).getByText('Try a new experiment')).toBeInTheDocument();
  expect(screen.getByText(/Missing fields: dataset/)).toBeInTheDocument(); expect(screen.getByText(/Truncated/)).toBeInTheDocument();
});
test('disables mutations during analysis and ignores completion after navigation',async()=>{
  let resolve!: (value: ResearchRun)=>void;
  vi.mocked(researchApi.analyze).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  render(<EvidenceWorkspace/>);await search();await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.click(screen.getByRole('button',{name:'Analyze selected papers'}));
  expect(screen.getByRole('button',{name:'Find papers'})).toBeDisabled();expect(screen.getByRole('button',{name:'New record'})).toBeDisabled();
  act(()=>{window.history.replaceState({},'','/');window.dispatchEvent(new PopStateEvent('popstate'));});
  await act(async()=>resolve(run));
  expect(screen.queryByLabelText('Select Paper A')).not.toBeInTheDocument();expect(window.location.search).toBe('');
});
test('failed analysis preserves candidates and shows no success',async()=>{
  vi.mocked(researchApi.analyze).mockRejectedValueOnce(new Error('Request timed out. The server may still be processing this operation.'));
  render(<EvidenceWorkspace/>);await search();await userEvent.click(screen.getByLabelText('Select Paper A'));await userEvent.click(screen.getByRole('button',{name:'Analyze selected papers'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Request timed out');expect(screen.getByLabelText('Select Paper A')).toBeChecked();expect(researchApi.analyze).toHaveBeenCalledTimes(1);
});


test.each(['restored','created'])('hash navigation preserves unsaved state in a %s record without fetching again',async(mode)=>{
  if(mode==='restored') window.history.replaceState({},'',`/?run=${run.id}`);
  render(<EvidenceWorkspace/>);
  if(mode==='created') await search(); else await screen.findByLabelText('Select Paper A');
  await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.clear(screen.getByLabelText('Research topic'));
  await userEvent.type(screen.getByLabelText('Research topic'),'Unsaved topic');
  const file=new File(['%PDF'],'pending.pdf',{type:'application/pdf'});
  await userEvent.upload(screen.getByLabelText('PDF file'),file);
  const fetches=vi.mocked(researchApi.get).mock.calls.length;
  for(const hash of ['#research-evidence-arxiv%3A2401.12345%3Ap2%3Ae1','']) {
    await act(async()=>{window.history.replaceState({},'',`/?run=${run.id}${hash}`);window.dispatchEvent(new PopStateEvent('popstate'));});
    expect(screen.getByLabelText('Select Paper A')).toBeChecked();
    expect(screen.getByLabelText('Research topic')).toHaveValue('Unsaved topic');
    expect((screen.getByLabelText('PDF file') as HTMLInputElement).files?.[0]).toBe(file);
    expect(researchApi.get).toHaveBeenCalledTimes(fetches);
  }
});
