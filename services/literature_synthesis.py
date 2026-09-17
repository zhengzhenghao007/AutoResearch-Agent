"""Extractive comparison; exploratory proposals are explicitly labelled."""
from schemas.research import Artifact, Claim, PaperEvidence
from services.evidence_review import review_paper


def build_suggestions(papers: list[PaperEvidence]) -> list[Claim]:
    suggestions = []
    for paper in papers:
        if not review_paper(paper).approved:
            continue
        for claim in paper.claims:
            if claim.category in ('limitation', 'future_work'):
                suggestions.append(Claim(
                    id=f'suggestion:{claim.id}',
                    text='Consider a study addressing this author-reported limitation or future direction: '
                         + claim.text + ' Feasibility and novelty are unverified; this is not an observed result.',
                    category='future_work', claim_type='suggestion',
                    evidence_ids=list(claim.evidence_ids), created_by='extractive-synthesis-v1',
                    timestamp=claim.timestamp,
                ))
    return suggestions


def synthesize(papers: list[PaperEvidence]) -> list[Artifact]:
    accepted = [p for p in papers if review_paper(p).approved]
    if not accepted:
        return []
    claims = [c for p in accepted for c in p.claims]
    evidence = {e.id: e for p in accepted for e in p.evidence}
    titles = {p.document.source.id: p.document.source.title for p in accepted}

    def line(c):
        e = evidence[c.evidence_ids[0]]
        return f'[{c.claim_type}; {c.category}] {titles[e.source_id]}, p.{e.page}: {c.text} [evidence={e.id}]'

    methods = [c for c in claims if c.category == 'method']
    suggestions = build_suggestions(papers)
    return [
        Artifact(kind='literature_summary', title='Quoted literature evidence (not independently verified)', content='\n'.join(line(c) for c in claims), claim_ids=[c.id for c in claims], evidence_ids=list(evidence)),
        Artifact(kind='method_comparison', title='Methods side by side; no ranking inferred', content='\n'.join(line(c) for c in methods) or 'No methods extracted from the parsed pages.', claim_ids=[c.id for c in methods], evidence_ids=[e for c in methods for e in c.evidence_ids]),
        Artifact(kind='research_ideas', title='Exploratory suggestions, not findings', content='\n'.join(line(c) for c in suggestions) or 'Insufficient explicit limitations/future directions for grounded suggestions.', claim_ids=[c.id for c in suggestions], evidence_ids=[e for c in suggestions for e in c.evidence_ids]),
        Artifact(kind='coverage_gaps', title='Evidence coverage gaps only', content='\n'.join(f'{p.document.source.title}: missing extracted categories: {", ".join(p.missing_fields) or "none"}; read {len(p.document.pages)}/{p.document.total_pages} pages.' for p in papers) + '\nThese gaps concern selected parsed pages, not the whole field. No user experimental data or results were supplied.'),
    ]
