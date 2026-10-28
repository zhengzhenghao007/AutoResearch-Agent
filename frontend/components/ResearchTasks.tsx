'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ResearchTask,TaskBudget} from '@/types/research-tasks';
import type {ResearchRun} from '@/types/research';
import './research-tasks.css';

type Props={runId:string;topic:string;papers?:ResearchRun['papers'];readOnly?:boolean;onEvidence?:(id:string)=>void};
const defaults:TaskBudget={max_steps:20,max_seconds:60,max_evidence:30};
const resumable=(task:ResearchTask)=>['ready','paused','running'].includes(task.status);
const errorText=(error:unknown)=>error instanceof Error?error.message:'Task request failed';
export default function ResearchTasks(props:Props){return <TaskPanel key={props.runId} {...props}/>;}
function TaskPanel({runId,topic,papers=[],readOnly=false,onEvidence}:Props){
 const [items,setItems]=useState<ResearchTask[]>([]),[task,setTask]=useState<ResearchTask|null>(null);
 const [question,setQuestion]=useState(topic),[questions,setQuestions]=useState('');
 const [budget,setBudget]=useState<TaskBudget>(defaults);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[uncertain,setUncertain]=useState(false),[notice,setNotice]=useState('');
 const active=useRef(true),lock=useRef(false),continuing=useRef(false);
 function accept(value:ResearchTask){
  if(value.run_id!==runId)throw new Error('Task belongs to another research record.');
  if(!active.current)return;
  setTask(value);setBudget(value.budget);setItems(values=>[value,...values.filter(t=>t.id!==value.id)]);
 }
 useEffect(()=>{
  active.current=true;
  researchApi.researchTasks(runId).then(value=>{
   if(!active.current)return;
   if(value.items.some(t=>t.run_id!==runId))throw new Error('Task history does not match this record.');
   setItems(value.items);setTask(value.items[0]??null);if(value.items[0])setBudget(value.items[0].budget);
  }).catch(e=>{if(active.current)setError(errorText(e));});
  return()=>{active.current=false;continuing.current=false;};
 },[runId]);
 async function action(operation:()=>Promise<ResearchTask>,write=true){
  if(lock.current||(write&&(readOnly||uncertain)))return;
  lock.current=true;setBusy(true);setError('');setNotice('');
  try{accept(await operation());if(active.current)setUncertain(false);}
  catch(e){if(active.current){setError(errorText(e));setUncertain(true);}}
  finally{lock.current=false;if(active.current)setBusy(false);}
 }
 async function refresh(){
  if(lock.current)return;
  if(task){await action(()=>researchApi.researchTask(runId,task.id),false);return;}
  lock.current=true;setBusy(true);
  try{const value=await researchApi.researchTasks(runId);if(active.current){if(value.items.some(t=>t.run_id!==runId))throw new Error('Task history does not match this record.');setItems(value.items);if(value.items[0])accept(value.items[0]);setError('');setUncertain(false);}}
  catch(e){if(active.current)setError(errorText(e));}
  finally{lock.current=false;if(active.current)setBusy(false);}
 }
 async function execute(all:boolean){
  if(!task||lock.current||readOnly||uncertain||!resumable(task))return;
  lock.current=true;continuing.current=all;setBusy(true);setError('');setNotice('');
  try{
   for(let n=0;n<200;n++){
    const value=await researchApi.nextResearchTask(runId,task.id);
    if(!active.current)return;
    if(value.id!==task.id)throw new Error('Task response does not match the selected task.');
    accept(value);
    if(!all||!continuing.current||!resumable(value)||value.status==='running')break;
   }
  }catch(e){if(active.current){setError(errorText(e));setUncertain(true);}}
  finally{lock.current=false;continuing.current=false;if(active.current)setBusy(false);}
 }
 async function inspectEvidence(id:string){
  if(!task||!onEvidence)return;
  await action(async()=>{
   const current=await researchApi.researchTask(runId,task.id);
   if(current.id!==task.id||current.run_id!==runId)throw new Error('Task response does not match this record.');
   if(active.current&&current.status!=='stale'&&current.steps.some(step=>step.result?.evidence_ids.includes(id)))onEvidence(id);
   return current;
  },false);
 }
 const validBudget=Number.isInteger(budget.max_steps)&&budget.max_steps>=1&&budget.max_steps<=200&&Number.isFinite(budget.max_seconds)&&budget.max_seconds>=1&&budget.max_seconds<=3600&&Number.isInteger(budget.max_evidence)&&budget.max_evidence>=1&&budget.max_evidence<=500;
 const subquestions=questions.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
 const locked=busy||readOnly||uncertain;
 function evidenceLabel(id:string){
  const paper=papers.find(p=>p.evidence.some(e=>e.id===id));
  const evidence=paper?.evidence.find(e=>e.id===id);
  return paper&&evidence?`${paper.document.source.title} · PDF page ${evidence.page}`:id;
 }
 function stepLabel(step:ResearchTask['steps'][number]){
  const labels:Record<string,string>={lexical_retrieve:'Find matching quotations',inspect_sources:'Check source pages'};
  return labels[step.tool]?step.title.replace(/^[^:]+:/,`${labels[step.tool]}:`):step.title;
 }
 return <section className="research-task-panel" aria-label="Research task execution">
  <header className="task-heading"><div><h3>Plan and follow the evidence</h3><p>Run a bounded research task against this record’s saved papers. Every completed step is saved. This mode uses lexical retrieval, with no model calls or provider charges.</p></div><button disabled={busy} onClick={()=>void refresh()}>Refresh task</button></header>
  {error&&<p role="alert" className="research-error">{error}{uncertain?' Refresh the task before retrying; the last operation may have completed.':''}</p>}
  {notice&&<p role="status">{notice}</p>}
  <details className="task-compose" open={!task}><summary>New research plan</summary>
   <fieldset disabled={locked}><label>Research question<textarea maxLength={2000} value={question} onChange={e=>setQuestion(e.target.value)}/></label>
    <label>Subquestions (optional, one per line)<textarea maxLength={6000} rows={3} value={questions} onChange={e=>setQuestions(e.target.value)} placeholder="Which assumptions are required?"/></label>
    <p className="research-meta">Up to 6 specific subquestions. Leave empty for an inspectable evidence plan derived from the question. Creating a plan does not execute it.</p>
    <button disabled={!question.trim()||subquestions.length>6||!validBudget||items.length>=20} onClick={()=>void action(()=>researchApi.createResearchTask(runId,{question:question.trim(),subquestions,budget}))}>Create research plan</button>
   </fieldset>
  </details>
  <fieldset className="task-budget" disabled={locked}><legend>Task limits</legend>
   <label>Maximum step attempts<input type="number" min={1} max={200} value={Number.isFinite(budget.max_steps)?budget.max_steps:''} onChange={e=>setBudget(b=>({...b,max_steps:e.target.valueAsNumber}))}/></label>
   <label>Maximum active seconds<input type="number" min={1} max={3600} value={Number.isFinite(budget.max_seconds)?budget.max_seconds:''} onChange={e=>setBudget(b=>({...b,max_seconds:e.target.valueAsNumber}))}/></label>
   <label>Maximum evidence items<input type="number" min={1} max={500} value={Number.isFinite(budget.max_evidence)?budget.max_evidence:''} onChange={e=>setBudget(b=>({...b,max_evidence:e.target.valueAsNumber}))}/></label>
   {task&&<button disabled={!validBudget||budget.max_steps<task.budget.max_steps||budget.max_seconds<task.budget.max_seconds||budget.max_evidence<task.budget.max_evidence} onClick={()=>void action(()=>researchApi.increaseResearchTaskBudget(runId,task.id,budget))}>Increase task limits</button>}
  </fieldset>
  {!items.length&&<p>No research tasks yet.</p>}
  {items.length>0&&<label>Saved research tasks<select disabled={busy} value={task?.id??''} onChange={e=>{const next=items.find(t=>t.id===e.target.value);if(next){void action(()=>researchApi.researchTask(runId,next.id),false);}}}>{items.map(t=><option key={t.id} value={t.id}>{t.question} ({t.status.replaceAll('_',' ')})</option>)}</select></label>}
  {task&&<>
   <div className="task-state"><strong>{task.status.replaceAll('_',' ')}</strong><span>{task.steps.filter(s=>s.status==='completed').length} / {task.steps.length} checkpoints</span><span>{task.usage.steps} / {task.budget.max_steps} attempts</span><span>{task.usage.seconds.toFixed(2)} / {task.budget.max_seconds}s</span><span>{task.usage.evidence} / {task.budget.max_evidence} evidence items</span></div>
   {task.stop_reason&&<p className="research-notice">{task.stop_reason}</p>}
   <div className="task-actions"><button disabled={locked||!resumable(task)} onClick={()=>void execute(false)}>Run next step</button><button disabled={locked||!resumable(task)} onClick={()=>void execute(true)}>Continue task</button>{busy&&<button onClick={()=>{continuing.current=false;setNotice('Will stop requesting steps after the current step is saved.');}}>Pause after this step</button>}<button disabled={locked||['cancelled','completed','incomplete','stale','failed'].includes(task.status)} onClick={()=>void action(()=>researchApi.cancelResearchTask(runId,task.id))}>Cancel task</button></div>
   <div className="task-plan"><section><h4>Evidence questions</h4><ol>{task.subquestions.map(q=><li key={q.id}><strong>{q.question}</strong><ul>{q.requirements.map((r,i)=><li key={i}>{r}</li>)}</ul></li>)}</ol></section>
    <section><h4>Execution checkpoints</h4>{task.steps.map(step=><details key={step.id} className="task-step"><summary><span>{stepLabel(step)}</span><small>{step.status} · {step.attempts} attempts</small></summary><p className="research-meta">{step.depends_on.length?'Starts after its evidence search checkpoint.':'Runs against the saved source snapshot.'}</p>{step.result?<><p>{step.result.summary}</p>{step.result.gaps.length>0&&<ul className="task-gaps">{step.result.gaps.map((gap,i)=><li key={i}>{gap}</li>)}</ul>}{step.result.evidence_ids.map(id=><button key={id} disabled={busy||!onEvidence||task.status==='stale'} onClick={()=>void inspectEvidence(id)}>Inspect evidence {evidenceLabel(id)}</button>)}</>:<p>No committed result yet.</p>}</details>)}</section></div>
   <details className="task-events"><summary>Execution history and source binding</summary><p>Source snapshot: <code>{task.source_sha256}</code></p><p>Model input tokens: {task.usage.input_tokens}; output tokens: {task.usage.output_tokens}; provider cost: ${task.usage.cost_usd.toFixed(2)}. Source linkage does not establish scientific validity.</p><ol>{task.events.map((event,i)=><li key={i}><time>{event.at}</time> {event.message}</li>)}</ol></details>
  </>}
 </section>;
}
