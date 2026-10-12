"""Bounded, deterministic review cues without modifying accepted snapshots."""
import re
from schemas.research import ResearchRun
from schemas.claim_review import ClaimReviewFlag, ClaimReviewReport
from services.research_validation import validate_run


PLANNING = re.compile(
    r'\b(?:future\s+(?:work|research)|we\s+(?:plan|intend)\s+to|'
    r'we\s+will\s+(?:evaluate|test|investigate|measure|conduct|perform|study))\b',
    re.IGNORECASE,
)


def build_claim_review(run: ResearchRun) -> ClaimReviewReport:
    run = ResearchRun.model_validate(run.model_dump())
    validate_run(run)
    flags = []
    total = checked = 0
    for paper in run.papers:
        evidence = {item.id: item for item in paper.evidence}
        for claim in paper.claims:
            total += 1
            if claim.category not in ('experiment', 'result'):
                continue
            checked += 1
            match = PLANNING.search(claim.text)
            if match:
                flags.append(ClaimReviewFlag(
                    claim_id=claim.id, source_id=paper.document.source.id,
                    category=claim.category, claim_text=claim.text, matched_text=match.group(),
                    evidence=[evidence[id] for id in claim.evidence_ids],
                ))
    return ClaimReviewReport(run_id=run.id, claim_count=total, checked_claim_count=checked,
                             flagged_claim_count=len(flags), flags=flags)
