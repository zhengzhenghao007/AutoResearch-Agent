import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LiteratureReview from '@/components/LiteratureReview';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{literaturePacket:vi.fn()}}));
test('builds source-bound review material only on request',async()=>{
 vi.mocked(researchApi.literaturePacket).mockResolvedValue({report:{run_id:'r',project_name:'Research',goal:'',input_sha256:'x',generated_at:'2026-11-06T00:00:00Z',source_ids:['a'],sections:[],searches:[],missing_requirements:['Review protocol required'],scope:'Quoted material'},markdown:'# Research'});
 render(<LiteratureReview runId="r" sourceIds={['a']} onEvidence={()=>{}}/>);
 expect(researchApi.literaturePacket).not.toHaveBeenCalled();
 await userEvent.click(screen.getByRole('button',{name:'Build review material'}));
 expect(await screen.findByRole('button',{name:'Download review Markdown'})).toBeVisible();
 await userEvent.click(screen.getByText('Requirements to resolve'));
 expect(screen.getByText('Review protocol required')).toBeVisible();
 expect(researchApi.literaturePacket).toHaveBeenCalledWith('r',['a']);
});
