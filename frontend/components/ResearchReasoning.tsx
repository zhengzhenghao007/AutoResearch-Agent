'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ReasoningRecord} from '@/types/research-reasoning';

type Props={runId:string;topic:string;readOnly?:boolean;onEvidence?:(id:string)=>void};
export default function ResearchReasoning(props:Props){return <ReasoningPanel key={`${props.runId}:${props.topic}`} {...props}/>;}
function ReasoningPanel({runId,topic,readOnly=false,onEvidence}:Props){
 const [question,setQuestion]=useState(topic),[consent,setConsent]=useState(false),[items,setItems]=useState<ReasoningRecord[]>([]);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[uncertain,setUncertain]=useState(false),[loaded,setLoaded]=useState(false);
 const active=useRef(true),lock=useRef(false);
 useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
 function accept(records:ReasoningRecord[]){if(records.some(item=>item.run_id!==runId))throw new Error('Report history belongs to another project.');if(active.current){setItems(records);setLoaded(true);}}
 async function refresh(){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{accept((await researchApi.reasoningHistory(runId)).items);if(active.current)setUncertain(false);}
  catch(e){if(active.current)setError(e instanceof Error?e.message:'Unable to load reports.');}
  finally{lock.current=false;if(active.current)setBusy(false);}
 }
 async function generate(){
  if(lock.current||readOnly||!consent||uncertain)return;lock.current=true;setBusy(true);setError('');
  try{const record=await researchApi.generateReasoning(runId,{question:question.trim(),allow_model:true,max_output_tokens:3000});accept([record,...items.filter(item=>item.id!==record.id)]);}
  catch(e){if(active.current){setError(e instanceof Error?e.message:'Model report request failed.');setUncertain(true);}}
  finally{lock.current=false;if(active.current){setBusy(false);setConsent(false);}}
 }
 async function inspect(record:ReasoningRecord,id:string){
  if(lock.current||!onEvidence)return;lock.current=true;setBusy(true);setError('');
  try{const records=(await researchApi.reasoningHistory(runId)).items;accept(records);const current=records.find(item=>item.id===record.id);if(active.current&&current?.current&&current.status==='completed')onEvidence(id);}
  catch(e){if(active.current)setError(e instanceof Error?e.message:'Unable to verify report sources.');}
  finally{lock.current=false;if(active.current)setBusy(false);}
 }
 const evidence=(record:ReasoningRecord,ids:string[])=>ids.map(id=><button key={id} disabled={busy||!onEvidence} onClick={()=>void inspect(record,id)}>Inspect report evidence {id}</button>);
 return <details className="task-compose"><summary>Optional model research synthesis</summary>
  <p>Generate a cross-paper matrix, hypotheses and review from saved evidence. One provider call per new input, up to 3 calls per project. Source links are not scientific validation.</p>
  <button disabled={busy} onClick={()=>void refresh()}>Load model report history</button>
  {error&&<p role="alert">{error}{uncertain?' Refresh history before another request; the provider may already have been called.':''}</p>}
  <fieldset disabled={busy||readOnly||uncertain}>
   <label>Model research question<textarea maxLength={2000} value={question} onChange={event=>setQuestion(event.target.value)}/></label>
   <label><input type="checkbox" checked={consent} onChange={event=>setConsent(event.target.checked)}/>I allow sending saved evidence to the configured model provider; charges may apply.</label>
   <button disabled={!consent||!question.trim()} onClick={()=>void generate()}>Generate model research report</button>
  </fieldset>
  {busy&&<p role="status">Loading model report…</p>}
  {loaded&&!items.length&&<p>No saved model reports.</p>}
  {items.map(record=><article key={record.id}><h4>{record.question}</h4><p>{record.status} · {record.created_at}</p>
   {record.coverage&&<p>Model input: {record.coverage.selected} of {record.coverage.available} quotations from {record.coverage.selected_sources} of {record.coverage.available_sources} papers.</p>}
   {record.error&&<p role="alert">{record.error}</p>}
   {record.status==='reserved'&&<p>The provider call is in progress or its outcome is unknown. This request will not be automatically retried.</p>}
   {!record.current&&<p>Sources or research goal changed. Report content is withheld.</p>}
   {record.current&&record.status==='completed'&&record.report&&<>
    <h5>Evidence matrix</h5>{record.report.matrix.map((row,index)=><section key={index}><h6>{row.source_id}</h6><p>{row.research_question}</p><p>Method: {row.method}</p><p>Results: {row.results}</p><p>Limitations: {row.limitations}</p><p>Uncertainty: {row.uncertainty}</p>{evidence(record,row.evidence_ids)}</section>)}
    <h5>Hypotheses to test</h5>{record.report.hypotheses.map((row,index)=><section key={index}><p>{row.text}</p><p>Validation experiment: {row.validation_experiment}</p><p>Uncertainty: {row.uncertainty}</p>{evidence(record,row.evidence_ids)}</section>)}
    <h5>Literature review</h5>{record.report.review.map((row,index)=><section key={index}><h6>{row.theme} · {row.kind.replaceAll('_',' ')}</h6><p>{row.text}</p><p>Uncertainty: {row.uncertainty}</p>{evidence(record,row.evidence_ids)}</section>)}
    <ul>{record.report.uncertainties.map((text,index)=><li key={index}>{text}</li>)}</ul>
   </>}
   <p className="research-meta">Input tokens: {record.usage.input_tokens??'unknown'}; output tokens: {record.usage.output_tokens??'unknown'}; cost: {record.usage.cost_usd===null?'unknown':`$${record.usage.cost_usd.toFixed(2)}`}</p>
  </article>)}
 </details>;
}
