import {afterEach,expect,test,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SemanticReview from '@/components/SemanticReview';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{semanticReview:vi.fn()}}));
const claim={id:'c',text:'We will evaluate a method.',category:'experiment' as const,claim_type:'paper_report' as const,evidence_ids:['e'],created_by:'test',timestamp:'2026-10-14T00:00:00Z'};
const source={id:'s',title:'Paper',uri:'upload:test',sha256:'a'.repeat(64),kind:'paper' as const,collected_at:claim.timestamp};
const paper={document:{source,pages:[{number:1,text:claim.text}],total_pages:1,truncated:false},claims:[claim],evidence:[{id:'e',source_id:'s',page:1,quote:claim.text}],missing_fields:[],extractor:'test'};
const run:ResearchRun={schema_version:1,id:'a'.repeat(32),topic:'Test',plan:[],candidates:[],selected_ids:[],papers:[paper],generated_claims:[],artifacts:[],review:{approved:true,issues:[],scope:'Literal only'}};
const result={schema_version:1 as const,run_id:run.id,input_sha256:'b'.repeat(64),input_claims:[{claim,source,evidence:paper.evidence,pages:paper.document.pages}],omitted_claim_count:0,model:'mock',generated_at:claim.timestamp,output:{claims:[{claim_id:'c',verdict:'uncertain' as const,evidence_ids:['e'],rationale:'Plans are not completed experiments.'}],contradictions:[]},scientific_validation:'not_assessed' as const,scope:'Unverified model judgments.'};
afterEach(()=>{vi.resetAllMocks();vi.restoreAllMocks();vi.unstubAllGlobals();});
async function select(){await userEvent.click(screen.getByLabelText('Review claim c'));await userEvent.click(screen.getByLabelText(/Send selected claims/));}
test('requires explicit selection and consent; presents model uncertainty with provenance',async()=>{
  vi.mocked(researchApi.semanticReview).mockResolvedValue(result);
  render(<SemanticReview run={run} revision={0}/>);
  expect(researchApi.semanticReview).not.toHaveBeenCalled();expect(screen.getByRole('button',{name:'Run model review'})).toBeDisabled();
  await select();await userEvent.click(screen.getByRole('button',{name:'Run model review'}));
  expect(await screen.findByText('Plans are not completed experiments.')).toBeInTheDocument();
  expect(screen.getByText('No potential contradictions reported. This does not prove consistency.')).toBeInTheDocument();
  expect(researchApi.semanticReview).toHaveBeenCalledWith(run.id,['c']);
});
test('record revision discards pending result and consent',async()=>{
  let resolve!:(v:typeof result)=>void;vi.mocked(researchApi.semanticReview).mockReturnValue(new Promise(r=>{resolve=r;}));
  const {rerender}=render(<SemanticReview run={run} revision={0}/>);await select();await userEvent.click(screen.getByRole('button',{name:'Run model review'}));
  rerender(<SemanticReview run={run} revision={1}/>);await act(async()=>resolve(result));
  expect(screen.queryByText('Plans are not completed experiments.')).not.toBeInTheDocument();
  expect(screen.getByLabelText(/Send selected claims/)).not.toBeChecked();
});

test('rejects another record response and exports exact successful report',async()=>{
  const create=vi.fn().mockReturnValue('blob:test');vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:create,revokeObjectURL:vi.fn()}));
  let filename='';vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){filename=this.download;});
  vi.mocked(researchApi.semanticReview).mockResolvedValueOnce({...result,run_id:'wrong'}).mockResolvedValueOnce(result);
  render(<SemanticReview run={run} revision={0}/>);await select();await userEvent.click(screen.getByRole('button',{name:'Run model review'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('different record');
  await userEvent.click(screen.getByRole('button',{name:'Run model review'}));await screen.findByText('Plans are not completed experiments.');
  await userEvent.click(screen.getByRole('button',{name:'Download model review JSON'}));
  expect(filename).toBe(`semantic-review-${run.id}.json`);
  expect(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsText(create.mock.calls[0][0]);})).toBe(JSON.stringify(result,null,2)+'\n');
});

test('failed annotation preserves pending review and prevents overlapping requests',async()=>{
  let resolve!:(v:typeof result)=>void;vi.mocked(researchApi.semanticReview).mockReturnValue(new Promise(r=>{resolve=r;}));
  const {rerender}=render(<SemanticReview run={run} revision={0}/>);await select();await userEvent.click(screen.getByRole('button',{name:'Run model review'}));
  rerender(<SemanticReview run={run} revision={0} blocked/>);
  expect(screen.getByRole('button',{name:'Run model review'})).toBeDisabled();
  rerender(<SemanticReview run={run} revision={0}/>);
  expect(screen.getByRole('button',{name:'Run model review'})).toBeDisabled();
  expect(screen.getByLabelText(/Send selected claims/)).toBeChecked();
  await act(async()=>resolve(result));
  expect(await screen.findByText('Plans are not completed experiments.')).toBeInTheDocument();
  expect(researchApi.semanticReview).toHaveBeenCalledTimes(1);
});
