import {expect,test,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {buildWritingCoach} from '@/lib/writing-coach';
import WritingCoach from '@/components/WritingCoach';
import type {ManuscriptSection} from '@/types/manuscript';

const sections:ManuscriptSection[]=[{id:'intro',title:'Introduction',sentences:[
 {id:'fact',text:'An asserted result',kind:'paper_report',reference_ids:[]},
 {id:'idea',text:'Our hypothesis is untested',kind:'hypothesis',reference_ids:[]},
 {id:'todo',text:'Collect observations',kind:'placeholder',reference_ids:[]},
]}];

test('distinguishes unsupported bindings from hypotheses and unresolved work',()=>{
 const report=buildWritingCoach(sections,[],false,'empirical');
 expect(report.issues.find(i=>i.sentenceId==='fact')?.code).toBe('missing_reference');
 expect(report.issues.some(i=>i.sentenceId==='idea')).toBe(false);
 expect(report.issues.find(i=>i.sentenceId==='todo')?.code).toBe('placeholder');
 expect(report.scientificValidation).toBe('not_assessed');
});

test('theory and review prompts do not impose experimental baselines',()=>{
 const theory=buildWritingCoach([],[],false,'theory');
 const review=buildWritingCoach([],[],false,'review');
 expect(theory.questions.join(' ')).toContain('proof');
 expect(review.questions.join(' ')).toContain('inclusion');
 expect(theory.questions.join(' ')).not.toContain('baseline');
 expect(review.questions.join(' ')).not.toContain('ablation');
});

test('stale sources and incompatible references are explicit',()=>{
 const report=buildWritingCoach([{id:'s',title:'Results',sentences:[{id:'x',text:'Observed',kind:'user_observation',reference_ids:['paper:1']}]}],[{id:'paper:1',kind:'paper_claim',text:'Claim',paper:null,computation:null}],true,'empirical');
 expect(report.issues.map(i=>i.code)).toContain('stale_sources');
 expect(report.issues.map(i=>i.code)).toContain('reference_kind');
});

test('valid bindings do not imply semantic approval and missing IDs remain actionable',()=>{
 const paragraph={id:'s',text:'A reported finding.',kind:'paper_report' as const,reference_ids:['p']};
 const block={id:'p',kind:'paper_claim' as const,text:'A finding',paper:null,computation:null};
 const report=buildWritingCoach([{id:'c',title:'Background',sentences:[paragraph]}],[block],false,'review');
 expect(report.issues).toEqual([]);
 expect(report.scientificValidation).toBe('not_assessed');
 const missing=buildWritingCoach([{id:'c',title:'Background',sentences:[paragraph]}],[],false,'review');
 expect(missing.issues[0]).toMatchObject({code:'missing_binding',sentenceId:'s',sectionId:'c'});
});

test('strong wording is a question, not an unsupported verdict',()=>{
 const report=buildWritingCoach([{id:'c',title:'Result',sentences:[{id:'s',text:'This theorem guarantees coverage.',kind:'paper_report',reference_ids:['p']}]}],[{id:'p',kind:'paper_claim',text:'Theorem',paper:null,computation:null}],false,'theory');
 expect(report.issues).toHaveLength(1);
 expect(report.issues[0]).toMatchObject({code:'claim_strength',priority:'consider'});
 expect(report.issues[0].action).toContain('It may be justified');
});

test('panel follows live edits and separates questions from automated checks',async()=>{
 const props={runId:'run',revisionId:'r1',sections,blocks:[],stale:false,dirty:true,onLocate:()=>{}};
 const view=render(<WritingCoach {...props}/>);
 await userEvent.click(screen.getByText('Writing coach'));
 expect(screen.getByText(/Unsaved draft/)).toBeVisible();
 expect(screen.getByRole('button',{name:'Go to paragraph fact'})).toBeVisible();
 await userEvent.selectOptions(screen.getByLabelText('Research approach'),'theory');
 expect(screen.getByText(/Which assumptions does each proof/)).toBeVisible();
 view.rerender(<WritingCoach {...props} sections={[]} dirty={false}/>);
 expect(screen.queryByRole('button',{name:'Go to paragraph fact'})).not.toBeInTheDocument();
 expect(screen.getByText(/Scientific validity is not assessed/)).toBeVisible();
});

test('guidance download records draft provenance and does not claim approval',async()=>{
 let blob:Blob|undefined;
 const create=vi.fn((value:Blob)=>{blob=value;return 'blob:notes';});
 const oldCreate=URL.createObjectURL,oldRevoke=URL.revokeObjectURL;
 URL.createObjectURL=create;URL.revokeObjectURL=vi.fn();
 const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
 try{
  render(<WritingCoach runId="run" revisionId="r1" inputSha256="snapshot" sections={sections} blocks={[]} stale dirty onLocate={()=>{}}/>);
  await userEvent.click(screen.getByText('Writing coach'));
  await userEvent.click(screen.getByRole('button',{name:'Download guidance notes'}));
  const text=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsText(blob!);});
  const data=JSON.parse(text);
  expect(data).toMatchObject({run_id:'run',base_revision_id:'r1',input_sha256:'snapshot',unsaved_draft:true,stale_sources:true,scientificValidation:'not_assessed'});
  expect(data.issues.some((item:{code:string})=>item.code==='stale_sources')).toBe(true);
  expect(screen.getByRole('status')).toHaveTextContent('not an approved manuscript');
 }finally{click.mockRestore();URL.createObjectURL=oldCreate;URL.revokeObjectURL=oldRevoke;}
});
