import {afterEach,expect,test,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ManuscriptEditor from '@/components/ManuscriptEditor';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{manuscript:vi.fn(),saveManuscript:vi.fn(),reviewManuscript:vi.fn(),approveManuscript:vi.fn(),exportManuscript:vi.fn()}}));
const source={schema_version:1 as const,builder:'evidence-draft-v1' as const,run_id:'run',topic:'Topic',input_sha256:'hash',sections:[],omitted_legacy_observation_claims:0,scientific_validation:'not_assessed' as const,contradiction_review:'not_assessed' as const,approval:'not_requested' as const,statistics_scope:'Descriptive',scope:'Traceability'};
const revision={id:'r1',number:1,created_at:'today',reason:'Initial',content_sha256:'content',input_sha256:'hash',sections:[{id:'intro',title:'Introduction',sentences:[{id:'s1',text:'Original hypothesis',kind:'hypothesis' as const,reference_ids:[]}]}],source};
const state={run_id:'run',current_input_sha256:'hash',revisions:[revision],reviews:[],approvals:[]};
afterEach(()=>vi.resetAllMocks());
test('failed save preserves edited text and reason and prevents approval',async()=>{
 vi.mocked(researchApi.manuscript).mockResolvedValue(state);vi.mocked(researchApi.saveManuscript).mockRejectedValue(new Error('Conflict'));
 render(<ManuscriptEditor runId="run" revision={0}/>);const text=await screen.findByLabelText('Sentence s1');await userEvent.clear(text);await userEvent.type(text,'Edited hypothesis');await userEvent.type(screen.getByLabelText('Revision reason'),'Clarify');await userEvent.click(screen.getByRole('button',{name:'Save manuscript revision'}));expect(await screen.findByRole('alert')).toHaveTextContent('Conflict');expect(text).toHaveValue('Edited hypothesis');expect(screen.getByLabelText('Revision reason')).toHaveValue('Clarify');expect(screen.getByRole('button',{name:'Approve current manuscript'})).toBeDisabled();
});
test('requires unchecked model and human consents',async()=>{
 vi.mocked(researchApi.manuscript).mockResolvedValue(state);render(<ManuscriptEditor runId="run" revision={0}/>);await screen.findByLabelText('Sentence s1');expect(screen.getByLabelText(/Send this manuscript/)).not.toBeChecked();expect(screen.getByRole('button',{name:'Review manuscript with model'})).toBeDisabled();expect(screen.getByLabelText(/I have reviewed/)).not.toBeChecked();
});
test('ignores delayed response from an old source revision',async()=>{
 let resolve!:(v:typeof state)=>void;vi.mocked(researchApi.manuscript).mockReturnValueOnce(new Promise(r=>resolve=r)).mockResolvedValueOnce({...state,revisions:[]});const {rerender}=render(<ManuscriptEditor runId="run" revision={0}/>);rerender(<ManuscriptEditor runId="run" revision={1}/>);await act(async()=>resolve(state));expect(screen.queryByLabelText('Sentence s1')).not.toBeInTheDocument();expect(await screen.findByRole('button',{name:'Initialize from current preview'})).toBeInTheDocument();
});
test('reorders chapters and preserves prior revision content in history after saving',async()=>{
 vi.mocked(researchApi.manuscript).mockResolvedValue({...state,revisions:[{...revision,sections:[...revision.sections,{id:'end',title:'Discussion',sentences:[]}]}]});
 vi.mocked(researchApi.saveManuscript).mockImplementation(async(_id,body)=>({...state,revisions:[revision,{...revision,id:'r2',number:2,reason:body.reason,sections:body.sections!}]}));
 render(<ManuscriptEditor runId="run" revision={0}/>);await screen.findByLabelText('Sentence s1');await userEvent.click(screen.getByLabelText('Move Discussion up'));await userEvent.clear(screen.getByLabelText('Sentence s1'));await userEvent.type(screen.getByLabelText('Sentence s1'),'New text');await userEvent.type(screen.getByLabelText('Revision reason'),'Reorder');await userEvent.click(screen.getByRole('button',{name:'Save manuscript revision'}));expect(await screen.findByText(/Revision 2 ·/)).toBeInTheDocument();expect(screen.getByText(/\[hypothesis\] Original hypothesis/)).toBeInTheDocument();expect(researchApi.saveManuscript).toHaveBeenCalledWith('run',expect.objectContaining({expected_revision:'r1',sections:[{id:'end',title:'Discussion',sentences:[]},{...revision.sections[0],sentences:[{...revision.sections[0].sentences[0],text:'New text'}]}]}));
});
test('serializes model review and renders returned findings with no text changes',async()=>{
 let resolve!:(v:typeof state)=>void;vi.mocked(researchApi.manuscript).mockResolvedValue(state);vi.mocked(researchApi.reviewManuscript).mockReturnValue(new Promise(r=>resolve=r));const busy=vi.fn();render(<ManuscriptEditor runId="run" revision={0} onBusyChange={busy}/>);await screen.findByLabelText('Sentence s1');await userEvent.click(screen.getByLabelText(/Send this manuscript/));await userEvent.click(screen.getByRole('button',{name:'Review manuscript with model'}));expect(screen.getByRole('button',{name:'Review manuscript with model'})).toBeDisabled();expect(busy).toHaveBeenLastCalledWith(true);await act(async()=>resolve(state));expect(screen.getByLabelText('Sentence s1')).toHaveValue('Original hypothesis');expect(screen.getByLabelText(/Send this manuscript/)).not.toBeChecked();
});
test('new findings invalidate an older human approval and remain advisory',async()=>{
 vi.mocked(researchApi.manuscript).mockResolvedValue({...state,reviews:[{id:'rv',revision_id:'r1',content_sha256:'content',input_sha256:'hash',model:'fake',created_at:'today',findings:[{sentence_id:'s1',status:'uncertain',rationale:'Needs independent assessment'}],contradictions:[],scientific_validation:'not_assessed'}],approvals:[{revision_id:'r1',content_sha256:'content',input_sha256:'hash',review_count:0,reviewer:'Tester',note:'Prior assessment',created_at:'today'}]});
 render(<ManuscriptEditor runId="run" revision={0}/>);expect(await screen.findByText(/Needs independent assessment/)).toBeInTheDocument();expect(screen.getByRole('button',{name:'Download approved manuscript'})).toBeDisabled();expect(screen.getByLabelText('Sentence s1')).toHaveValue('Original hypothesis');
});
test('source hash changes prevent model review and export despite existing approval',async()=>{
 vi.mocked(researchApi.manuscript).mockResolvedValue({...state,current_input_sha256:'newhash',approvals:[{revision_id:'r1',content_sha256:'content',input_sha256:'hash',review_count:0,reviewer:'Tester',note:'Prior assessment',created_at:'today'}]});render(<ManuscriptEditor runId="run" revision={0}/>);await screen.findByLabelText('Sentence s1');expect(screen.getByRole('button',{name:'Download approved manuscript'})).toBeDisabled();expect(screen.getByLabelText(/Send this manuscript/)).toBeDisabled();expect(screen.getByText(/Source data changed/)).toBeInTheDocument();
});

test('approval sends the exact review count the human saw',async()=>{
 vi.mocked(researchApi.manuscript).mockResolvedValue(state);
 vi.mocked(researchApi.approveManuscript).mockResolvedValue(state);
 render(<ManuscriptEditor runId="run" revision={0}/>);await screen.findByLabelText('Sentence s1');
 await userEvent.type(screen.getByLabelText('Manuscript reviewer'),'Human');
 await userEvent.type(screen.getByLabelText('Manuscript approval note'),'Reviewed offline');
 await userEvent.click(screen.getByLabelText(/I have reviewed/));
 await userEvent.click(screen.getByRole('button',{name:'Approve current manuscript'}));
 expect(researchApi.approveManuscript).toHaveBeenCalledWith('run','r1','Human','Reviewed offline',0);
});
