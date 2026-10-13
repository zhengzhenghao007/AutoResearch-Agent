'use client';
import CategoryEditor from './CategoryEditor';
import type {ResearchRun,Claim,Category} from '@/types/research';
export default function CategoryRevisions({run,busy,onSave}:{run:ResearchRun;busy:boolean;onSave:(claim:Claim,category:Category,reason:string)=>Promise<boolean>}) {
  const history=run.category_revisions??[];
  return <section className="research-exports" aria-label="Category revisions"><h3>Category revisions</h3>
    <p>Category changes preserve original quotations and evidence. They do not certify scientific validity. {Math.max(0,20-history.length)} revisions remaining.</p>
    {run.papers.flatMap(p=>p.claims).length===0&&<p>No processed claims to revise.</p>}
    {run.papers.map(p=><details key={p.document.source.id}><summary>{p.document.source.title} — edit categories</summary>{p.claims.map(claim=><CategoryEditor key={JSON.stringify(claim)} claim={claim} disabled={busy||history.length>=20} onSave={onSave}/>)}</details>)}
    <details><summary>Revision history ({history.length})</summary>{history.length===0?<p>No category revisions.</p>:<ol>{history.map((event,index)=><li key={index}><p>{event.before.document.source.title} · {event.claim_id} · {event.revised_at}</p><p>{event.before.claims.find(c=>c.id===event.claim_id)?.category} → {event.after.claims.find(c=>c.id===event.claim_id)?.category}: {event.reason}</p><details><summary>Before and after snapshots</summary><pre className="research-export-code">{JSON.stringify({before:event.before,after:event.after},null,2)}</pre></details></li>)}</ol>}</details>
  </section>;
}
