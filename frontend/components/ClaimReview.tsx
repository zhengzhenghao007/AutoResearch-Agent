'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ClaimReviewData} from '@/types/claim-review';

export default function ClaimReview({runId,revision}:{runId:string;revision:number}) {
  return <ReportPanel key={`${runId}:${revision}`} runId={runId}/>;
}
function ReportPanel({runId}:{runId:string}) {
  const active=useRef(false);const inFlight=useRef(false);
  const [report,setReport]=useState<ClaimReviewData|null>(null);
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  async function load() {
    if(inFlight.current)return;
    inFlight.current=true;setBusy(true);setError('');setReport(null);
    try {
      const result=await researchApi.claimReview(runId);
      if(result.run_id!==runId)throw new Error('Report returned a different research record. Reopen the record and try again.');
      if(active.current)setReport(result);
    } catch(error) {if(active.current)setError(error instanceof Error?error.message:'Unable to load claim review.');}
    finally {inFlight.current=false;if(active.current)setBusy(false);}
  }
  function download() {
    if(!report)return;
    const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json;charset=utf-8'}));
    const anchor=document.createElement('a');anchor.href=url;
    anchor.download=`claim-review-${/^[a-f0-9]{32}$/.test(runId)?runId:'record'}.json`;
    document.body.appendChild(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <section className="research-exports" aria-label="Claim classification review">
    <h3>Claim classification review</h3>
    <p className="research-meta">Advisory English planning-language flags only. Semantic validity is not assessed; no flags does not mean approval. Claims are not changed.</p>
    <div className="research-row"><button disabled={busy} onClick={()=>void load()}>Load claim review</button>{report&&<button onClick={download}>Download claim review JSON</button>}</div>
    {busy&&<p role="status">Loading claim review…</p>}{error&&<p role="alert" className="research-error">{error}</p>}
    {report&&<><p>{report.scope}</p><p>Claims: {report.claim_count} · Checked: {report.checked_claim_count} · Flagged: {report.flagged_claim_count}</p>
      <p className="research-meta">Rule: {report.rule_version} · Semantic validation: not assessed</p>
      {report.flags.length===0?<p className="research-empty">No planning-language flags found. This is not semantic approval.</p>:<ul>{report.flags.map(flag=><li key={flag.claim_id}>
        <h4>{flag.category}: {flag.claim_id}</h4><p className="research-meta">Source: {flag.source_id}</p>
        <blockquote className="research-prose">{flag.claim_text}</blockquote><p>Matched phrase: <mark>{flag.matched_text}</mark></p><p>{flag.message}</p>
        <h5>Original evidence</h5><ul>{flag.evidence.map((item,index)=><li key={`${item.id}:${index}`}><p className="research-meta">Source {item.source_id} · Page {item.page} · Evidence {item.id}</p><blockquote className="research-prose">{item.quote}</blockquote></li>)}</ul>
      </li>)}</ul>}</>}
  </section>;
}