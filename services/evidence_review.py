"""Deterministic checks that never ask an LLM to certify its own citations."""
from schemas.research import CATEGORIES, PaperEvidence, Review


def normalized(text: str) -> str:
    return ' '.join(text.split())


def review_paper(paper: PaperEvidence) -> Review:
    issues = []
    doc = paper.document
    pages = {p.number: p.text for p in doc.pages}
    evidence = {e.id: e for e in paper.evidence}
    present = {c.category for c in paper.claims}
    missing = set(paper.missing_fields)
    if present & missing or present | missing != set(CATEGORIES) or len(missing) != len(paper.missing_fields):
        issues.append('Inconsistent missing_fields coverage')
    if len(pages) != len(doc.pages) or any(n > doc.total_pages for n in pages):
        issues.append('Invalid or duplicate page numbers')
    if list(pages) != list(range(1, len(pages) + 1)) or doc.truncated != (len(pages) < doc.total_pages):
        issues.append('Inconsistent page coverage or truncation')
    if len(evidence) != len(paper.evidence):
        issues.append('Duplicate evidence IDs')
    if len({c.id for c in paper.claims}) != len(paper.claims):
        issues.append('Duplicate claim IDs')
    if not paper.evidence or not paper.claims:
        issues.append('No supported claims extracted')
    for item in paper.evidence:
        if item.source_id != doc.source.id:
            issues.append(f'{item.id}: wrong source')
        if item.page not in pages or normalized(item.quote) not in normalized(pages.get(item.page, '')):
            issues.append(f'{item.id}: quote not found on cited page')
    for claim in paper.claims:
        refs = [evidence[e] for e in claim.evidence_ids if e in evidence]
        if len(refs) != len(claim.evidence_ids) or not refs:
            issues.append(f'{claim.id}: missing evidence')
        if claim.claim_type in ('paper_report', 'user_observation'):
            if not any(normalized(claim.text) == normalized(e.quote) for e in refs):
                issues.append(f'{claim.id}: factual report must be an exact quotation')
            expected = 'paper' if claim.claim_type == 'paper_report' else 'user_data'
            if doc.source.kind != expected:
                issues.append(f'{claim.id}: incompatible source type')
        elif claim.claim_type in ('hypothesis', 'suggestion') and claim.category in ('result', 'experiment'):
            issues.append(f'{claim.id}: generated ideas cannot be experimental observations')
    return Review(approved=not issues, issues=issues)
