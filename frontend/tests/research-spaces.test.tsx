import {beforeEach,expect,test,vi} from 'vitest';
import {render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EvidenceWorkspace from '@/components/EvidenceWorkspace';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{list:vi.fn(),get:vi.fn(),updateProject:vi.fn(),create:vi.fn(),quickRead:vi.fn(),generateQuickRead:vi.fn()}}));
const run:ResearchRun={schema_version:1,id:'a'.repeat(32),topic:'A survey.pdf',plan:[],candidates:[],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,scope:'Literal only',issues:[]}};
beforeEach(()=>{vi.resetAllMocks();window.history.replaceState({},'',`/?run=${run.id}`);vi.mocked(researchApi.list).mockResolvedValue({items:[],total:0,page:1,page_size:10});vi.mocked(researchApi.get).mockResolvedValue(run);});
test('legacy PDF project title becomes Research and can be renamed without becoming a goal',async()=>{
 vi.mocked(researchApi.updateProject).mockResolvedValue({...run,project_name:'Scheduling'});
 render(<EvidenceWorkspace/>);
 await userEvent.click(await screen.findByRole('button',{name:'Rename project Research'}));
 const input=screen.getByLabelText('Project name');await userEvent.clear(input);await userEvent.type(input,'Scheduling');await userEvent.tab();
 expect(researchApi.updateProject).toHaveBeenCalledWith(run.id,expect.objectContaining({project_name:'Scheduling',research_goal:''}));
 expect(await screen.findByRole('button',{name:'Rename project Scheduling'})).toBeVisible();
});
test('blank space has no mandatory research topic and no automatic model generation',async()=>{
 window.history.replaceState({},'','/');render(<EvidenceWorkspace/>);
 expect(await screen.findByRole('button',{name:'Rename project Research'})).toBeVisible();
 expect(screen.getByRole('button',{name:'Create offline record'})).toBeEnabled();
 expect(researchApi.generateQuickRead).not.toHaveBeenCalled();
 const nav=screen.getByRole('navigation',{name:'Research workflow'});
 expect(within(nav).queryByText('1')).not.toBeInTheDocument();
});
