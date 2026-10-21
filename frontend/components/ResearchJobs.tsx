'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import {researchApi,type ResearchJob} from '@/lib/research-api';

export default function ResearchJobs({topic,runId,selectedIds,blocked,readOnly,onOpen}:{topic:string;runId?:string;selectedIds:string[];blocked:boolean;readOnly:boolean;onOpen:(id:string)=>void}){
 const [jobs,setJobs]=useState<ResearchJob[]>([]),[error,setError]=useState(''),[pending,setPending]=useState(false);
 const alive=useRef(false),locked=useRef(false),version=useRef(0);
 async function refresh(){const current=++version.current;try{const value=await researchApi.jobs();if(alive.current&&current===version.current)setJobs(value.items);}catch(e){if(alive.current&&current===version.current)setError(e instanceof Error?e.message:'Could not load jobs');}}
 const invalidate=useCallback(()=>{alive.current=false;version.current++;},[]);
 useEffect(()=>{alive.current=true;queueMicrotask(()=>{if(alive.current)void refresh();});const timer=setInterval(()=>{if(!locked.current)void refresh();},2000);return()=>{invalidate();clearInterval(timer);};},[invalidate]);
 async function action(work:()=>Promise<unknown>){if(locked.current||readOnly)return;locked.current=true;setPending(true);setError('');version.current++;try{await work();if(alive.current)await refresh();}catch(e){if(alive.current)setError(e instanceof Error?e.message:'Job operation failed');}finally{locked.current=false;if(alive.current)setPending(false);}}
 return <section aria-label="Background jobs"><h3>Background jobs</h3>
 <p>Search and analysis run on the server and survive navigation. Open a completed result when ready. Model reviews are never queued automatically.</p>
 {!readOnly&&<div className="research-row">
 <button disabled={blocked||pending||!topic.trim()} onClick={()=>void action(()=>researchApi.submitJob({kind:'search',topic:topic.trim()}))}>Queue search</button>
 <button disabled={blocked||pending||!runId||!selectedIds.length} onClick={()=>void action(()=>researchApi.submitJob({kind:'analyze',run_id:runId!,selected_ids:selectedIds}))}>Queue analysis</button>
 </div>}
 {error&&<p role="alert">{error}</p>}
 <ul>{jobs.map(job=>{const active=['queued','running','cancel_requested'].includes(job.status);return <li key={job.id}>
 <strong>{job.kind} · {job.status} · attempt {job.attempt}</strong><p>{job.progress}</p>{job.error&&<p>{job.error}</p>}
 {job.status==='succeeded'&&job.run_id&&<button disabled={blocked||pending} onClick={()=>onOpen(job.run_id!)}>Open result</button>}
 {!readOnly&&<>{active?<button disabled={pending||job.status==='cancel_requested'} onClick={()=>void action(()=>researchApi.cancelJob(job.id))}>Cancel</button>:<>
 {['failed','cancelled','interrupted'].includes(job.status)&&job.attempt<3&&<button disabled={pending} onClick={()=>void action(()=>researchApi.retryJob(job.id))}>Retry</button>}
 <button disabled={pending} onClick={()=>void action(()=>researchApi.deleteJob(job.id))}>Remove job</button></>}</>}
 </li>;})}</ul>{!jobs.length&&<p>No background jobs.</p>}
 </section>;
}
