"""Build an offline reading checklist with exact, validated evidence links."""
import hashlib
import json
import re
from schemas.research_investigation import InvestigationCandidate, InvestigationReport
from services.evidence_review import review_paper

STOPWORDS = set('this that with from have were been their which would could should these those study paper results method methods future work limitation limitations'.split())


def terms(text):
    return {word for word in re.findall(r'[a-z]{4,}', text.lower()) if word not in STOPWORDS}


def build_investigation(run, source_ids):
    known = {paper.document.source.id for paper in run.papers}
    if len(set(source_ids)) != len(source_ids) or not set(source_ids) <= known:
        raise ValueError('Select distinct existing papers')
    selected = set(source_ids) if source_ids else known
    papers = [paper for paper in run.papers if paper.document.source.id in selected]
    limitations = ['Related passages share words with the limitation. Read them to assess whether they address it.',
                   'External similar-work search has not been performed. Novelty remains unverified.']
    accepted = []
    for paper in papers:
        if review_paper(paper).approved:
            accepted.append(paper)
        else:
            limitations.append(f'Excluded invalid evidence from {paper.document.source.title}.')
        if paper.document.truncated:
            limitations.append(f'Partial text coverage for {paper.document.source.title}.')
        if paper.document.ocr_pages:
            limitations.append(f'OCR text requires checking against the PDF for {paper.document.source.title}.')
    candidates = []
    total = 0
    for paper in accepted:
        evidence = {item.id: item for item in paper.evidence}
        for claim in paper.claims:
            if claim.claim_type != 'paper_report' or claim.category not in ('limitation', 'future_work'):
                continue
            total += 1
            if len(candidates) >= 20:
                continue
            quotation = evidence[claim.evidence_ids[0]]
            query = terms(quotation.quote)
            related = []
            for other in accepted:
                if other.document.source.id == paper.document.source.id:
                    continue
                for passage in other.evidence:
                    overlap = query & terms(passage.quote)
                    if len(overlap) >= 2:
                        related.append((len(overlap), passage))
            related.sort(key=lambda pair: (-pair[0], pair[1].id))
            candidates.append(InvestigationCandidate(claim_id=claim.id, source_id=paper.document.source.id,
                title=paper.document.source.title, quotation=quotation,
                related_passages=[item for _, item in related[:3]],
                question='Which conditions cause this reported limitation, and do the other selected papers address them?'))
    if len(papers) < 2:
        limitations.append('Select at least two papers for cross-paper investigation.')
    payload = {'papers': [paper.model_dump(mode='json') for paper in papers], 'goal': run.research_goal}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return InvestigationReport(input_sha256=digest, goal=run.research_goal or '',
        source_ids=[paper.document.source.id for paper in papers], candidates=candidates[:20],
        total_candidates=total, limitations=limitations,
        source_titles={paper.document.source.id: paper.document.source.title for paper in papers})
