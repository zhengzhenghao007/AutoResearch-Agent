"""Deterministic citation views derived from validated evidence, with no I/O."""
from schemas.research import ResearchRun
from schemas.citation_registry import (
    CitationRegistry, CitationSourceEntry, CitationEvidenceRef, CitationClaimRef,
)
from services.arxiv_identity import explicit_arxiv_revision_id
from services.research_validation import validate_run


def build_citation_registry(run: ResearchRun) -> CitationRegistry:
    validate_run(run)
    claims = [claim for paper in run.papers for claim in paper.claims] + run.generated_claims
    entries = []
    for paper in run.papers:
        source = paper.document.source
        evidence_ids = {item.id for item in paper.evidence}
        entries.append(CitationSourceEntry(
            source_id=source.id, sha256=source.sha256, title=source.title,
            kind=source.kind, uri=source.uri,
            arxiv_revision_id=explicit_arxiv_revision_id(source.uri),
            evidence=[CitationEvidenceRef(id=e.id, page=e.page, quote=e.quote) for e in paper.evidence],
            claims=[CitationClaimRef(id=c.id, text=c.text, category=c.category,
                    claim_type=c.claim_type, evidence_ids=list(c.evidence_ids))
                    for c in claims if evidence_ids.intersection(c.evidence_ids)],
        ))
    return CitationRegistry(run_id=run.id, topic=run.topic, sources=entries)
