import {beforeEach,expect,test,vi} from 'vitest';
import {render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EvidenceWorkspace from '@/components/EvidenceWorkspace';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{list:vi.fn(),get:vi.fn()}}));
vi.mock('@/components/ManuscriptEditor',()=>({default:()=> <label>Draft text<textarea/></label>}));
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
