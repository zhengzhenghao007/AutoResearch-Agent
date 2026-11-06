import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResearchInvestigation from '@/components/ResearchInvestigation';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{investigation:vi.fn()}}));

test('generates only on request and opens the original evidence',async()=>{
 const onEvidence=vi.fn();
 vi.mocked(researchApi.investigation).mockResolvedValue({input_sha256:'x',goal:'',source_ids:['a','b'],source_titles:{a:'First',b:'Second'},total_candidates:1,limitations:['Novelty unverified'],candidates:[{claim_id:'c',source_id:'a',title:'First',quotation:{id:'e',source_id:'a',page:2,quote:'Limited to a single dataset'},related_passages:[],question:'Does another study address this?',novelty:'Unverified'}]});
 render(<ResearchInvestigation runId="r" sourceIds={['a','b']} onEvidence={onEvidence}/>);
 expect(researchApi.investigation).not.toHaveBeenCalled();
 await userEvent.click(screen.getByRole('button',{name:'Build investigation checklist'}));
 expect(await screen.findByText('Novelty unverified')).toBeVisible();
 await userEvent.click(screen.getByText('First · page 2'));
 await userEvent.click(screen.getByRole('button',{name:'Read limitation in context'}));
 expect(onEvidence).toHaveBeenCalledWith('e');
 expect(researchApi.investigation).toHaveBeenCalledWith('r',['a','b']);
});
