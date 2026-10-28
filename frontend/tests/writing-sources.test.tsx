import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WritingSources from '@/components/WritingSources';
import type {DraftBlock} from '@/types/manuscript-draft';
const block:DraftBlock={id:'paper:c1',kind:'paper_claim',text:'An exact quotation about uncertainty.',paper:{claim_id:'c1',source:{id:'source',title:'A research paper',kind:'paper',uri:'upload:paper',sha256:'a'.repeat(64),collected_at:''},evidence:[{id:'e1',source_id:'source',page:2,quote:'An exact quotation about uncertainty.'}],parsed_pages:2,total_pages:3,truncated:true},computation:null};
test('opens source evidence beside writing and inserts a bound quote into the chosen chapter',async()=>{
 const insert=vi.fn();render(<WritingSources blocks={[block]} sections={[{id:'intro',title:'Introduction',sentences:[]}]} disabled={false} onInsert={insert}/>);
 await userEvent.type(screen.getByLabelText('Search writing sources'),'uncertainty');
 await userEvent.click(screen.getByRole('button',{name:'Inspect source: A research paper'}));
 expect(screen.getByRole('blockquote')).toHaveTextContent(block.text);
 expect(screen.getByText(/PDF page 2/,{selector:'footer'})).toBeVisible();
 await userEvent.click(screen.getByRole('button',{name:'Insert with reference'}));
 expect(insert).toHaveBeenCalledWith('intro',block);
});
test('filters nonmatching sources and prevents insertion when locked',async()=>{
 render(<WritingSources blocks={[block]} sections={[{id:'intro',title:'Introduction',sentences:[]}]} disabled onInsert={vi.fn()}/>);
 await userEvent.click(screen.getByRole('button',{name:'Inspect source: A research paper'}));
 expect(screen.getByRole('button',{name:'Insert with reference'})).toBeDisabled();
 await userEvent.type(screen.getByLabelText('Search writing sources'),'absent term');
 expect(screen.getByText('No matching source material.')).toBeVisible();
});
