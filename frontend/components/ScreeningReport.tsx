'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ScreeningReportData} from '@/types/screening-report';

const notices = {
  excluded_but_selected:'Excluded but selected for analysis.',
  included_but_not_selected:'Included but not selected for analysis.',
  selected_without_decision:'Selected without a screening decision.',
};
export default function ScreeningReport({runId,revision}:{runId:string;revision:number}) {
  return <ReportPanel key={`${runId}:${revision}`} runId={runId}/>;
}
function ReportPanel({runId}:{runId:string}) {
  const active=useRef(false);const inFlight=useRef(false);
  const [report,setReport]=useState<ScreeningReportData|null>(null);
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  async function load() {
    if(inFlight.current)return;
    inFlight.current=true;setBusy(true);setError('');setReport(null);
    try {
      const result=await researchApi.screeningReport(runId);
      if(result.run_id!==runId)throw new Error('Report returned a different research record. Reopen the record and try again.');
      if(active.current)setReport(result);
    } catch(error) {if(active.current)setError(error instanceof Error?error.message:'Unable to load screening report.');}
    finally {inFlight.current=false;if(active.current)setBusy(false);}
  }
  function download() {
    if(!report)return;
    const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json;charset=utf-8'}));
    const anchor=document.createElement('a');anchor.href=url;
    anchor.download=`screening-${/^[a-f0-9]{32}$/.test(runId)?runId:'record'}.json`;
    document.body.appendChild(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <section className="research-exports" aria-label="Screening audit report">
    <h3>Screening audit report</h3>
    <p className="research-meta">Saved records only. Unsaved checkboxes and annotation drafts are not included. Selection does not mean analysis succeeded.</p>
    <div className="research-row"><button disabled={busy} onClick={()=>void load()}>Load screening report</button>{report&&<button onClick={download}>Download screening JSON</button>}</div>
    {busy&&<p role="status">Loading screening report…</p>}{error&&<p role="alert" className="research-error">{error}</p>}
    {report&&<><p>{report.scope}</p><p>Total: {report.counts.total} · Included: {report.counts.include} · Excluded: {report.counts.exclude} · Undecided: {report.counts.undecided} · Saved selection: {report.counts.selected}</p>
      {report.items.length===0?<p className="research-empty">No candidates in this saved record.</p>:<ul>{report.items.map(item=><li key={item.candidate.id}>
        <strong>{item.candidate.title}</strong><p>Decision: {item.status} · Saved selection: {item.selected_for_analysis?'yes':'no'}</p>
        {item.selection_notice&&<p className="research-notice">{notices[item.selection_notice]}</p>}
        <details><summary>Decision history ({item.history.length})</summary>{item.history.length===0?<p>No recorded decision.</p>:<ol>{item.history.map((event,index)=><li key={index}><span>{event.decision}: {event.reason}</span> <time dateTime={event.decided_at}>{event.decided_at}</time></li>)}</ol>}</details>
      </li>)}</ul>}</>}
  </section>;
}
