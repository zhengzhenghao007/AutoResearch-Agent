'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
import type {SemanticReviewReport} from '@/types/semantic-review';
export default function SemanticReview({run,revision,blocked=false}:{run:ResearchRun;revision:number;blocked?:boolean}) {
  const inFlightRef=useRef(false);
  const [busy,setBusy]=useState(false);
  return <Panel key={`${run.id}:${revision}`} run={run} blocked={blocked} busy={busy} setBusy={setBusy} inFlightRef={inFlightRef}/>;
}
function Panel({run,blocked,busy,setBusy,inFlightRef}:{run:ResearchRun;blocked:boolean;busy:boolean;setBusy:(value:boolean)=>void;inFlightRef:{current:boolean}}) {
  const claims=run.papers.flatMap(p=>p.claims);
  const [selected,setSelected]=useState<string[]>([]);const [consent,setConsent]=useState(false);
  const [report,setReport]=useState<SemanticReviewReport|null>(null);const [error,setError]=useState('');
  const active=useRef(false);
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  async function review() {
    if(blocked||inFlightRef.current||!consent||!selected.length||selected.length>20)return;
    inFlightRef.current=true;setBusy(true);setError('');setReport(null);
    try {const result=await researchApi.semanticReview(run.id,selected);
      if(result.run_id!==run.id)throw new Error('Model review returned a different record.');
      if(active.current)setReport(result);
    }catch(e){if(active.current)setError(e instanceof Error?e.message:'Model review failed.');}
    finally{inFlightRef.current=false;setBusy(false);}
  }
  function download(){
    if(!report)return;
    const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=`semantic-review-${/^[a-f0-9]{32}$/.test(run.id)?run.id:'record'}.json`;
    document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <section className="research-exports" aria-label="Model semantic review"><h3>Model semantic review</h3>
    <p>Optional external model review. Select up to 20 saved claims. Sends their text, source metadata, quotations and complete cited pages to the configured provider; charges may apply. One request, no automatic corrections. Scientific validity remains unverified.</p>
    <details><summary>Select claims ({selected.length}/20)</summary>{claims.length===0&&<p>No processed claims.</p>}{claims.map(c=><label key={c.id} className="research-prose"><input type="checkbox" aria-label={`Review claim ${c.id}`} checked={selected.includes(c.id)} disabled={blocked||busy||(!selected.includes(c.id)&&selected.length>=20)} onChange={e=>{setSelected(old=>e.target.checked?[...old,c.id]:old.filter(id=>id!==c.id));setReport(null);}}/>{c.category}: {c.text}</label>)}</details>
    <label><input type="checkbox" checked={consent} disabled={blocked||busy} onChange={e=>setConsent(e.target.checked)}/>Send selected claims and cited pages to the configured model provider.</label>
    <div className="research-row"><button disabled={blocked||busy||!consent||!selected.length} onClick={()=>void review()}>Run model review</button>{report&&<button onClick={download}>Download model review JSON</button>}</div>
    {busy&&<p role="status">Reviewing selected claims…</p>}{error&&<p role="alert">{error} No automatic retry; a timed-out request may still incur provider usage.</p>}
    {report&&<><p>{report.scope}</p><p>Model: {report.model} · {report.generated_at} · Omitted claims: {report.omitted_claim_count}</p><p>Input hash: {report.input_sha256}</p>
      <h4>Model support judgments</h4><ul>{report.output.claims.map(f=>{const input=report.input_claims.find(i=>i.claim.id===f.claim_id);return <li key={f.claim_id}><strong>{f.claim_id}: {f.verdict} (model judgment)</strong><p>{f.rationale}</p><blockquote>{input?.claim.text}</blockquote><ul>{input?.evidence.filter(e=>f.evidence_ids.includes(e.id)).map(e=><li key={e.id}>Source {e.source_id}, page {e.page}: <q>{e.quote}</q></li>)}</ul></li>;})}</ul>
      <h4>Potential contradictions</h4>{report.output.contradictions.length===0?<p>No potential contradictions reported. This does not prove consistency.</p>:<ul>{report.output.contradictions.map((c,i)=><li key={i}>{c.claim_ids.join(' ↔ ')}: {c.rationale}</li>)}</ul>}
      <details><summary>Exact reviewed input and full cited pages</summary><pre className="research-export-code">{JSON.stringify(report.input_claims,null,2)}</pre></details>
      <p>Download to retain this report. It is not saved to the research record. Category changes require an explicit revision with a reason.</p>
    </>}
  </section>;
}
