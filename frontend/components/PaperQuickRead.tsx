'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {PaperQuickRead as Report,QuickReadPoint} from '@/types/paper-quick-read';

const sections=[['problem','Research problem'],['innovations','Author-claimed innovations'],['methods','Methods & experiments'],['findings_applications','Findings & applications'],['limitations','Limitations'],['goal_relevance','Relevance to your goal'],['suggested_directions','Possible research directions']] as const;
export default function PaperQuickRead({runId,sourceId,goal,readOnly=false,onPage,onDirection}:{runId:string;sourceId:string;goal?:string|null;readOnly?:boolean;onPage:(page:number,quote:string)=>void;onDirection?:(text:string)=>void}){
 const [report,setReport]=useState<Report|null>(null),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const active=useRef(true),lock=useRef(false);
 useEffect(()=>{active.current=true;let current=true;
  researchApi.quickRead(runId,sourceId).then(value=>{if(current)setReport(value);}).catch(e=>{if(current)setError(e instanceof Error?e.message:'Could not load saved quick read.');}).finally(()=>{if(current)setLoading(false);});
  return()=>{current=false;active.current=false;};
 },[runId,sourceId,goal]);
 async function generate(){if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{const value=await researchApi.generateQuickRead(runId,sourceId);if(active.current)setReport(value);}
  catch(e){if(active.current)setError(e instanceof Error?e.message:'Could not summarize this paper.');}
  finally{lock.current=false;if(active.current)setBusy(false);}
 }
 function point(item:QuickReadPoint,index:number){return <li key={index}><p>{item.text}</p><div className="quick-read-references">{item.references.map((ref,i)=><button key={i} title={ref.quote} onClick={()=>onPage(ref.page,ref.quote)}>Page {ref.page}</button>)}</div>{item.kind==='hypothesis'&&<><small>Suggested direction, not an established finding.</small>{onDirection&&<button disabled={readOnly} onClick={()=>onDirection(item.text)}>Use as research goal</button>}</>}</li>;}
 return <section className="quick-read" aria-label="Paper quick read"><div className="quick-read-title"><div><h4>Paper quick read</h4><p className="research-meta">An optional concise outline, with source pages beside every point.</p></div>{!report&&<button className="research-primary" disabled={readOnly||busy||loading} onClick={()=>void generate()}>{busy?'Summarizing…':'Summarize paper'}</button>}</div>
 {!report&&!busy&&<p className="research-meta">You can skip this and read below. Summarizing sends selected paper text to your configured model (one bounded call); saved results are reused.</p>}
 {loading&&<p role="status">Loading saved outline…</p>}{busy&&<p role="status">Reading the paper and checking source references…</p>}{error&&<p role="alert">{error}</p>}
 {report&&<><p className="research-meta">Saved outline · {report.coverage.included_pages.length}/{report.coverage.total_pages} pages supplied · {report.model}</p>
 {report.coverage.notes.map((note,i)=><p className="research-notice" key={i}>{note}</p>)}
 {report.output.one_sentence&&<div className="quick-read-overview"><h5>In one sentence</h5><ul>{point(report.output.one_sentence,0)}</ul></div>}
 <h5>Main points</h5>{report.output.main_points.length?<ol className="quick-read-outline">{report.output.main_points.map(point)}</ol>:<p>Not established from the available text.</p>}
 <div className="quick-read-sections">{sections.filter(([key])=>key!=='goal_relevance'||Boolean(report.goal)).filter(([key])=>key!=='suggested_directions'||!report.goal).map(([key,label])=><details key={key}><summary>{label}</summary>{report.output[key].length?<ul>{report.output[key].map(point)}</ul>:<p>Not explicitly established in the supplied paper text.</p>}</details>)}</div>
 {!!report.output.missing_information.length&&<details><summary>Missing information</summary><ul>{report.output.missing_information.map((text,i)=><li key={i}>{text}</li>)}</ul></details>}
 <p className="research-meta">{report.advisory}</p></>}
 </section>;
}
