'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ProtocolFields,ReviewProtocol} from '@/types/review-protocol';
const labels:Record<keyof ProtocolFields,string>={question:'Review question',inclusion_criteria:'Inclusion criteria',exclusion_criteria:'Exclusion criteria',publication_range:'Publication date range',search_strategy:'Search strategy'};
const empty:ProtocolFields={question:'',inclusion_criteria:'',exclusion_criteria:'',publication_range:'',search_strategy:''};
function fieldsOf(protocol:ReviewProtocol):ProtocolFields {
 return {question:protocol.question,inclusion_criteria:protocol.inclusion_criteria,exclusion_criteria:protocol.exclusion_criteria,publication_range:protocol.publication_range,search_strategy:protocol.search_strategy};
}
export default function ReviewProtocolEditor({runId,onChange,readOnly=false}:{runId:string;readOnly?:boolean;onChange:()=>void}) {
 const [history,setHistory]=useState<ReviewProtocol[]>([]);
 const [fields,setFields]=useState<ProtocolFields>(empty);
 const [loaded,setLoaded]=useState(false);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const [saved,setSaved]=useState(false);
 const active=useRef(true);
 useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
 async function load(){
  setBusy(true);setError('');
  try{const result=await researchApi.reviewProtocol(runId);if(active.current){setHistory(result.revisions);setFields(result.revisions.length?fieldsOf(result.revisions.at(-1)!):empty);setLoaded(true);setSaved(false);onChange();}}
  catch(failure){if(active.current)setError(failure instanceof Error?failure.message:'Could not load protocol.');}
  finally{if(active.current)setBusy(false);}
 }
 async function save(){
  setBusy(true);setError('');
  try{const result=await researchApi.saveReviewProtocol(runId,fields,history.at(-1)?.revision??0);if(active.current){setHistory([...history,result]);setFields(fieldsOf(result));setSaved(true);onChange();}}
  catch(failure){if(active.current)setError(failure instanceof Error?failure.message:'Could not save protocol.');}
  finally{if(active.current)setBusy(false);}
 }
 return <details><summary>Review scope and eligibility criteria</summary>
  <button disabled={busy} onClick={()=>void load()}>{loaded?'Reload saved protocol':'Load review protocol'}</button>
  {error&&<p role="alert">{error}</p>}
  {loaded&&<form onSubmit={event=>{event.preventDefault();void save();}}><fieldset disabled={busy||readOnly}>
   <p>Drafts may be incomplete. Missing fields are listed in the review material. Date range can be stated as unrestricted.</p>
   {(Object.keys(labels) as (keyof ProtocolFields)[]).map(field=><label key={field}>{labels[field]}<textarea value={fields[field]} maxLength={field==='question'?2000:field==='publication_range'?500:5000} onChange={event=>{setFields({...fields,[field]:event.target.value});setSaved(false);}}/></label>)}
   <button>Save protocol revision</button>
  </fieldset></form>}
  {saved&&<p role="status">Protocol revision {history.at(-1)?.revision} saved. Rebuild review material to include it.</p>}
  {history.length>0&&<details><summary>Protocol history · {history.length} revisions</summary>{history.map(protocol=><details key={protocol.revision}><summary>Revision {protocol.revision} · {new Date(protocol.saved_at).toLocaleString()}</summary>{(Object.keys(labels) as (keyof ProtocolFields)[]).map(field=><p key={field}><strong>{labels[field]}</strong> {protocol[field]||'Unspecified'}</p>)}</details>)}</details>}
 </details>;
}
