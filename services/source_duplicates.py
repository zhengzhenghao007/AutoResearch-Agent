"""Exact independent clues only; never merge entities or rewrite a run."""
from schemas.source_duplicates import DuplicateMember, DuplicateGroup, CandidateSourceLink, SourceDuplicateReport
from services.arxiv_identity import recognized_arxiv_identifier
from services.source_identity import build_source_identities


def build_source_duplicates(run):
    # This view validates the complete run before deriving active DOI state.
    identities = build_source_identities(run)
    candidates, hashes, sources_by_arxiv = {}, {}, {}
    sources = {}
    for candidate in run.candidates:
        identifier = recognized_arxiv_identifier(candidate.pdf_url)
        if identifier:
            candidates.setdefault(identifier, []).append(DuplicateMember(
                entity_type='candidate', entity_id=candidate.id, title=candidate.title, uri=candidate.pdf_url))
    for paper in run.papers:
        source = paper.document.source
        member = DuplicateMember(entity_type='processed_source', entity_id=source.id, title=source.title, uri=source.uri)
        sources[source.id] = member
        hashes.setdefault(source.sha256, []).append(member)
        identifier = recognized_arxiv_identifier(source.uri)
        if identifier:
            sources_by_arxiv.setdefault(identifier, []).append(source.id)
    groups = []
    for kind, status, mapping in (
        ('exact_arxiv_identifier', 'explicit_identifier', candidates),
        ('same_pdf_bytes', 'exact_content_hash', hashes),
    ):
        groups.extend(DuplicateGroup(kind=kind, identity_status=status, identity_value=value, members=members)
                      for value, members in mapping.items() if len(members) > 1)
    groups.extend(DuplicateGroup(kind='shared_user_supplied_doi', identity_status='user_supplied_unverified',
                                identity_value=conflict.doi, members=[sources[id] for id in conflict.source_ids])
                  for conflict in identities.conflicts)
    links = [CandidateSourceLink(candidate_id=candidate.id, source_id=source_id, arxiv_identifier=identifier)
             for candidate in run.candidates
             if (identifier := recognized_arxiv_identifier(candidate.pdf_url))
             for source_id in sources_by_arxiv.get(identifier, [])]
    return SourceDuplicateReport(run_id=run.id, groups=groups, candidate_source_links=links)
