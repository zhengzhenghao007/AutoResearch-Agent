"""Validate persisted cross-object relationships, not just JSON shape."""
from schemas.research import ResearchRun
from services.evidence_review import review_paper
from services.literature_synthesis import build_suggestions, synthesize


def validate_run(run: ResearchRun) -> None:
    candidate_ids = [c.id for c in run.candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError('Duplicate candidate IDs')
    if len(run.selected_ids) != len(set(run.selected_ids)) or not set(run.selected_ids) <= set(candidate_ids):
        raise ValueError('Invalid selected candidate references')
    source_ids, evidence_ids, claim_ids = set(), set(), set()
    issues = []
    for paper in run.papers:
        if paper.document.source.id in source_ids:
            raise ValueError('Duplicate source IDs')
        source_ids.add(paper.document.source.id)
        if any(c.claim_type not in ('paper_report', 'user_observation') for c in paper.claims):
            raise ValueError('Generated claims must be stored at run level')
        for item in paper.evidence:
            if item.id in evidence_ids:
                raise ValueError('Duplicate global evidence IDs')
            evidence_ids.add(item.id)
        for claim in paper.claims:
            if claim.id in claim_ids:
                raise ValueError('Duplicate global claim IDs')
            claim_ids.add(claim.id)
        review = review_paper(paper)
        # Empty extraction is a valid negative result; invalid citations are not.
        if any(issue != 'No supported claims extracted' for issue in review.issues):
            raise ValueError('Invalid persisted evidence: ' + '; '.join(review.issues))
        issues.extend(f'{paper.document.source.title}: {issue}' for issue in review.issues)
    expected_issues = issues if run.papers else ['No papers processed']
    if run.review.approved != (bool(run.papers) and not issues) or run.review.issues != expected_issues:
        raise ValueError('Stored review does not match evidence')
    if run.generated_claims != build_suggestions(run.papers):
        raise ValueError('Invalid generated claims or suggestion provenance')
    if run.artifacts != synthesize(run.papers):
        raise ValueError('Stored artifacts do not match validated evidence')
