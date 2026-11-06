'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {InvestigationReport} from '@/types/research-investigation';

export default function ResearchInvestigation({runId,sourceIds,onEvidence}:{runId:string;sourceIds:string[];onEvidence:(id:string)=>void}) {
 const [report,setReport]=useState<InvestigationReport|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const active=useRef(true);
 useEffect(()=>{active.current=true;return ()=>{active.current=false;};},[]);
 async function investigate() {
  setBusy(true);setError('');
  try {const result=await researchApi.investigation(runId,sourceIds);if(active.current)setReport(result);}
  catch(failure){if(active.current)setError(failure instanceof Error?failure.message:'Investigation failed.');}
  finally{if(active.current)setBusy(false);}
 }
 function download() {
  const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='research-investigation.json';link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 return <section aria-label="Research questions">
  <h3>Investigate research questions</h3>
  <p>Explore reported limitations and check related passages in your selected papers.</p>
  <button disabled={busy||sourceIds.length<2} onClick={()=>void investigate()}>{busy?'Checking selected papers…':'Build investigation checklist'}</button>
  {sourceIds.length<2&&<p>Select at least two papers.</p>}
  {error&&<p role="alert">{error}</p>}
  {report&&<><p>{report.candidates.length} of {report.total_candidates} reported limitations shown.</p>
   <button onClick={download}>Download investigation report</button>
   {report.limitations.map(text=><p className="research-meta" key={text}>{text}</p>)}
   {!report.candidates.length&&<p>No supported limitations or future directions were extracted from these papers.</p>}
   {report.candidates.map(candidate=><details key={candidate.claim_id}>
    <summary>{candidate.title} · page {candidate.quotation.page}</summary>
    <blockquote>{candidate.quotation.quote}</blockquote>
    <button onClick={()=>onEvidence(candidate.quotation.id)}>Read limitation in context</button>
    <p>{candidate.question}</p><p>{candidate.novelty}</p>
    <h4>Other passages to check</h4>
    {candidate.related_passages.map(passage=><blockquote key={passage.id}><p>{report.source_titles[passage.source_id]} · page {passage.page}</p><p>{passage.quote}</p><button onClick={()=>onEvidence(passage.id)}>Read related passage · page {passage.page}</button></blockquote>)}
    {!candidate.related_passages.length&&<p>No passages matched the shared-word rule in the selected papers. Broaden your search and inspect the papers.</p>}
   </details>)}
  </>}
 </section>;
}
