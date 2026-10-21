import {afterEach,expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SessionWorkspace from '@/components/SessionWorkspace';
import {researchApi,setResearchToken} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({setResearchToken:vi.fn(),researchApi:{session:vi.fn()}}));
vi.mock('@/components/EvidenceWorkspace',()=>({default:()=> <div>Isolated workspace</div>}));
afterEach(()=>vi.resetAllMocks());

test('requires credentials after denied session and keeps token out of storage',async()=>{
 vi.mocked(researchApi.session).mockRejectedValueOnce(new Error('Authentication required')).mockResolvedValueOnce({mode:'deployment',user_id:'alice',role:'writer',jobs_enabled:true});
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

test('local offline session opens without a token',async()=>{
 vi.mocked(researchApi.session).mockResolvedValue({mode:'local',user_id:'local',role:'writer',jobs_enabled:false});
 render(<SessionWorkspace/>);
 expect(await screen.findByText('Isolated workspace')).toBeInTheDocument();
 expect(setResearchToken).not.toHaveBeenCalled();
});
