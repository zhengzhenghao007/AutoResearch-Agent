import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MetadataSearch from '@/components/MetadataSearch';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{metadataSearch:vi.fn(),metadataHistory:vi.fn()}}));
test('searches selected databases and retrieves saved history',async()=>{
 vi.mocked(researchApi.metadataHistory).mockResolvedValue({items:[]});
 render(<MetadataSearch runId="r" disabled={false}/>);
 expect(researchApi.metadataHistory).not.toHaveBeenCalled();
 await userEvent.click(screen.getByText('Search across literature databases'));
 await userEvent.type(screen.getByLabelText('Literature search query'),'conformal prediction');
 await userEvent.click(screen.getByRole('button',{name:'Search databases'}));
 expect(researchApi.metadataSearch).toHaveBeenCalledWith('r','conformal prediction',['crossref','openalex']);
 expect(researchApi.metadataHistory).toHaveBeenCalledWith('r');
});
