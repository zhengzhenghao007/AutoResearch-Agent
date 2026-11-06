'use client';
import ReviewProtocolEditor from './ReviewProtocolEditor';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {LiteraturePacket} from '@/types/literature-packet';
export default function LiteratureReview({runId,sourceIds,onEvidence,readOnly=false}:{runId:string;sourceIds:string[];readOnly?:boolean;onEvidence:(id:string)=>void}) {
 const [packet,setPacket]=useState<LiteraturePacket|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const active=useRef(true);
 const reportVersion=useRef(0);
 useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
 async function build(){
  const version=reportVersion.current;
  setBusy(true);setError('');
  try{const result=await researchApi.literaturePacket(runId,sourceIds);if(active.current&&version===reportVersion.current)setPacket(result);}
  catch(failure){if(active.current)setError(failure instanceof Error?failure.message:'Could not build review material.');}
  finally{if(active.current)setBusy(false);}
 }
 function download(format:'json'|'md'){
  if(!packet)return;
  const text=format==='json'?JSON.stringify(packet.report,null,2):packet.markdown;
  const url=URL.createObjectURL(new Blob([text],{type:format==='json'?'application/json':'text/markdown'}));
  const link=document.createElement('a');link.href=url;link.download=`literature-review-material.${format}`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 return <section aria-label="Literature review material"><h3>Prepare literature review material</h3>
  <p>Organize selected paper quotations with saved searches, screening decisions and missing review requirements.</p>
  <ReviewProtocolEditor readOnly={readOnly} runId={runId} onChange={()=>{reportVersion.current+=1;setPacket(null);}}/>
  <button disabled={busy||!sourceIds.length} onClick={()=>void build()}>{busy?'Preparing material…':'Build review material'}</button>
  {error&&<p role="alert">{error}</p>}
  {packet&&<><p>{packet.report.scope}</p><p>Generated {new Date(packet.report.generated_at).toLocaleString()} · {packet.report.source_ids.length} papers · {packet.report.searches.length} saved searches</p>
   <button onClick={()=>download('md')}>Download review Markdown</button><button onClick={()=>download('json')}>Download review provenance</button>
   <details><summary>Requirements to resolve</summary><ul>{packet.report.missing_requirements.map(item=><li key={item}>{item}</li>)}</ul></details>
   {packet.report.sections.map(section=><details key={section.id}><summary>{section.title} · {section.blocks.length} quotations</summary>
    {section.blocks.slice(0,5).map(block=><blockquote key={block.id}><p>{block.text}</p>{block.paper&&<><p>{block.paper.source.title}</p>{block.paper.evidence.map(item=><button key={item.id} onClick={()=>onEvidence(item.id)}>Read page {item.page}</button>)}</>}</blockquote>)}
    {section.blocks.length>5&&<p>The download includes all {section.blocks.length} quotations.</p>}
    {!section.blocks.length&&<p>No quotations extracted for this category.</p>}
   </details>)}
  </>}
 </section>;
}
