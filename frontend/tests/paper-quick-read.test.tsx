import {beforeEach,expect,test,vi} from 'vitest';
import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PaperQuickRead from '@/components/PaperQuickRead';
import {researchApi} from '@/lib/research-api';
import type {PaperQuickRead as Report} from '@/types/paper-quick-read';
vi.mock('@/lib/research-api',()=>({researchApi:{quickRead:vi.fn(),generateQuickRead:vi.fn()}}));
const point={text:'The method improves scheduling.',kind:'paper_report' as const,references:[{page:2,quote:'Our method improves scheduling.'}]};
const report:Report={run_id:'a',source_id:'s',source_sha256:'x',input_sha256:'x',goal:null,model:'Test model',usage:{input_tokens:10,output_tokens:10,total_tokens:20},coverage:{total_pages:3,parsed_pages:3,included_pages:[1,2,3],omitted_pages:[],truncated_pages:[],ocr_pages:[],notes:[]},output:{one_sentence:point,main_points:[point],problem:[],innovations:[],methods:[],findings_applications:[],limitations:[],goal_relevance:[],suggested_directions:[],missing_information:[]},advisory:'Check the original.'};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(researchApi.quickRead).mockResolvedValue(null);vi.mocked(researchApi.generateQuickRead).mockResolvedValue(report);});
test('only explicit summarization calls the model and page buttons locate cited text',async()=>{
 const onPage=vi.fn();render(<PaperQuickRead runId="a" sourceId="s" onPage={onPage}/>);
 await waitFor(()=>expect(screen.getByRole('button',{name:'Summarize paper'})).toBeEnabled());
 expect(researchApi.generateQuickRead).not.toHaveBeenCalled();
 await userEvent.click(screen.getByRole('button',{name:'Summarize paper'}));
 await screen.findByRole('heading',{name:'Main points'});
 await userEvent.click(screen.getAllByRole('button',{name:'Page 2'})[0]);
 expect(onPage).toHaveBeenCalledWith(2,point.references[0].quote);
 await userEvent.click(screen.getByText('Author-claimed innovations'));
 expect(screen.getAllByText('Not explicitly established in the supplied paper text.').length).toBeGreaterThan(0);
});
test('saved summaries are reused and read-only users cannot generate',async()=>{
 vi.mocked(researchApi.quickRead).mockResolvedValue(report);
 render(<PaperQuickRead runId="a" sourceId="s" onPage={vi.fn()} readOnly/>);
 await screen.findByRole('heading',{name:'Main points'});
 expect(researchApi.generateQuickRead).not.toHaveBeenCalled();
 expect(screen.queryByRole('button',{name:'Summarize paper'})).not.toBeInTheDocument();
});
test('failed generation remains retryable without inventing an outline',async()=>{
 vi.mocked(researchApi.generateQuickRead).mockRejectedValue(new Error('Provider unavailable'));
 render(<PaperQuickRead runId="a" sourceId="s" onPage={vi.fn()}/>);
 await waitFor(()=>expect(screen.getByRole('button',{name:'Summarize paper'})).toBeEnabled());
 await userEvent.click(screen.getByRole('button',{name:'Summarize paper'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Provider unavailable');
 expect(screen.getByRole('button',{name:'Summarize paper'})).toBeEnabled();
 expect(screen.queryByRole('heading',{name:'Main points'})).not.toBeInTheDocument();
});
