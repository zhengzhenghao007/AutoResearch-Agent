import LiteratureReview from './LiteratureReview';
import ResearchInvestigation from './ResearchInvestigation';
import type {Category,ResearchRun} from '@/types/research';

const rows: {id:Category;label:string}[]=[{id:'problem',label:'Research problem'},{id:'method',label:'Method'},{id:'dataset',label:'Data'},{id:'experiment',label:'Experiments'},{id:'result',label:'Reported results'},{id:'limitation',label:'Limitations'},{id:'future_work',label:'Future work'}];
export default function ComparisonTable({run,onEvidence,selectedIds=[],onSelection}:{run:ResearchRun;onEvidence:(id:string)=>void;selectedIds?:string[];onSelection?:(ids:string[])=>void}) {
 const chosen=selectedIds.filter(id=>run.papers.some(p=>p.document.source.id===id));
 const papers=chosen.length?run.papers.filter(p=>chosen.includes(p.document.source.id)):run.papers;
 const visibleEvidence = new Set(papers.flatMap(paper => paper.evidence.map(item => item.id)));
 const suggestions = chosen.length
   ? run.generated_claims.filter(claim => claim.evidence_ids.length > 0 && claim.evidence_ids.every(id => visibleEvidence.has(id)))
   : run.generated_claims;
 return <section aria-label="Paper comparison">
  <h3>Compare the evidence</h3><p className="research-meta">Compare what these papers report. Extracted categories may be wrong; open the quotation before drawing a conclusion. No performance ranking is inferred.</p>
  {onSelection&&run.papers.length>0&&<fieldset className="comparison-selection"><legend>Papers to compare</legend><p className="research-meta">All papers are shown until you select a subset.</p>{run.papers.map(p=><label key={p.document.source.id}><input type="checkbox" checked={chosen.includes(p.document.source.id)} onChange={e=>onSelection(e.target.checked?[...chosen,p.document.source.id]:chosen.filter(id=>id!==p.document.source.id))}/>{p.document.source.title}</label>)}{chosen.length>0&&<button onClick={()=>onSelection([])}>Compare all papers</button>}</fieldset>}
  {papers.length<2&&<p className="research-empty">{run.papers.length >= 2 ? "Select another paper to compare it alongside this one." : "Add at least two PDFs in Library for a side-by-side comparison."}</p>}
  {papers.length>0&&<div className="comparison-scroll" tabIndex={0} role="region" aria-label="Scrollable comparison table"><table className="comparison-table"><caption>Saved paper quotations by category</caption><thead><tr><th scope="col">Category</th>{papers.map(p=><th scope="col" key={p.document.source.id}>{p.document.source.title}<span>{p.document.pages.length}/{p.document.total_pages} pages</span></th>)}</tr></thead><tbody>{rows.map(row=><tr key={row.id}><th scope="row">{row.label}</th>{papers.map(p=>{const claims=p.claims.filter(c=>c.category===row.id&&c.claim_type==='paper_report');return <td key={p.document.source.id}>{claims.length? <><p className="comparison-excerpt">{claims[0].text}</p><button onClick={()=>onEvidence(claims[0].evidence_ids[0])}>Read evidence</button>{claims.length>1&&<details><summary>{claims.length-1} more extracts</summary>{claims.slice(1).map(c=><div key={c.id}><p>{c.text}</p><button onClick={()=>onEvidence(c.evidence_ids[0])}>Read evidence</button></div>)}</details>}</>:<span className="coverage-missing">Not extracted</span>}</td>;})}</tr>)}</tbody></table></div>}
  <p className="research-meta">“Not extracted” describes this record, not the absence of a result in the paper or a gap in the field.</p>
  <LiteratureReview key={JSON.stringify([run.id,run.research_goal,papers,run.candidate_decisions])} runId={run.id} sourceIds={papers.map(p=>p.document.source.id)} onEvidence={onEvidence}/>
  <ResearchInvestigation key={JSON.stringify([run.id,run.research_goal,papers])} runId={run.id} sourceIds={papers.map(p=>p.document.source.id)} onEvidence={onEvidence}/>
  <details className="research-advanced"><summary>Exploratory suggestions</summary><p>Ideas need evaluation; linked context does not establish novelty or feasibility.</p>{suggestions.length===0&&<p>No suggestions for these papers.</p>}{suggestions.map(c=><article key={c.id}><p>{c.text}</p>{c.evidence_ids[0]&&<button onClick={()=>onEvidence(c.evidence_ids[0])}>Read context</button>}</article>)}</details>
 </section>;
}
