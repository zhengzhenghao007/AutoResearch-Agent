import {afterEach,expect,test,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResearchMaterials,{MaterialPreview,workspaceCsv} from '@/components/ResearchMaterials';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
vi.mock('@/lib/research-api',()=>({researchApi:{previewWorkspaceItem:vi.fn(),workspaceItem:vi.fn()}}));
const run:ResearchRun={schema_version:1,id:'a',topic:'Study',plan:[],candidates:[],selected_ids:[],papers:[],generated_claims:[],artifacts:[],review:{approved:false,issues:[],scope:''},experiments:[{id:'data',sha256:'hash',kind:'user_data',claim_type:'user_observation',raw_json:'{}',imported_at:'',data:{title:'Measurements',protocol:null,statistical_method:null,columns:[{name:'score',unit:'m'}],rows:[{sample_id:'s1',values:{score:2}}]}}]};
afterEach(()=>{vi.resetAllMocks();vi.restoreAllMocks();});
test('shows raw data without rendering requests and retains a failed note',async()=>{
 const save=vi.fn().mockResolvedValue(false);
 render(<ResearchMaterials run={run} busy={false} onSave={save}/>);
 expect(screen.getByText('s1')).toBeInTheDocument();
 expect(researchApi.previewWorkspaceItem).not.toHaveBeenCalled();
 await userEvent.selectOptions(screen.getByLabelText('Material kind'),'note');
 await userEvent.type(screen.getByLabelText('Material title'),'Lab note');
 await userEvent.type(screen.getByLabelText('Note or caption'),'Observed today');
 await userEvent.click(screen.getByRole('button',{name:'Save material'}));
 expect(save).toHaveBeenCalledWith(expect.objectContaining({kind:'note',text:'Observed today'}));
 expect(screen.getByLabelText('Note or caption')).toHaveValue('Observed today');
});
test('requires a fresh preview before saving visual material',async()=>{
 vi.mocked(researchApi.previewWorkspaceItem).mockImplementation(async(_id,item)=>({item,dataset_sha256:'hash',headers:['score'],rows:[[2]],svg:null,markdown:'table',warnings:[]}));
 render(<ResearchMaterials run={run} busy={false} onSave={vi.fn()}/>);
 await userEvent.type(screen.getByLabelText('Material title'),'Results');
 await userEvent.click(screen.getByLabelText('score (m)'));
 expect(screen.getByRole('button',{name:'Save material'})).toBeDisabled();
 await userEvent.click(screen.getByRole('button',{name:'Preview material'}));
 expect(await screen.findByRole('button',{name:'Save material'})).toBeEnabled();
 await userEvent.type(screen.getByLabelText('Material title'),' revised');
 expect(screen.getByRole('button',{name:'Save material'})).toBeDisabled();
});
test('CSV neutralizes spreadsheet formula strings without changing numbers',()=>{
 expect(workspaceCsv(['=title'],[[' +SUM(1,2)',-2,null]])).toBe('"\'=title"\r\n"\' +SUM(1,2)","-2",""');
});
test('discards a late preview after its inputs change',async()=>{
 let resolve!:(value:Awaited<ReturnType<typeof researchApi.previewWorkspaceItem>>)=>void;
 vi.mocked(researchApi.previewWorkspaceItem).mockReturnValue(new Promise(r=>{resolve=r;}));
 render(<ResearchMaterials run={run} busy={false} onSave={vi.fn()}/>);
 await userEvent.type(screen.getByLabelText('Material title'),'Results');
 await userEvent.click(screen.getByLabelText('score (m)'));
 await userEvent.click(screen.getByRole('button',{name:'Preview material'}));
 const item=vi.mocked(researchApi.previewWorkspaceItem).mock.calls[0][1];
 await userEvent.type(screen.getByLabelText('Material title'),' new');
 await act(async()=>resolve({item,dataset_sha256:'hash',headers:['score'],rows:[[2]],svg:null,markdown:'',warnings:[]}));
 expect(screen.getByRole('button',{name:'Save material'})).toBeDisabled();
 expect(screen.queryByRole('heading',{name:'Material preview'})).not.toBeInTheDocument();
});
test('rejects preview from a different dataset and prevents read-only writes',async()=>{
 vi.mocked(researchApi.previewWorkspaceItem).mockImplementation(async(_id,item)=>({item,dataset_sha256:'wrong',headers:[],rows:[],svg:null,markdown:'',warnings:[]}));
 const save=vi.fn();
 const {rerender}=render(<ResearchMaterials run={run} busy={false} onSave={save}/>);
 await userEvent.type(screen.getByLabelText('Material title'),'Results');
 await userEvent.click(screen.getByLabelText('score (m)'));
 await userEvent.click(screen.getByRole('button',{name:'Preview material'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('does not match');
 rerender(<ResearchMaterials run={run} busy={false} readOnly onSave={save}/>);
 expect(screen.getByRole('button',{name:'Save material'})).toBeDisabled();
 expect(save).not.toHaveBeenCalled();
});
test('normalizes outer whitespace while retaining note line breaks',async()=>{
 vi.mocked(researchApi.previewWorkspaceItem).mockImplementation(async(_id,item)=>({item:{...item,title:item.title.trim(),text:item.text.trim()},dataset_sha256:'hash',headers:[],rows:[],svg:null,markdown:'',warnings:[]}));
 const save=vi.fn().mockResolvedValue(true);
 render(<ResearchMaterials run={run} busy={false} onSave={save}/>);
 await userEvent.type(screen.getByLabelText('Material title'),' Results ');
 await userEvent.type(screen.getByLabelText('Note or caption'),' First line\nSecond line ');
 await userEvent.click(screen.getByLabelText('score (m)'));
 await userEvent.click(screen.getByRole('button',{name:'Preview material'}));
 await userEvent.click(screen.getByRole('button',{name:'Save material'}));
 expect(save).toHaveBeenCalledWith(expect.objectContaining({title:'Results',text:'First line\nSecond line'}));
});
test('reports dirty draft, protects unload and requires confirmed discard',async()=>{
 const dirty=vi.fn();const confirm=vi.spyOn(window,'confirm').mockReturnValue(false);
 render(<ResearchMaterials run={run} busy={false} onSave={vi.fn()} onDirtyChange={dirty}/>);
 await userEvent.type(screen.getByLabelText('Note or caption'),' ');
 expect(dirty).toHaveBeenLastCalledWith(true);
 const event=new Event('beforeunload',{cancelable:true});window.dispatchEvent(event);expect(event.defaultPrevented).toBe(true);
 await userEvent.click(screen.getByRole('button',{name:'Discard material draft'}));
 expect(screen.getByLabelText('Note or caption')).toHaveValue(' ');
 confirm.mockReturnValue(true);
 await userEvent.click(screen.getByRole('button',{name:'Discard material draft'}));
 expect(screen.getByLabelText('Note or caption')).toHaveValue('');
 expect(dirty).toHaveBeenLastCalledWith(false);
});
test('reader can browse another raw dataset',async()=>{
 const second={...run.experiments![0],id:'second',data:{...run.experiments![0].data,title:'Second dataset',rows:[{sample_id:'other-sample',values:{score:3}}]}};
 render(<ResearchMaterials run={{...run,experiments:[...run.experiments!,second]}} busy={false} readOnly onSave={vi.fn()}/>);
 await userEvent.selectOptions(screen.getByLabelText('Dataset'),'second');
 expect(screen.getByText('other-sample')).toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Save material'})).toBeDisabled();
});
test('caps rendered preview rows without truncating underlying CSV data',()=>{
 const rows=Array.from({length:60},(_,i)=>[i]);
 render(<MaterialPreview preview={{item:{kind:'table',title:'Rows',text:'',dataset_id:'data',columns:['score'],x_column:null,chart_type:'bar'},dataset_sha256:'hash',headers:['score'],rows,svg:null,markdown:'',warnings:[]}}/>);
 expect(screen.getAllByRole('row')).toHaveLength(51);
 expect(screen.getByText(/all 60 rows/)).toBeInTheDocument();
 expect(workspaceCsv(['score'],rows).split('\r\n')).toHaveLength(61);
});
test('raw observations flag unsafe browser integers instead of displaying rounded values',()=>{
 const dataset={...run.experiments![0],data:{...run.experiments![0].data,rows:[{sample_id:'large',values:{score:9007199254740992}}]}};
 render(<ResearchMaterials run={{...run,experiments:[dataset]}} busy={false} onSave={vi.fn()}/>);
 expect(screen.getByText('Beyond browser integer precision; preview table for exact value')).toBeInTheDocument();
 expect(screen.queryByText('9007199254740992')).not.toBeInTheDocument();
 expect(screen.getByText(/Download original input/)).toBeInTheDocument();
});
test('unselected imported datasets prompt selection rather than another import',async()=>{
 render(<ResearchMaterials run={run} busy={false} onSave={vi.fn()}/>);
 await userEvent.selectOptions(screen.getByLabelText('Dataset'),'');
 expect(screen.getByText('Select a dataset above to inspect its observations.')).toBeInTheDocument();
});
