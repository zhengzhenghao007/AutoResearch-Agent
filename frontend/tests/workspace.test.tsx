import { beforeEach, expect, test, vi } from 'vitest';
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EvidenceWorkspace from '@/components/EvidenceWorkspace';
import { researchApi } from '@/lib/research-api';
import type { ResearchRun } from '@/types/research';
vi.mock('@/lib/research-api', () => ({ researchApi: { manuscript:vi.fn(), list:vi.fn(), get:vi.fn(), search:vi.fn(), analyze:vi.fn(), upload:vi.fn(), citations:vi.fn(), bibtex:vi.fn(), candidateDecision:vi.fn(), sourceIdentities:vi.fn(), sourceIdentity:vi.fn(), sourceDuplicates:vi.fn(), screeningReport:vi.fn(), claimReview:vi.fn() } }));
const run: ResearchRun = {schema_version:1,id:'a'.repeat(32),topic:'Navigation',plan:['Read sources'],candidates:[{id:'a',title:'Paper A',pdf_url:'https://arxiv.org/pdf/2401.12345',authors:[],summary:''},{id:'b',title:'Paper B',pdf_url:'',authors:[],summary:''}],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,issues:[],scope:'Literal support only'}};
beforeEach(() => {
  vi.resetAllMocks(); vi.mocked(researchApi.manuscript).mockResolvedValue({run_id:run.id,current_input_sha256:'hash',revisions:[],reviews:[],approvals:[]}); window.history.replaceState({}, '', '/');
  vi.mocked(researchApi.list).mockResolvedValue({items:[],total:0,page:1,page_size:10});
  vi.mocked(researchApi.search).mockResolvedValue(run);
  vi.mocked(researchApi.get).mockResolvedValue(run);
  vi.mocked(researchApi.analyze).mockResolvedValue(run);
  vi.mocked(researchApi.upload).mockResolvedValue(run);
});
async function search() { await userEvent.type(screen.getByLabelText('Research topic'), 'Navigation'); await userEvent.click(screen.getByRole('button',{name:'Find papers'})); await screen.findByLabelText('Select Paper A'); await userEvent.click(screen.getByText('Library tools: references, duplicates and screening')); for(const summary of screen.getAllByText('Screening decision',{selector:'summary'})) await userEvent.click(summary); }
function screening() { return within(screen.getByRole('group',{name:'Screening for Paper A'})); }
test('failed analysis preserves the unfinished screening draft',async()=>{
  render(<EvidenceWorkspace/>);await search();
  await userEvent.type(screening().getByLabelText('Screening reason'),'Draft reason');
  await userEvent.selectOptions(screening().getByLabelText('Screening decision'),'exclude');
  await userEvent.click(screen.getByLabelText('Select Paper A'));
  vi.mocked(researchApi.analyze).mockRejectedValueOnce(new Error('Analysis unavailable'));
  await userEvent.click(screen.getByRole('button',{name:'Analyze selected papers'}));
  await screen.findByText('Analysis unavailable');
  expect(screening().getByLabelText('Screening reason')).toHaveValue('Draft reason');
  expect(screening().getByLabelText('Screening decision')).toHaveValue('exclude');
});
async function recordReason(reason='Relevant protocol') {
  await userEvent.type(screening().getByLabelText('Screening reason'),reason);
  await userEvent.click(screening().getByRole('button',{name:'Record screening decision'}));
}
test('screening preserves unsaved selection and ordered revisions and clears exports',async()=>{
  render(<EvidenceWorkspace/>); await search();
  expect(screening().getByText('No screening annotation.')).toBeInTheDocument();
  vi.mocked(researchApi.citations).mockResolvedValue({schema_version:1,run_id:run.id,topic:run.topic,sources:[]});
  await userEvent.click(screen.getByRole('button',{name:'Load citation JSON'}));
  await screen.findByRole('button',{name:'Download citation JSON'});
  const first={candidate_id:'a',decision:'include' as const,reason:'Relevant protocol',decided_at:'2026-09-28T01:00:00Z'};
  vi.mocked(researchApi.candidateDecision).mockResolvedValueOnce({...run,candidate_decisions:[first]});
  await recordReason();
  expect(researchApi.candidateDecision).toHaveBeenCalledWith(run.id,{candidate_id:'a',decision:'include',reason:'Relevant protocol'});
  expect(screen.getByLabelText('Select Paper A')).not.toBeChecked();
  expect(screen.queryByRole('button',{name:'Download citation JSON'})).not.toBeInTheDocument();
  await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.selectOptions(screening().getByLabelText('Screening decision'),'exclude');
  vi.mocked(researchApi.candidateDecision).mockResolvedValueOnce({...run,candidate_decisions:[first,{...first,decision:'exclude',reason:'Different protocol'}]});
  await recordReason('Different protocol');
  expect(screen.getByLabelText('Select Paper A')).toBeChecked();
  await userEvent.click(screening().getByText('Screening history (2)'));
  const entries=screening().getAllByRole('listitem');
  expect(entries[0]).toHaveTextContent('Relevant protocol'); expect(entries[1]).toHaveTextContent('Different protocol');
  await userEvent.click(screen.getByRole('button',{name:'Analyze selected papers'}));
  expect(researchApi.analyze).toHaveBeenCalledWith(run.id,['a']);
});
test('screening failure preserves input without optimistic history or retries',async()=>{
  render(<EvidenceWorkspace/>); await search(); await userEvent.click(screen.getByLabelText('Select Paper A'));
  vi.mocked(researchApi.candidateDecision).mockRejectedValueOnce(new Error('Connection lost. Reopen the record to check its state.'));
  await recordReason('  <b>Unverified</b>  ');
  expect(screening().getByRole('alert')).toHaveTextContent('Connection lost');
  expect(screening().getByLabelText('Screening reason')).toHaveValue('  <b>Unverified</b>  ');
  expect(screen.getByLabelText('Select Paper A')).toBeChecked();
  expect(screening().getByText('No screening annotation.')).toBeInTheDocument();
  expect(researchApi.candidateDecision).toHaveBeenCalledTimes(1);
});
test('screening serializes writes and ignores completion after navigation',async()=>{
  let resolve!: (value: ResearchRun)=>void;
  vi.mocked(researchApi.candidateDecision).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  render(<EvidenceWorkspace/>); await search(); await recordReason();
  expect(screen.getByRole('button',{name:'Find papers'})).toBeDisabled();
  expect(screen.getByRole('button',{name:'New record'})).toBeDisabled();
  expect(within(screen.getByRole('group',{name:'Screening for Paper B'})).getByLabelText('Screening reason')).toBeDisabled();
  const other={...run,id:'b'.repeat(32),topic:'Different record'};
  vi.mocked(researchApi.get).mockResolvedValueOnce(other);
  await act(async()=>{window.history.replaceState({},'',`/?run=${other.id}`);window.dispatchEvent(new PopStateEvent('popstate'));});
  await screen.findByRole('heading',{name:'Different record'});
  await act(async()=>resolve({...run,candidate_decisions:[{candidate_id:'a',decision:'include',reason:'Stale',decided_at:''}]}));
  expect(screen.getByRole('heading',{name:'Different record'})).toBeInTheDocument();
  expect(screen.queryByText('Stale')).not.toBeInTheDocument();
});
test('exports exist only for a current run and reset after same-run analysis',async()=>{
  vi.mocked(researchApi.citations).mockResolvedValue({schema_version:1,run_id:run.id,topic:run.topic,sources:[]});
  render(<EvidenceWorkspace/>);
  expect(screen.queryByRole('region',{name:'Research exports'})).not.toBeInTheDocument();
  await search();
  await userEvent.click(screen.getByRole('button',{name:'Load citation JSON'}));
  await screen.findByRole('button',{name:'Download citation JSON'});
  expect(screen.getByRole('button',{name:'Find papers'})).toBeEnabled();
  await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.click(screen.getByRole('button',{name:'Analyze selected papers'}));
  await screen.findByRole('button',{name:'Load citation JSON'});
  expect(screen.queryByRole('button',{name:'Download citation JSON'})).not.toBeInTheDocument();
});
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
  await screen.findAllByText('A reported result');
  await userEvent.click(screen.getByRole('button',{name:'Reading & evidence'}));
  expect(screen.getByText('The exact supported quotation.')).toBeVisible();
  expect(screen.getByLabelText('Extracted page 2')).toHaveTextContent('The full extracted page text.');
  expect(screen.getByRole('link',{name:'Open source PDF at page 2'})).toHaveAttribute('href','https://arxiv.org/pdf/2401.12345#page=2');
  expect(screen.getByText('Truncated document')).toBeVisible();
  await userEvent.click(screen.getByRole('button',{name:'Compare'}));
  await userEvent.click(screen.getByText('Exploratory suggestions'));
  expect(screen.getByText('Try a new experiment')).toBeVisible();
  await userEvent.click(screen.getByRole('button',{name:'Read evidence'}));
  expect(screen.getByText('The exact supported quotation.')).toBeVisible();
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

test('DOI and screening saves preserve each other drafts and unsaved workspace inputs',async()=>{
  const source={id:'s',title:'Source A',uri:'upload:test',sha256:'0'.repeat(64)};
  vi.mocked(researchApi.sourceIdentities).mockResolvedValue({run_id:run.id,sources:[{source,active:true,doi:null,provenance:null}],conflicts:[]});
  vi.mocked(researchApi.sourceIdentity).mockResolvedValue(run);
  vi.mocked(researchApi.candidateDecision).mockResolvedValue(run);
  render(<EvidenceWorkspace/>);await search();await userEvent.click(screen.getByRole('button',{name:'Load DOI annotations'}));
  await screen.findByLabelText('DOI reason');
  await userEvent.type(screen.getByLabelText('DOI'),'10.1234/test');await userEvent.type(screen.getByLabelText('DOI reason'),'Unsent DOI reason');
  await recordReason();
  await waitFor(()=>expect(screen.getByLabelText('DOI reason')).toBeEnabled());
  expect(screen.getByLabelText('DOI reason')).toHaveValue('Unsent DOI reason');
  await userEvent.type(screening().getByLabelText('Screening reason'),'Unsent screening');
  await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.clear(screen.getByLabelText('Research topic'));await userEvent.type(screen.getByLabelText('Research topic'),'Unsent topic');
  const file=new File(['%PDF'],'unsent.pdf',{type:'application/pdf'});await userEvent.upload(screen.getByLabelText('PDF file'),file);
  await userEvent.click(screen.getByRole('button',{name:'Record DOI annotation'}));
  await waitFor(()=>expect(screen.getByLabelText('DOI reason')).toBeEnabled());
  expect(screen.getByLabelText('DOI reason')).toHaveValue('');
  expect(screening().getByLabelText('Screening reason')).toHaveValue('Unsent screening');
  expect(screen.getByLabelText('Select Paper A')).toBeChecked();expect(screen.getByLabelText('Research topic')).toHaveValue('Unsent topic');
  expect((screen.getByLabelText('PDF file') as HTMLInputElement).files?.[0]).toBe(file);
});
test('late DOI writes cannot replace a newly opened record',async()=>{
  let resolve!:(value:ResearchRun)=>void;
  vi.mocked(researchApi.sourceIdentity).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  vi.mocked(researchApi.sourceIdentities).mockResolvedValue({run_id:run.id,sources:[{source:{id:'s',title:'Source A',uri:'upload:test',sha256:'0'.repeat(64)},active:true,doi:null,provenance:null}],conflicts:[]});
  render(<EvidenceWorkspace/>);await search();await userEvent.click(screen.getByRole('button',{name:'Load DOI annotations'}));await screen.findByLabelText('DOI');
  await userEvent.type(screen.getByLabelText('DOI'),'10.1234/test');await userEvent.type(screen.getByLabelText('DOI reason'),'Test');await userEvent.click(screen.getByRole('button',{name:'Record DOI annotation'}));
  expect(screen.getByRole('button',{name:'Find papers'})).toBeDisabled();expect(screening().getByLabelText('Screening reason')).toBeDisabled();
  const other={...run,id:'b'.repeat(32),topic:'Other record'};vi.mocked(researchApi.get).mockResolvedValueOnce(other);
  await act(async()=>{window.history.replaceState({},'',`/?run=${other.id}`);window.dispatchEvent(new PopStateEvent('popstate'));});await screen.findByRole('heading',{name:'Other record'});
  await act(async()=>resolve(run));expect(screen.getByRole('heading',{name:'Other record'})).toBeInTheDocument();expect(screen.queryByLabelText('DOI reason')).not.toBeInTheDocument();
});

test('duplicate report preserves inputs and is discarded as soon as an annotation write starts',async()=>{
  vi.mocked(researchApi.sourceDuplicates).mockResolvedValue({schema_version:1,run_id:run.id,groups:[],candidate_source_links:[]});
  let reject!:(error:Error)=>void;vi.mocked(researchApi.candidateDecision).mockReturnValueOnce(new Promise((_resolve,r)=>{reject=r;}));
  render(<EvidenceWorkspace/>);await search();await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.type(screening().getByLabelText('Screening reason'),'Pending reason');
  await userEvent.click(screen.getByRole('button',{name:'Load duplicate clues'}));await screen.findByRole('button',{name:'Download duplicate clues JSON'});
  expect(screen.getByLabelText('Select Paper A')).toBeChecked();expect(screening().getByLabelText('Screening reason')).toHaveValue('Pending reason');
  await userEvent.click(screening().getByRole('button',{name:'Record screening decision'}));
  expect(screen.queryByRole('region',{name:'Duplicate clues'})).not.toBeInTheDocument();
  await act(async()=>reject(new Error('Connection lost')));
  await screen.findByRole('button',{name:'Load duplicate clues'});
  expect(screen.queryByRole('button',{name:'Download duplicate clues JSON'})).not.toBeInTheDocument();
  expect(screening().getByLabelText('Screening reason')).toHaveValue('Pending reason');
});

test('screening report preserves inputs and is discarded as soon as an annotation write starts',async()=>{
  vi.mocked(researchApi.screeningReport).mockResolvedValue({schema_version:1,run_id:run.id,topic:run.topic,counts:{total:0,include:0,exclude:0,undecided:0,selected:0},items:[],scope:'Annotations only'});
  let reject!:(error:Error)=>void;vi.mocked(researchApi.candidateDecision).mockReturnValueOnce(new Promise((_resolve,r)=>{reject=r;}));
  render(<EvidenceWorkspace/>);await search();await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.type(screening().getByLabelText('Screening reason'),'Pending reason');
  await userEvent.click(screen.getByRole('button',{name:'Load screening report'}));await screen.findByRole('button',{name:'Download screening JSON'});
  expect(screen.getByLabelText('Select Paper A')).toBeChecked();expect(screening().getByLabelText('Screening reason')).toHaveValue('Pending reason');
  await userEvent.click(screening().getByRole('button',{name:'Record screening decision'}));
  expect(screen.queryByRole('region',{name:'Screening audit report'})).not.toBeInTheDocument();
  await act(async()=>reject(new Error('Connection lost')));
  await screen.findByRole('button',{name:'Load screening report'});
  expect(screen.queryByRole('button',{name:'Download screening JSON'})).not.toBeInTheDocument();
  expect(screening().getByLabelText('Screening reason')).toHaveValue('Pending reason');
});

test('claim review preserves inputs and is discarded as soon as an annotation write starts',async()=>{
  vi.mocked(researchApi.claimReview).mockResolvedValue({schema_version:1,run_id:run.id,rule_version:'planning-language-en-v1',claim_count:0,checked_claim_count:0,flagged_claim_count:0,flags:[],semantic_validation:'not_assessed',scope:'Advisory only'});
  let reject!:(error:Error)=>void;vi.mocked(researchApi.candidateDecision).mockReturnValueOnce(new Promise((_resolve,r)=>{reject=r;}));
  render(<EvidenceWorkspace/>);await search();await userEvent.click(screen.getByLabelText('Select Paper A'));
  await userEvent.type(screening().getByLabelText('Screening reason'),'Pending reason');
  await userEvent.click(screen.getByRole('button',{name:'Reading & evidence'}));
  await userEvent.click(screen.getByText('Advanced review: source checks and claim categories'));
  await userEvent.click(screen.getByRole('button',{name:'Load claim review'}));await screen.findByRole('button',{name:'Download claim review JSON'});
  await userEvent.click(screen.getByRole('button',{name:'Library'}));
  expect(screen.getByLabelText('Select Paper A')).toBeChecked();expect(screening().getByLabelText('Screening reason')).toHaveValue('Pending reason');
  await userEvent.click(screen.getByRole('button',{name:'Library'}));
  await userEvent.click(screening().getByRole('button',{name:'Record screening decision'}));
  expect(screen.queryByRole('region',{name:'Claim classification review'})).not.toBeInTheDocument();
  await act(async()=>reject(new Error('Connection lost')));
  await userEvent.click(screen.getByRole('button',{name:'Reading & evidence'}));
  await screen.findByRole('button',{name:'Load claim review'});
  expect(screen.queryByRole('button',{name:'Download claim review JSON'})).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button',{name:'Library'}));
  expect(screening().getByLabelText('Screening reason')).toHaveValue('Pending reason');
});
