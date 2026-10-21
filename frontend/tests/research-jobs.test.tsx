import {afterEach,expect,test,vi} from 'vitest';
import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResearchJobs from '@/components/ResearchJobs';
import {researchApi,type ResearchJob} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{jobs:vi.fn(),submitJob:vi.fn(),cancelJob:vi.fn(),retryJob:vi.fn(),deleteJob:vi.fn()}}));
afterEach(()=>vi.resetAllMocks());
const queued:ResearchJob={id:'job',kind:'search',status:'queued',attempt:1,run_id:null,error:null,progress:'Waiting for a worker'};
const props={topic:'Synthetic',selectedIds:[],blocked:false,readOnly:false,onOpen:vi.fn()};
test('queues explicitly and cancels persisted work',async()=>{
 vi.mocked(researchApi.jobs).mockResolvedValueOnce({items:[]}).mockResolvedValueOnce({items:[queued]}).mockResolvedValue({items:[{...queued,status:'cancelled'}]});
 vi.mocked(researchApi.submitJob).mockResolvedValue(queued);
 vi.mocked(researchApi.cancelJob).mockResolvedValue({...queued,status:'cancelled'});
 render(<ResearchJobs {...props}/>);
 await screen.findByText('No background jobs.');
 await userEvent.click(screen.getByRole('button',{name:'Queue search'}));
 expect(await screen.findByText(/search · queued/)).toBeInTheDocument();
 expect(researchApi.submitJob).toHaveBeenCalledWith({kind:'search',topic:'Synthetic'});
 await userEvent.click(screen.getByRole('button',{name:'Cancel'}));
 expect(await screen.findByText(/search · cancelled/)).toBeInTheDocument();
 expect(researchApi.cancelJob).toHaveBeenCalledWith('job');
});
test('finished jobs never replace current record automatically and respect dirty state',async()=>{
 vi.mocked(researchApi.jobs).mockResolvedValue({items:[{...queued,status:'succeeded',run_id:'result'}]});
 const onOpen=vi.fn();
 const {rerender}=render(<ResearchJobs {...props} onOpen={onOpen} blocked/>);
 expect(await screen.findByRole('button',{name:'Open result'})).toBeDisabled();
 expect(onOpen).not.toHaveBeenCalled();
 rerender(<ResearchJobs {...props} onOpen={onOpen}/>);
 await userEvent.click(screen.getByRole('button',{name:'Open result'}));
 expect(onOpen).toHaveBeenCalledWith('result');
});
test('reader has no mutation controls',async()=>{
 vi.mocked(researchApi.jobs).mockResolvedValue({items:[queued]});
 render(<ResearchJobs {...props} readOnly/>);
 await waitFor(()=>expect(screen.getByText(/search · queued/)).toBeInTheDocument());
 expect(screen.queryByRole('button',{name:'Cancel'})).not.toBeInTheDocument();
 expect(screen.queryByRole('button',{name:'Queue search'})).not.toBeInTheDocument();
});
