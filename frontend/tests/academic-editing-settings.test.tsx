import {expect,test,vi} from 'vitest';
import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WorkspaceSettings from '@/components/WorkspaceSettings';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{editingPolicy:vi.fn(),updateEditingPolicy:vi.fn()}}));
test('loads the academic editing policy on demand and saves a new local profile',async()=>{
 vi.mocked(researchApi.editingPolicy).mockResolvedValue({enabled:true,profile:'standard',editable:true});
 vi.mocked(researchApi.updateEditingPolicy).mockResolvedValue({enabled:true,profile:'minimal',editable:true});
 render(<WorkspaceSettings onTasks={()=>{}}/>);
 expect(researchApi.editingPolicy).not.toHaveBeenCalled();
 await userEvent.click(screen.getByText('Settings',{exact:true}));
 await userEvent.click(screen.getByText('Academic Humanizer',{exact:true}));
 await userEvent.selectOptions(await screen.findByRole('combobox'),'minimal');
 await waitFor(()=>expect(researchApi.updateEditingPolicy).toHaveBeenCalledWith('minimal'));
 expect(screen.getByRole('combobox')).toHaveValue('minimal');
});
