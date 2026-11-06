import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewProtocolEditor from '@/components/ReviewProtocolEditor';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{reviewProtocol:vi.fn(),saveReviewProtocol:vi.fn()}}));
test('loads before editing and saves against the loaded revision',async()=>{
 vi.mocked(researchApi.reviewProtocol).mockResolvedValue({run_id:'r',revisions:[]});
 vi.mocked(researchApi.saveReviewProtocol).mockResolvedValue({revision:1,saved_at:'2026-11-06T00:00:00Z',question:'Question',inclusion_criteria:'',exclusion_criteria:'',publication_range:'',search_strategy:''});
 const onChange=vi.fn();render(<ReviewProtocolEditor runId="r" onChange={onChange}/>);
 await userEvent.click(screen.getByText('Review scope and eligibility criteria'));
 await userEvent.click(screen.getByRole('button',{name:'Load review protocol'}));
 await userEvent.type(await screen.findByLabelText('Review question'),'Question');
 await userEvent.click(screen.getByRole('button',{name:'Save protocol revision'}));
 expect(researchApi.saveReviewProtocol).toHaveBeenCalledWith('r',expect.objectContaining({question:'Question'}),0);
 expect(await screen.findByRole('status')).toHaveTextContent('revision 1 saved');
 expect(onChange).toHaveBeenCalledTimes(2);
});
