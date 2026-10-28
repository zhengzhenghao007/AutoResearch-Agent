'use client';

import {useEffect,useRef,useState} from 'react';
import type {ResearchRun} from '@/types/research';
import type {WorkspaceItem,WorkspaceItemRequest,WorkspacePreview} from '@/types/workspace';
import {researchApi} from '@/lib/research-api';
import './materials.css';

export function workspaceCsv(headers:string[],rows:(string|number|null)[][]):string {
  const cell=(value:string|number|null)=>{
    let text=String(value??'');
    if(typeof value==='string' && /^[\s]*[=+@-]|^[\t\r\n]/.test(text)) text="'"+text;
    return '"'+text.replaceAll('"','""')+'"';
  };
  return [headers,...rows].map(row=>row.map(cell).join(',')).join('\r\n');
}
function download(text:string,type:string,name:string){
  const url=URL.createObjectURL(new Blob([text],{type}));
  const anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function rawCell(value:number|null|undefined):number|string|null{
  return typeof value==='number'&&Number.isInteger(value)&&!Number.isSafeInteger(value)
    ? 'Beyond browser integer precision; preview table for exact value'
    : value??null;
}
function DataTable({headers,rows}:{headers:string[];rows:(string|number|null)[][]}){
  return <div className="materials-table"><table><thead><tr>{headers.map((h,i)=><th key={i} scope="col">{h}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j}>{cell===null?<span className="materials-muted">Missing</span>:cell}</td>)}</tr>)}</tbody></table></div>;
}
export function MaterialPreview({preview}:{preview:WorkspacePreview}){
  return <div className="material-preview">
    {/* SVG is isolated in an image document, never injected into the application DOM. */}
    {/* eslint-disable-next-line @next/next/no-img-element -- generated SVG data URI needs no remote image optimization */}
    {preview.svg && <img className="material-chart" src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(preview.svg)}`} alt={preview.item.title}/>}
    {preview.headers.length>0 && <DataTable headers={preview.headers} rows={preview.rows.slice(0,50)}/>}
    {preview.rows.length>50 && <p className="materials-muted">Showing the first 50 observations. Download CSV for all {preview.rows.length} rows.</p>}
    {preview.warnings.length>0 && <ul className="materials-warnings">{preview.warnings.map((warning,i)=><li key={i}>{warning}</li>)}</ul>}
    <div className="material-actions">{preview.svg && <button type="button" onClick={()=>download(preview.svg!,'image/svg+xml','research-figure.svg')}>Download SVG</button>}{preview.headers.length>0 && <button type="button" onClick={()=>download(workspaceCsv(preview.headers,preview.rows),'text/csv;charset=utf-8','research-table.csv')}>Download CSV</button>}</div>
  </div>;
}
type Props={run:ResearchRun;busy:boolean;readOnly?:boolean;onSave:(request:WorkspaceItemRequest)=>Promise<boolean>;onDirtyChange?:(dirty:boolean)=>void};
export default function ResearchMaterials(props:Props){return <MaterialsEditor key={props.run.id} {...props}/>;}
function MaterialsEditor({run,busy,readOnly=false,onSave,onDirtyChange}:Props){
  const datasets=run.experiments??[];
  const [spec,setSpec]=useState<WorkspaceItemRequest>({kind:'table',title:'',text:'',dataset_id:datasets[0]?.id??null,columns:[],x_column:null,chart_type:'bar'});
  const [preview,setPreview]=useState<{key:string;value:WorkspacePreview}|null>(null);
  const [opened,setOpened]=useState<{id:string;value:WorkspacePreview}|null>(null);
  const [loading,setLoading]=useState(false);
  const [saving,setSaving]=useState(false);
  const [error,setError]=useState('');
  const [search,setSearch]=useState('');
  const [filter,setFilter]=useState('all');
  const requestId=useRef(0);
  const dataset=datasets.find(d=>d.id===spec.dataset_id);
  const normalized={...spec,title:spec.title.trim(),text:spec.text.trim()};
  const key=JSON.stringify([normalized,dataset?.sha256]);
  const dirty=spec.title.length>0||spec.text.length>0;
  useEffect(()=>{onDirtyChange?.(dirty);return ()=>onDirtyChange?.(false);},[dirty,onDirtyChange]);
  useEffect(()=>{
    if(!dirty)return;
    const warn=(event:BeforeUnloadEvent)=>{event.preventDefault();event.returnValue='';};
    window.addEventListener('beforeunload',warn);
    return ()=>window.removeEventListener('beforeunload',warn);
  },[dirty]);
  const currentKey=useRef(key);
  useEffect(()=>{currentKey.current=key;},[key]);
  useEffect(()=>()=>{requestId.current++;},[]);
  const shown=preview?.key===key?preview.value:null;
  const locked=busy||saving||readOnly;
  function change(patch:Partial<WorkspaceItemRequest>){setSpec(value=>({...value,...patch}));setError('');}
  function bound(value:WorkspacePreview,expected:WorkspaceItemRequest,sha:string|null){
    return value.dataset_sha256===sha && (['kind','title','text','dataset_id','x_column','chart_type'] as const).every(field=>value.item[field]===expected[field]) && JSON.stringify(value.item.columns)===JSON.stringify(expected.columns);
  }
  async function renderPreview(){
    const ticket=++requestId.current;setLoading(true);setError('');
    try{const value=await researchApi.previewWorkspaceItem(run.id,normalized);
      if(ticket!==requestId.current||currentKey.current!==key)return;
      if(!bound(value,normalized,dataset?.sha256??null))throw new Error('Preview does not match the selected material and dataset. Please retry.');
      setPreview({key,value});
    }catch(e){if(ticket===requestId.current)setError(e instanceof Error?e.message:'Unable to preview material.');}
    finally{if(ticket===requestId.current)setLoading(false);}
  }
  async function save(){
    setSaving(true);setError('');
    try{if(await onSave(normalized)){setSpec(value=>({...value,title:'',text:''}));setPreview(null);}else setError('Material was not saved. Your draft is preserved.');}
    catch(e){setError(e instanceof Error?e.message:'Unable to save material.');}
    finally{setSaving(false);}
  }
  async function open(item:WorkspaceItem){
    const ticket=++requestId.current;setLoading(true);setOpened(null);setError('');
    try{const value=await researchApi.workspaceItem(run.id,item.id);if(ticket!==requestId.current)return;
      if(!bound(value,item,item.dataset_sha256))throw new Error('Saved rendering does not match its material record.');
      setOpened({id:item.id,value});
    }catch(e){if(ticket===requestId.current)setError(e instanceof Error?e.message:'Unable to open material.');}
    finally{if(ticket===requestId.current)setLoading(false);}
  }
  const items=(run.workspace_items??[]).filter(item=>(filter==='all'||item.kind===filter)&&`${item.title} ${item.text}`.toLowerCase().includes(search.toLowerCase()));
  const valid=spec.title.trim() && (spec.kind==='note'?spec.text.trim():dataset&&spec.columns.length>0&&(spec.kind!=='figure'||spec.chart_type==='bar'||spec.x_column));
  return <section className="research-materials" aria-label="Research materials">
    <header className="materials-heading"><div><span className="materials-eyebrow">Research record / data & figures</span><h2>Turn observations into materials</h2><p>Inspect imported data, build a reproducible visual, or keep an experiment note.</p></div><span className="materials-count">{(run.workspace_items??[]).length} saved</span></header>
    {error && <p role="alert" className="materials-error">{error}</p>}
    <div className="materials-workbench"><section className="materials-card"><h3>Compose material</h3>
      <label>Dataset<select disabled={busy||saving} value={spec.dataset_id??''} onChange={e=>change({dataset_id:e.target.value||null,columns:[],x_column:null})}><option value="">{spec.kind==='note'?'No linked dataset':'Select a dataset'}</option>{datasets.map(d=><option key={d.id} value={d.id}>{d.data.title}</option>)}</select></label>
      <fieldset disabled={locked}><label>Material kind<select value={spec.kind} onChange={e=>change({kind:e.target.value as WorkspaceItemRequest['kind'],columns:[],x_column:null})}><option value="table">Data table</option><option value="figure">Computed figure</option><option value="note">Researcher note</option></select></label>
      <label>Material title<input maxLength={200} value={spec.title} onChange={e=>change({title:e.target.value})}/></label>
      {spec.kind!=='note' && <fieldset className="materials-columns"><legend>{spec.kind==='figure'?'Y column':'Table columns'}</legend>{dataset?.data.columns.map(column=><label key={column.name}><input type="checkbox" checked={spec.columns.includes(column.name)} onChange={e=>change({columns:spec.kind==='figure'?(e.target.checked?[column.name]:[]):e.target.checked?[...spec.columns,column.name]:spec.columns.filter(c=>c!==column.name)})}/>{column.name}{column.unit?` (${column.unit})`:''}</label>)}</fieldset>}
      {spec.kind==='figure' && <><label>Chart type<select value={spec.chart_type} onChange={e=>change({chart_type:e.target.value as WorkspaceItemRequest['chart_type']})}><option value="bar">Bar</option><option value="line">Line</option><option value="scatter">Scatter</option></select></label><label>X column<select value={spec.x_column??''} onChange={e=>change({x_column:e.target.value||null})}><option value="">Sample IDs (bar only)</option>{dataset?.data.columns.map(c=><option key={c.name}>{c.name}</option>)}</select></label></>}
      <label>Note or caption<textarea rows={4} maxLength={10000} value={spec.text} onChange={e=>change({text:e.target.value})}/></label>
      <div className="material-actions">{spec.kind!=='note' && <button type="button" disabled={!valid||loading} onClick={renderPreview}>{loading?'Rendering…':'Preview material'}</button>}<button className="material-primary" type="button" disabled={!valid||(spec.kind!=='note'&&!shown)} onClick={save}>{saving?'Saving…':'Save material'}</button></div></fieldset>
      {dirty&&<button type="button" disabled={busy||saving} onClick={()=>{if(window.confirm('Discard the unsaved material draft?')){setSpec(value=>({...value,title:'',text:'',columns:[],x_column:null}));setPreview(null);setError('');}}}>Discard material draft</button>}
      <p className="materials-muted">Saved records are immutable. Corrections create a new material. Notes are not scientific results.</p>
    </section><section className="materials-card"><h3>{shown?'Material preview':'Raw observations'}</h3>{shown?<MaterialPreview preview={shown}/>:dataset?<><p>{dataset.data.title} · {dataset.data.rows.length} observations</p><DataTable headers={['Sample ID',...dataset.data.columns.map(c=>`${c.name}${c.unit?` (${c.unit})`:''}`)]} rows={dataset.data.rows.slice(0,50).map(row=>[row.sample_id,...dataset.data.columns.map(c=>rawCell(row.values[c.name]))])}/>{dataset.data.rows.length>50&&<p className="materials-muted">Showing the first 50 observations.</p>}<p className="materials-muted">Missing values remain missing. Rendering does not establish significance or scientific validity. For exact source bytes, use Download original input in the imported observations section.</p></>:<p className="materials-empty">{datasets.length>0?'Select a dataset above to inspect its observations.':'Import CSV or JSON observations to inspect your data and create a figure.'}</p>}</section></div>
    <section className="materials-library"><header><h3>Saved materials</h3><div className="materials-filters"><label>Search materials<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Title or note text"/></label><label>Filter materials<select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All materials</option><option value="figure">Figures</option><option value="table">Tables</option><option value="note">Notes</option></select></label></div></header>
      {items.length===0?<p className="materials-empty">No matching materials. Saved figures, tables and notes will appear here.</p>:<div className="materials-gallery">{items.map(item=><article className="materials-card" key={item.id}><span className="materials-eyebrow">{item.kind==='note'?'Researcher note':item.kind==='figure'?'Computed figure':'Data table'}</span><h4>{item.title}</h4><time dateTime={item.created_at}>{item.created_at.slice(0,10)}</time><p className="material-note">{item.text}</p>{item.kind!=='note'&&<button type="button" disabled={loading} aria-expanded={opened?.id===item.id} onClick={()=>opened?.id===item.id?setOpened(null):void open(item)}>{opened?.id===item.id?'Close material':'Open material'}</button>}{opened?.id===item.id&&<MaterialPreview preview={opened.value}/>}</article>)}</div>}
    </section>
  </section>;
}
