'use client';
import type {ResearchRun} from '@/types/research';

export default function ResearchOverview({run,onStage,onSource}:{run:ResearchRun;onStage:(stage:string)=>void;onSource:(id:string)=>void}) {
 const gaps=run.papers.filter(p=>p.document.truncated||p.document.pages.length<p.document.total_pages||!p.evidence.length||p.missing_fields.length);
 const hasPapers=run.papers.length>0;
 return <section className="research-overview" aria-label="Research readiness">
  <div className="overview-next"><div><h3>{!hasPapers?'Add your first source':gaps.length?'Inspect extraction gaps':'Check evidence in context'}</h3>
   <p>{!hasPapers?'Add a PDF or analyze selected candidates to start reading.':gaps.length?`${gaps.length} of ${run.papers.length} papers need a closer look before synthesis.`:'Read the surrounding pages, compare findings, then develop your draft.'}</p></div>
   <button onClick={()=>onStage(hasPapers?'reading':'library')}>{hasPapers?'Review source evidence':'Go to source collection'}</button>
  </div>
  {hasPapers&&<><p className="overview-status"><strong>{run.review.approved?'Literal checks passed':'Literal checks need attention'}</strong>. Scientific validity is not assessed by these checks.</p>
   {run.review.issues.length>0&&<details><summary>Source check issues ({run.review.issues.length})</summary><ul>{run.review.issues.map((issue,i)=><li key={i}>{issue}</li>)}</ul></details>}
   {gaps.length>0&&<details className="overview-gaps"><summary>Extraction coverage ({gaps.length} papers with gaps)</summary><p>Missing categories mean the extractor found no matching material. They do not prove that a paper lacks those findings.</p>
    <ul>{gaps.map(p=><li key={p.document.source.id}><strong>{p.document.source.title}</strong>
     {(p.document.truncated||p.document.pages.length<p.document.total_pages)&&<p>Partial text: {p.document.pages.length} of {p.document.total_pages} pages extracted{p.document.truncated?' (truncated)':''}.</p>}
     {!p.evidence.length&&<p>No quotations extracted. Read the source pages directly.</p>}
     {p.missing_fields.length>0&&<p>Not extracted: {p.missing_fields.map(c=>c.replaceAll('_',' ')).join(', ')}.</p>}
     <button aria-label={`Inspect ${p.document.source.title}`} onClick={()=>onSource(p.document.source.id)}>Inspect source</button></li>)}</ul>
   </details>}
  </>}
 </section>;
}
