import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResearchOverview from '@/components/ResearchOverview';
import type {ResearchRun} from '@/types/research';
const run:ResearchRun={schema_version:1,id:'a'.repeat(32),topic:'Study',plan:[],candidates:[],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:true,issues:[],scope:'Literal only'}};
test('empty records guide source collection without claiming passed evidence',()=>{
 render(<ResearchOverview run={run} onStage={vi.fn()} onSource={vi.fn()}/>);
 expect(screen.getByText('Add your first source')).toBeVisible();
 expect(screen.queryByText('Literal checks passed')).not.toBeInTheDocument();
});
test('passed literal checks do not hide extraction gaps or imply scientific review',async()=>{
 const onSource=vi.fn();
 render(<ResearchOverview run={{...run,papers:[{document:{source:{id:'source',title:'Partial paper',kind:'paper',uri:'upload:paper',sha256:'0'.repeat(64),collected_at:''},pages:[{number:1,text:'Text'}],total_pages:5,truncated:true},evidence:[],claims:[],missing_fields:['result','limitation'],extractor:'rule'}]}} onStage={vi.fn()} onSource={onSource}/>);
 expect(screen.getByText('Literal checks passed')).toBeVisible();
 expect(screen.getByText(/Scientific validity is not assessed/)).toBeVisible();
 await userEvent.click(screen.getByText('Extraction coverage (1 papers with gaps)'));
 expect(screen.getByText(/1 of 5 pages/)).toBeVisible();
 expect(screen.getByText(/No quotations extracted/)).toBeVisible();
 expect(screen.getByText(/result, limitation/)).toBeVisible();
 await userEvent.click(screen.getByRole('button',{name:'Inspect Partial paper'}));
 expect(onSource).toHaveBeenCalledWith('source');
});
