import {beforeEach,expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EvidenceWorkspace from '@/components/EvidenceWorkspace';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{list:vi.fn(),get:vi.fn(),researchSkills:vi.fn(),submitJob:vi.fn()}}));
vi.mock('@/components/ResearchTasks',()=>({default:()=> <h3>Task execution test view</h3>}));
vi.mock('@/components/ResearchJobs',()=>({default:()=> <h3>Background search progress</h3>}));
const run:ResearchRun={schema_version:1,id:'a'.repeat(32),topic:'Study',plan:[],candidates:[],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,issues:[],scope:'Literal'}};
beforeEach(()=>{vi.clearAllMocks();window.history.replaceState({},'','/');vi.mocked(researchApi.get).mockResolvedValue(run);vi.mocked(researchApi.list).mockResolvedValue({items:[{id:run.id,topic:'Study',project_name:'Study',candidate_count:0,selected_count:0,paper_count:0,updated_at:'',source_support_passed:false}],total:1,page:1,page_size:10});});
test('filters project history from the top search',async()=>{
 render(<EvidenceWorkspace/>);await screen.findByText('Study');
 await userEvent.type(screen.getByRole('searchbox',{name:'Search projects on this page'}),'unmatched');
 expect(screen.getByText('No matching projects on this page.')).toBeVisible();
 expect(screen.queryByText('Study')).not.toBeInTheDocument();
});
test('opens execution through settings and preserves deep links',async()=>{
 window.history.replaceState({},'',`/?run=${run.id}`);
 render(<EvidenceWorkspace/>);await screen.findByRole('heading',{name:'Study'});
 await userEvent.click(screen.getByText('Settings', {exact:true}));
 await userEvent.click(screen.getByText('Agent and model configuration'));
 await userEvent.click(screen.getByRole('button',{name:'Open execution controls'}));
 expect(screen.getByText('Task execution test view')).toBeVisible();
 expect(new URL(window.location.href).searchParams.get('stage')).toBe('tasks');
});
test('home submits a background search without requiring job controls',async()=>{
 render(<EvidenceWorkspace jobsEnabled/>);
 await userEvent.type(screen.getByLabelText('Research topic'),'conformal prediction');
 await userEvent.click(screen.getByRole('button',{name:'Find papers'}));
 expect(researchApi.submitJob).toHaveBeenCalledWith({kind:'search',topic:'conformal prediction'});
 expect(await screen.findByText('Background search progress')).toBeVisible();
});
