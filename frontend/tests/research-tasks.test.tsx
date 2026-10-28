import {beforeEach,expect,test,vi} from 'vitest';
import {act,render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResearchTasks from '@/components/ResearchTasks';
import {researchApi} from '@/lib/research-api';
import type {ResearchTask} from '@/types/research-tasks';
vi.mock('@/lib/research-api',()=>({researchApi:{researchTasks:vi.fn(),createResearchTask:vi.fn(),researchTask:vi.fn(),nextResearchTask:vi.fn(),cancelResearchTask:vi.fn(),increaseResearchTaskBudget:vi.fn()}}));
const task:ResearchTask={id:'a'.repeat(32),run_id:'b'.repeat(32),question:'How do missing inputs affect coverage?',source_sha256:'hash',created_at:'2026-10-28',updated_at:'2026-10-28',status:'ready',stop_reason:null,budget:{max_steps:20,max_seconds:60,max_evidence:30},usage:{steps:0,seconds:0,evidence:0,input_tokens:0,output_tokens:0,cost_usd:0},subquestions:[{id:'q1',question:'What fails with missing inputs?',requirements:['Find source quotations']}],steps:[{id:'s1',question_id:'q1',title:'Inspect source evidence',tool:'retrieve',depends_on:[],status:'pending',attempts:0,input_sha256:'hash',result:null}],events:[]};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(researchApi.researchTasks).mockResolvedValue({items:[task]});vi.mocked(researchApi.researchTask).mockResolvedValue(task);});
test('loads durable plans without automatically executing and respects read-only mode',async()=>{
 render(<ResearchTasks runId={task.run_id} topic={task.question} readOnly/>);
 await screen.findByText('What fails with missing inputs?');
 expect(researchApi.nextResearchTask).not.toHaveBeenCalled();
 expect(screen.getByRole('button',{name:'Run next step'})).toBeDisabled();
 expect(screen.getByRole('button',{name:'Create research plan'})).toBeDisabled();
});
test('executes one step and displays checkpoint result and missing evidence',async()=>{
 vi.mocked(researchApi.nextResearchTask).mockResolvedValue({...task,status:'incomplete',stop_reason:'No matching source evidence',usage:{...task.usage,steps:1},steps:[{...task.steps[0],status:'completed',result:{evidence_ids:[],gaps:['No coverage evidence'],summary:'No supported answer'}}]});
 render(<ResearchTasks runId={task.run_id} topic={task.question}/>);
 await screen.findByText('What fails with missing inputs?');
 await userEvent.click(screen.getByRole('button',{name:'Run next step'}));
 await screen.findByText('No matching source evidence');
 expect(researchApi.nextResearchTask).toHaveBeenCalledTimes(1);
 expect(screen.getByRole('button',{name:'Run next step'})).toBeDisabled();
 await userEvent.click(screen.getByText('Inspect source evidence'));
 expect(screen.getByText('No coverage evidence')).toBeVisible();
});
test('failed calls preserve the plan and require refresh before uncertain retry',async()=>{
 vi.mocked(researchApi.nextResearchTask).mockRejectedValue(new Error('Connection lost'));
 render(<ResearchTasks runId={task.run_id} topic={task.question}/>);
 await screen.findByText('What fails with missing inputs?');
 await userEvent.click(screen.getByRole('button',{name:'Run next step'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Connection lost');
 expect(screen.getByRole('button',{name:'Run next step'})).toBeDisabled();
 await userEvent.click(screen.getByRole('button',{name:'Refresh task'}));
 await waitFor(()=>expect(screen.getByRole('button',{name:'Run next step'})).toBeEnabled());
});
test('late response from a previous record cannot replace the next record task',async()=>{
 let resolve!:(v:ResearchTask)=>void;
 vi.mocked(researchApi.nextResearchTask).mockReturnValue(new Promise(r=>{resolve=r;}));
 const view=render(<ResearchTasks runId={task.run_id} topic={task.question}/>);
 await screen.findByText('What fails with missing inputs?');
 await userEvent.click(screen.getByRole('button',{name:'Run next step'}));
 vi.mocked(researchApi.researchTasks).mockResolvedValue({items:[]});
 view.rerender(<ResearchTasks runId={'c'.repeat(32)} topic="New topic"/>);
 await screen.findByText('No research tasks yet.');
 await act(async()=>resolve({...task,status:'completed'}));
 expect(screen.queryByText('What fails with missing inputs?')).not.toBeInTheDocument();
});

test('evidence navigation rechecks source binding and blocks stale completed results',async()=>{
 const completed={...task,status:'completed' as const,steps:[{...task.steps[0],status:'completed' as const,result:{evidence_ids:['ev1'],gaps:[],summary:'Retrieved evidence'}}]};
 vi.mocked(researchApi.researchTasks).mockResolvedValue({items:[completed]});
 vi.mocked(researchApi.researchTask).mockResolvedValue({...completed,status:'stale',stop_reason:'Saved sources changed'});
 const inspect=vi.fn();render(<ResearchTasks runId={task.run_id} topic={task.question} onEvidence={inspect}/>);
 await screen.findByText('What fails with missing inputs?');
 await userEvent.click(screen.getByText('Inspect source evidence'));
 await userEvent.click(screen.getByRole('button',{name:'Inspect evidence ev1'}));
 await screen.findByText('Saved sources changed');
 expect(inspect).not.toHaveBeenCalled();
 expect(screen.getByRole('button',{name:'Inspect evidence ev1'})).toBeDisabled();
});

test('budget exhausted task continues only after an explicit increase',async()=>{
 const exhausted={...task,status:'budget_exhausted' as const,usage:{...task.usage,steps:20}};
 vi.mocked(researchApi.researchTasks).mockResolvedValue({items:[exhausted]});
 vi.mocked(researchApi.increaseResearchTaskBudget).mockResolvedValue({...exhausted,status:'paused',budget:{...task.budget,max_steps:25}});
 render(<ResearchTasks runId={task.run_id} topic={task.question}/>);
 await screen.findByText('What fails with missing inputs?');
 expect(screen.getByRole('button',{name:'Run next step'})).toBeDisabled();
 await userEvent.clear(screen.getByLabelText('Maximum step attempts'));
 await userEvent.type(screen.getByLabelText('Maximum step attempts'),'25');
 await userEvent.click(screen.getByRole('button',{name:'Increase task limits'}));
 expect(researchApi.increaseResearchTaskBudget).toHaveBeenCalledWith(task.run_id,task.id,{...task.budget,max_steps:25});
 expect(screen.getByRole('button',{name:'Run next step'})).toBeEnabled();
 expect(screen.getByText('20 / 25 attempts')).toBeVisible();
});
