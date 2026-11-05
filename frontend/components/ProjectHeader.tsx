'use client';
import {useState} from 'react';
import type {ResearchRun} from '@/types/research';
import {projectName} from '@/lib/project-name';

export default function ProjectHeader({run,disabled,onSave,onDirtyChange}:{run:ResearchRun|null;disabled:boolean;onSave:(name:string,goal:string)=>Promise<boolean>;onDirtyChange:(value:boolean)=>void}) {
 const savedName=run?projectName(run):'Research',savedGoal=run?.research_goal??'';
 const [name,setName]=useState(savedName),[goal,setGoal]=useState(savedGoal),[editing,setEditing]=useState(false),[goalOpen,setGoalOpen]=useState(Boolean(savedGoal));
 const [saving,setSaving]=useState(false),[error,setError]=useState(''),[saved,setSaved]=useState(false);
 async function save(){
  const nextName=name.trim()||'Research',nextGoal=goal.trim();
  if(nextName===savedName&&nextGoal===savedGoal){setName(nextName);setEditing(false);onDirtyChange(false);return;}
  setSaving(true);setError('');
  try{if(await onSave(nextName,nextGoal)){setName(nextName);setGoal(nextGoal);setEditing(false);setSaved(true);onDirtyChange(false);}else setError('Not saved. Retry after the current operation finishes.');}
  catch(e){setError(e instanceof Error?e.message:'Could not save project.');}
  finally{setSaving(false);}
 }
 function discard(){setName(savedName);setGoal(savedGoal);setEditing(false);setError('');onDirtyChange(false);}
 return <section className="project-header" aria-label="Research project">
  {editing?<label>Project name<input autoFocus maxLength={200} value={name} disabled={saving||disabled} onChange={e=>{setName(e.target.value);setSaved(false);onDirtyChange(true);}} onBlur={()=>void save()} onKeyDown={e=>{if(e.key==='Enter')e.currentTarget.blur();if(e.key==='Escape')discard();}}/></label>:<h2 aria-label={savedName}><button className="project-name" disabled={disabled} onClick={()=>setEditing(true)} aria-label={`Rename project ${savedName}`}>{savedName}<span aria-hidden="true"> ✎</span></button></h2>}
  {!goalOpen?<button className="goal-add" disabled={disabled} onClick={()=>setGoalOpen(true)}>Add research goal (optional)</button>:<label className="project-goal">Research goal (optional)<textarea aria-label="Research goal (optional)" maxLength={2000} value={goal} disabled={disabled||saving} onChange={e=>{setGoal(e.target.value);setSaved(false);onDirtyChange(true);}} onBlur={()=>void save()} placeholder="What would you like to understand? You can leave this empty and start with papers."/><span className="research-meta">Saved when you leave this field. This goal guides research; the project name is only a label.</span></label>}
  {saving&&<p role="status">Saving project…</p>}{saved&&!saving&&<p role="status" className="research-meta">Project saved</p>}
  {error&&<div role="alert"><p>{error}</p><button onClick={()=>void save()} disabled={saving||disabled}>Retry save</button><button onClick={discard} disabled={saving}>Discard changes</button></div>}
  {run&&<p className="research-meta">Project total: {run.papers.length} papers · {run.papers.reduce((n,p)=>n+p.evidence.length,0)} extracts. {run.review.approved?'Extracts match extracted text; check the original before citing.':'Source checks pending.'}</p>}
 </section>;
}
