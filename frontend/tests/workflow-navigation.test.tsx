import {beforeEach,expect,test,vi} from 'vitest';
import {act,render,screen,within,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EvidenceWorkspace from '@/components/EvidenceWorkspace';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{list:vi.fn(),get:vi.fn()}}));
vi.mock('@/components/ManuscriptEditor',()=>({default:({onBusyChange}:{onBusyChange?:(value:boolean)=>void})=> <><label>Draft text<textarea onChange={()=>onBusyChange?.(true)}/></label><button onClick={()=>onBusyChange?.(false)}>Release draft lock</button></>}));
const record:ResearchRun={schema_version:1,id:'a'.repeat(32),topic:'Example study',plan:[],candidates:[],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,scope:'Literal only',issues:[]}};
beforeEach(()=>{vi.resetAllMocks();window.history.replaceState({},'',`/?run=${record.id}`);vi.mocked(researchApi.list).mockResolvedValue({items:[],total:0,page:1,page_size:10});vi.mocked(researchApi.get).mockResolvedValue(record);});
test('four stages preserve unsaved writing and hide unrelated controls',async()=>{
 render(<EvidenceWorkspace/>);
 await screen.findByRole('heading',{name:'Example study'});
 const nav=screen.getByRole('navigation',{name:'Research workflow'});
 expect(within(nav).getAllByRole('button')).toHaveLength(4);
 expect(screen.getByLabelText('Research topic')).toBeVisible();
 await userEvent.click(within(nav).getByRole('button',{name:'Writing'}));
 expect(screen.getByLabelText('Research topic')).not.toBeVisible();
 await userEvent.type(screen.getByLabelText('Draft text'),'Keep this unsaved paragraph');
 await userEvent.click(within(nav).getByRole('button',{name:'Compare'}));
 expect(screen.getByLabelText('Draft text')).not.toBeVisible();
 await userEvent.click(within(nav).getByRole('button',{name:'Writing'}));
 expect(screen.getByLabelText('Draft text')).toHaveValue('Keep this unsaved paragraph');
});

test('opens the selected paper even without extracts and allows reading unquoted pages',async()=>{
 const paper=(id:string,title:string)=>({document:{source:{id,title,kind:'paper' as const,uri:`upload:${title}`,sha256:'0'.repeat(64),collected_at:''},pages:[{number:1,text:'Opening page'},{number:2,text:'Important material omitted by the extractor.'}],total_pages:2,truncated:false},claims:[],evidence:[],missing_fields:[],extractor:'literal-rule-v1'});
 vi.mocked(researchApi.get).mockResolvedValue({...record,papers:[paper('a','First paper'),paper('b','Second paper')]});
 render(<EvidenceWorkspace/>);
 const buttons=await screen.findAllByRole('button',{name:'Read paper'});
 await userEvent.click(buttons[1]);
 expect(screen.getByLabelText('Paper')).toHaveValue('b');
 await userEvent.selectOptions(screen.getByLabelText('Source page'),'2');
 expect(screen.getByLabelText('Extracted page 2')).toHaveTextContent('Important material omitted by the extractor.');
});

test('restores a writing deep link and same-record back navigation without refetching',async()=>{
 window.history.replaceState({},'',`/?run=${record.id}&stage=writing`);
 render(<EvidenceWorkspace/>);
 const draft=await screen.findByLabelText('Draft text');
 expect(draft).toBeVisible();
 await userEvent.type(draft,'Keep my work');
 const nav=within(screen.getByRole('navigation',{name:'Research workflow'}));
 await userEvent.click(nav.getByRole('button',{name:'Compare'}));
 expect(new URL(window.location.href).searchParams.get('stage')).toBe('compare');
 act(()=>{window.history.replaceState({},'',`/?run=${record.id}&stage=writing`);window.dispatchEvent(new PopStateEvent('popstate'));});
 expect(draft).toBeVisible();expect(draft).toHaveValue('Keep my work');
 expect(researchApi.get).toHaveBeenCalledTimes(1);
});

test('browser navigation cannot silently discard a dirty manuscript',async()=>{
 window.history.replaceState({},'',`/?run=${record.id}&stage=writing`);
 render(<EvidenceWorkspace/>);
 const draft=await screen.findByLabelText('Draft text');await userEvent.type(draft,'Unsaved');
 act(()=>{window.history.replaceState({},'','/');window.dispatchEvent(new PopStateEvent('popstate'));});
 expect(draft).toBeVisible();expect(draft).toHaveValue('Unsaved');
 expect(new URL(window.location.href).searchParams.get('run')).toBe(record.id);
 expect(screen.getByRole('alert')).toHaveTextContent('Save or discard');
});

test('stage changes during a slow record load keep the URL consistent',async()=>{
 let resolve!:(value:ResearchRun)=>void;
 vi.mocked(researchApi.get).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
 window.history.replaceState({},'',`/?run=${record.id}&stage=writing`);
 render(<EvidenceWorkspace/>);await screen.findByText('Opening research record…');
 await userEvent.click(screen.getByRole('button',{name:'Library'}));
 await act(async()=>resolve(record));
 expect(new URL(window.location.href).searchParams.get('stage')).toBeNull();
 expect(screen.getByLabelText('Research topic')).toBeVisible();
});

test('blocked browser Back preserves the previous record for navigation after saving',async()=>{
 const other={...record,id:'b'.repeat(32),topic:'Other study'};
 vi.mocked(researchApi.list).mockResolvedValue({items:[{id:other.id,topic:other.topic,candidate_count:0,selected_count:0,paper_count:0,updated_at:'',source_support_passed:false}],total:1,page:1,page_size:10});
 vi.mocked(researchApi.get).mockImplementation(async id=>id===other.id?other:record);
 render(<EvidenceWorkspace/>);await screen.findByRole('heading',{name:record.topic});
 await userEvent.click(screen.getByRole('button',{name:/Other study/}));
 await screen.findByRole('heading',{name:other.topic});
 await userEvent.click(screen.getByRole('button',{name:'Writing'}));
 await userEvent.type(await screen.findByLabelText('Draft text'),'Retain this');
 act(()=>window.history.back());
 await waitFor(()=>expect(screen.getByRole('button',{name:'Library'})).toHaveAttribute('aria-current','step'));
 act(()=>window.history.back());
 await screen.findByRole('alert');
 await waitFor(()=>expect(new URL(window.location.href).searchParams.get('run')).toBe(other.id));
 await userEvent.click(screen.getByRole('button',{name:'Writing'}));
 expect(screen.getByLabelText('Draft text')).toHaveValue('Retain this');
 await userEvent.click(screen.getByRole('button',{name:'Release draft lock'}));
 act(()=>window.history.back());
 await waitFor(()=>expect(screen.getByRole('button',{name:'Library'})).toHaveAttribute('aria-current','step'));
 act(()=>window.history.back());
 await screen.findByRole('heading',{name:record.topic});
});
