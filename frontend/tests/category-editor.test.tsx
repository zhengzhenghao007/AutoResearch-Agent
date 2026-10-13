import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CategoryEditor from '@/components/CategoryEditor';
import type {Claim} from '@/types/research';
const claim:Claim={id:'c',text:'We will evaluate this method.',category:'experiment',claim_type:'paper_report',evidence_ids:['e'],created_by:'test',timestamp:'2026-10-14T00:00:00Z'};
test('submits exact expected claim and preserves reason on failure',async()=>{
  const save=vi.fn().mockRejectedValueOnce(new Error('Stale claim')).mockResolvedValueOnce(true);
  render(<CategoryEditor claim={claim} disabled={false} onSave={save}/>);
  expect(screen.getByRole('button',{name:'Save category revision'})).toBeDisabled();
  await userEvent.selectOptions(screen.getByLabelText('New category'),'future_work');
  await userEvent.type(screen.getByLabelText('Revision reason'),'Planned work');
  await userEvent.click(screen.getByRole('button',{name:'Save category revision'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Stale claim');
  expect(screen.getByLabelText('Revision reason')).toHaveValue('Planned work');
  expect(save).toHaveBeenCalledWith(claim,'future_work','Planned work');
  await userEvent.click(screen.getByRole('button',{name:'Save category revision'}));
  expect(screen.getByLabelText('Revision reason')).toHaveValue('');
});
test('budget or shared busy state disables edits',()=>{
  render(<CategoryEditor claim={claim} disabled onSave={vi.fn()}/>);
  expect(screen.getByLabelText('New category')).toBeDisabled();
  expect(screen.getByRole('button',{name:'Save category revision'})).toBeDisabled();
});
