"""Explicit category-only changes with preserved evidence and bounded history."""
from schemas.research import CATEGORIES
from services.evidence_review import review_paper


def set_category(paper, claim_id, category):
    updated = paper.model_copy(deep=True)
    claim = next(c for c in updated.claims if c.id == claim_id)
    claim.category = category
    present = {c.category for c in updated.claims}
    updated.missing_fields = [c for c in CATEGORIES if c not in present]
    return updated


def validate_revision(event):
    before = next((c for c in event.before.claims if c.id == event.claim_id), None)
    after = next((c for c in event.after.claims if c.id == event.claim_id), None)
    if before is None or after is None or before.category == after.category:
        raise ValueError('Invalid category revision target')
    if any(c.claim_type not in ('paper_report', 'user_observation') for c in event.before.claims):
        raise ValueError('Invalid category revision claim type')
    if not review_paper(event.before).approved or not review_paper(event.after).approved:
        raise ValueError('Invalid category revision evidence')
    if event.after != set_category(event.before, event.claim_id, after.category):
        raise ValueError('Invalid category revision: only category and coverage may change')


def replay_revisions(papers, events):
    """Reapply only to the same source, claim content and cited evidence.

    Extraction timestamps can differ; other claim attributes must match.
    Historical entries for absent or changed evidence remain audit records only.
    """
    result = list(papers)
    for event in events:
        old = next(c for c in event.before.claims if c.id == event.claim_id)
        new = next(c for c in event.after.claims if c.id == event.claim_id)
        old_source = event.before.document.source
        old_evidence = [e for e in event.before.evidence if e.id in old.evidence_ids]
        for i, paper in enumerate(result):
            source = paper.document.source
            if (source.id, source.sha256, source.uri) != (old_source.id, old_source.sha256, old_source.uri):
                continue
            current = next((c for c in paper.claims if c.id == event.claim_id), None)
            if current is None or current.model_dump(exclude={'timestamp'}) != old.model_dump(exclude={'timestamp'}):
                continue
            if [e for e in paper.evidence if e.id in current.evidence_ids] != old_evidence:
                continue
            result[i] = set_category(paper, event.claim_id, new.category)
    return result
