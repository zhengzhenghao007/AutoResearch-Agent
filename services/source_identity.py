"""Read-only identity state, distinct from citation and BibTeX contracts."""
from schemas.source_identity import CurrentSourceIdentity, IdentitySourceSnapshot, IdentityConflict, SourceIdentities
from services.research_validation import validate_run


def build_source_identities(run):
    validate_run(run)
    snapshots = {p.document.source.id: IdentitySourceSnapshot(
        id=p.document.source.id, sha256=p.document.source.sha256,
        uri=p.document.source.uri, title=p.document.source.title) for p in run.papers}
    active = set(snapshots)
    latest = {}
    for event in run.source_identity_annotations:
        snapshots.setdefault(event.source_id, event.source)
        latest[event.source_id] = event.doi
    sources, groups = [], {}
    for source_id, snapshot in snapshots.items():
        doi = latest.get(source_id)
        sources.append(CurrentSourceIdentity(source=snapshot, active=source_id in active,
            doi=doi, provenance='user_supplied' if doi is not None else None))
        if doi is not None and source_id in active:
            groups.setdefault(doi, []).append(source_id)
    return SourceIdentities(run_id=run.id, sources=sources,
        conflicts=[IdentityConflict(doi=doi, source_ids=ids) for doi, ids in groups.items() if len(ids) > 1])
