import {afterEach,expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SessionWorkspace from '@/components/SessionWorkspace';
import {researchApi,setResearchToken} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({setResearchToken:vi.fn(),researchApi:{session:vi.fn()}}));
vi.mock('@/components/EvidenceWorkspace',()=>({default:()=> <div>Isolated workspace</div>}));
afterEach(()=>vi.resetAllMocks());

test('requires credentials after denied session and keeps token out of storage',async()=>{
 vi.mocked(researchApi.session).mockRejectedValueOnce(Object.assign(new Error('Authentication required'),{status:401})).mockResolvedValueOnce({mode:'deployment',user_id:'alice',role:'writer',jobs_enabled:true});
 render(<SessionWorkspace/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('Authentication required');
 expect(screen.queryByText('Isolated workspace')).not.toBeInTheDocument();
 await userEvent.type(screen.getByLabelText('Access token'),'secret-for-test');
 await userEvent.click(screen.getByRole('button',{name:'Connect'}));
 expect(await screen.findByText('Isolated workspace')).toBeInTheDocument();
 expect(setResearchToken).toHaveBeenCalledWith('secret-for-test');
 expect(screen.getByLabelText('Access token')).toHaveValue('');
 expect(sessionStorage.length).toBe(0);expect(localStorage.length).toBe(0);
 await userEvent.click(screen.getByRole('button',{name:'Disconnect'}));
 expect(screen.queryByText('Isolated workspace')).not.toBeInTheDocument();
 expect(setResearchToken).toHaveBeenLastCalledWith('');
});

test('a disconnected local API gives recovery instructions, not a token prompt',async()=>{
 vi.mocked(researchApi.session).mockRejectedValue(new Error('Connection lost'));
 render(<SessionWorkspace/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('Connection lost');
 expect(screen.queryByLabelText('Access token')).not.toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Retry connection'})).toBeVisible();
});

test('invalid replacement credentials retain the deployment login form',async()=>{
 vi.mocked(researchApi.session).mockResolvedValueOnce({mode:'deployment',user_id:'alice',role:'writer',jobs_enabled:true}).mockRejectedValueOnce(Object.assign(new Error('Authentication required'),{status:401}));
 render(<SessionWorkspace/>);
 await screen.findByText('Isolated workspace');
 await userEvent.type(screen.getByLabelText('Access token'),'wrong');
 await userEvent.click(screen.getByRole('button',{name:'Connect'}));
 await screen.findByRole('alert');
 expect(screen.getByLabelText('Access token')).toBeVisible();
 expect(screen.queryByRole('button',{name:'Retry connection'})).not.toBeInTheDocument();
});

test('local offline session opens without a token',async()=>{
 vi.mocked(researchApi.session).mockResolvedValue({mode:'local',user_id:'local',role:'writer',jobs_enabled:false});
 render(<SessionWorkspace/>);
 expect(await screen.findByText('Isolated workspace')).toBeInTheDocument();
 expect(setResearchToken).not.toHaveBeenCalled();
 expect(screen.queryByLabelText('Access token')).not.toBeInTheDocument();
 expect(screen.queryByRole('button',{name:'Disconnect'})).not.toBeInTheDocument();
});
