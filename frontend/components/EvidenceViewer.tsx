import type { Claim, ResearchRun } from '@/types/research';

const anchor = (kind: string, id: string) => `research-${kind}-${id}`;
/** Only canonical arXiv HTTPS PDF addresses become external links. */
export function sourcePdf(uri: string, page?: number): string | null {
  if (!/^https:\/\/arxiv\.org\/pdf\/(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?\/\d{7})(?:v\d+)?(?:\.pdf)?$/.test(uri)) return null;
  return `${uri}${page ? `#page=${page}` : ''}`;
}

export default function EvidenceViewer({run}: {run: ResearchRun}) {
  const evidence = run.papers.flatMap(p => p.evidence);
  const evidenceIds = new Set(evidence.map(e => e.id));
  const claims = [...run.papers.flatMap(p => p.claims), ...run.generated_claims];
  const ideas = (claim: Claim) => claim.claim_type === 'suggestion' || claim.claim_type === 'hypothesis';
  function citations(ids: string[]) {
    return <div className="research-citations">{ids.map(id => evidenceIds.has(id) ? <a key={id} href={`#${encodeURIComponent(anchor('evidence',id))}`}>Evidence {id}</a> : <span key={id}>Evidence unavailable: {id}</span>)}</div>;
  }
  function claimView(claim: Claim) {
    return <article key={claim.id} id={anchor('claim',claim.id)} className="research-claim">
      <p className="research-meta">{claim.category.replaceAll('_',' ')} / {claim.claim_type}</p><p>{claim.text}</p>{citations(claim.evidence_ids)}
    </article>;
  }
  function artifacts(suggestions: boolean) {
    return run.artifacts.filter(a => (a.kind === 'research_ideas') === suggestions).map((artifact,index) => {
      const linkedClaims = claims.filter(c => artifact.claim_ids.includes(c.id));
      const ids = [...new Set([...artifact.evidence_ids,...linkedClaims.flatMap(c=>c.evidence_ids)])];
      return <article className="research-artifact" key={`${artifact.kind}-${index}`}><h4>{artifact.title}</h4><p className="research-prose">{artifact.content}</p>{citations(ids)}
        {artifact.claim_ids.map(id => claims.some(c=>c.id===id) ? <a className="research-claim-link" key={id} href={`#${encodeURIComponent(anchor('claim',id))}`}>Claim {id}</a> : <span key={id}>Claim unavailable: {id}</span>)}
      </article>;
    });
  }
  return <div className="research-reading">
    <section aria-label="Source support review" className="research-review"><h3>Source support review</h3><p>{run.review.approved ? 'Literal source support checks passed.' : 'Source support has not passed.'}</p><p className="research-meta">{run.review.scope}</p>{run.review.issues.length>0 && <ul>{run.review.issues.map((issue,i)=><li key={i}>{issue}</li>)}</ul>}</section>
    {evidence.length===0 && <p className="research-empty">No evidence extracted. Select papers to analyze or add a text-based PDF. Missing evidence does not establish a scientific conclusion.</p>}
    <section aria-label="Supported findings"><h3>Supported findings</h3>{artifacts(false)}{claims.filter(c=>!ideas(c)).map(claimView)}{claims.filter(c=>!ideas(c)).length===0 && <p className="research-meta">No supported claims in this record.</p>}</section>
    <section aria-label="Research suggestions" className="research-suggestions"><h3>Research suggestions</h3><p className="research-meta">Ideas and hypotheses need evaluation. Linked evidence provides context, not validation.</p>{artifacts(true)}{claims.filter(ideas).map(claimView)}{claims.filter(ideas).length===0 && !run.artifacts.some(a=>a.kind==='research_ideas') && <p>No suggestions generated.</p>}</section>
    <section aria-label="Evidence and extracted pages"><h3>Evidence and extracted pages</h3>
      {run.papers.map(paper => {const {source,pages,total_pages,truncated}=paper.document; return <article className="research-source" key={source.id}><h4>{source.title}</h4><p className="research-meta">Source: {source.uri}</p><p className="research-meta">{pages.length} extracted of {total_pages} pages. {truncated ? 'Truncated: only part of this document was processed.' : 'Document not truncated.'}</p><p className="research-meta">Missing fields: {paper.missing_fields.length ? paper.missing_fields.join(', ') : 'none reported'}</p>
        {paper.evidence.map(item => <blockquote tabIndex={-1} className="research-evidence" id={anchor('evidence',item.id)} key={item.id}><p>{item.quote}</p><footer>Evidence {item.id} · {source.title} · Page {item.page}</footer><div className="research-citations">{pages.some(page=>page.number===item.page) ? <a href={`#${encodeURIComponent(anchor('page',`${source.id}-${item.page}`))}`}>Extracted page {item.page}</a> : <span>Extracted page unavailable</span>}{sourcePdf(source.uri,item.page) && <a href={sourcePdf(source.uri,item.page)!} target="_blank" rel="noopener noreferrer">Open source PDF at page {item.page}</a>}</div></blockquote>)}
        {pages.map(page => <section tabIndex={-1} className="research-page" id={anchor('page',`${source.id}-${page.number}`)} key={page.number}><h5>{source.title} / Page {page.number}</h5><p className="research-prose">{page.text || 'No text extracted from this page.'}</p></section>)}
      </article>;})}
    </section>
  </div>;
}
