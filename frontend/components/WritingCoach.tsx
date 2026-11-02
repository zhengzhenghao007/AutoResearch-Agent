'use client';
import {useState} from 'react';
import type {ManuscriptSection} from '@/types/manuscript';
import type {DraftBlock} from '@/types/manuscript-draft';
import {buildWritingCoach,type ResearchApproach} from '@/lib/writing-coach';
import './writing-coach.css';

interface Props {runId:string;revisionId:string;inputSha256?:string;sections:ManuscriptSection[];blocks:DraftBlock[];stale:boolean;dirty:boolean;onLocate:(sectionId:string,sentenceId?:string)=>void}
export default function WritingCoach({runId,revisionId,inputSha256,sections,blocks,stale,dirty,onLocate}:Props){
 const [approach,setApproach]=useState<ResearchApproach>('unspecified');
 const [message,setMessage]=useState('');
 const report=buildWritingCoach(sections,blocks,stale,approach);
 function download(){
  setMessage('');
  try{
   const data={schema_version:1,kind:'writing_coach_working_notes',run_id:runId,base_revision_id:revisionId,input_sha256:inputSha256,unsaved_draft:dirty,stale_sources:stale,generated_at:new Date().toISOString(),...report};
   const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
   try{const link=document.createElement('a');link.href=url;link.download='writing-coach-notes.json';link.click();setMessage('Guidance notes downloaded. These are not an approved manuscript.');}
   finally{setTimeout(()=>URL.revokeObjectURL(url),1000);}
  }catch{setMessage('Could not download guidance notes. Please retry.');}
 }
 return <details className="writing-coach"><summary>Writing coach</summary>
  <p>Develop the argument before polishing the prose. These local checks follow the current editor, including unsaved changes. Scientific validity is not assessed.</p>
  <div className="coach-toolbar"><label>Research approach<select value={approach} onChange={e=>setApproach(e.target.value as ResearchApproach)}><option value="unspecified">Choose an approach</option><option value="empirical">Empirical / experimental</option><option value="theory">Theory / proof</option><option value="review">Literature review / synthesis</option><option value="interpretive">Interpretive / qualitative</option></select></label><button onClick={download}>Download guidance notes</button></div>
  <p className="research-meta">{dirty?'Unsaved draft':'Saved revision'} · {stale?'Source snapshot changed':'Source snapshot unchanged'}. Approach selection lasts for this editor session; export notes to retain it. No model calls.</p>
  {message&&<p role="status">{message}</p>}
  <h4>Draft checks ({report.issues.length})</h4>
  {!report.issues.length&&<p>No mechanical issues found. This does not establish argument quality, novelty or readiness for submission.</p>}
  <ol className="coach-findings">{report.issues.map((item,index)=><li key={`${item.code}:${item.sentenceId??item.sectionId}:${index}`}><div><span className={`coach-priority ${item.priority}`}>{item.priority==='repair'?'Repair binding':item.priority==='develop'?'Develop draft':'Consider wording'}</span><strong>{item.title}</strong></div>{item.excerpt&&<blockquote>{item.excerpt}</blockquote>}<p>{item.action}</p>{item.sectionId&&<button onClick={()=>onLocate(item.sectionId!,item.sentenceId)}>{item.sentenceId?`Go to paragraph ${item.sentenceId}`:'Go to chapter'}</button>}</li>)}</ol>
  <h4>Questions for your next revision</h4><p className="research-meta">Discussion prompts, not automatic judgments. Record answers in your research notes or manuscript.</p>
  <ol className="coach-questions">{report.questions.map(question=><li key={question}>{question}</li>)}</ol>
 </details>;
}
