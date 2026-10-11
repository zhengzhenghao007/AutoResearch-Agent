# P2 citation registry increment

Derive a read-only registry from validated ResearchRun v1 snapshots, using
standalone output contracts. API and CLI use the same pure builder. No snapshot
migration, dependency, external lookup, new storage, or frontend change.

Source order follows persisted papers; evidence and claims retain their original
order. Generated claims are included per source when their evidence references
intersect that source, preserving the full original reference list and claim
type. No grouping by title or assumed bibliographic identity occurs.

An arXiv revision is recognized only from a strictly matched stored URL with an
explicit vN suffix. Unversioned and unrecognized links retain their URI but have
null revision identifiers. This does not claim the remote metadata was verified.

Tests cover revision parsing, upload provenance, exact quotations, generated
suggestions, source separation, deterministic output, unchanged snapshots and
mtime, original API compatibility, API/CLI equality, missing records, and corrupt
snapshot rejection. Human review and representative scientific evaluation remain
pending. DOI/BibTeX, multi-source identity, inclusion/exclusion and semantic review
remain later P2 work.

Verification: 114 Python tests passed (one existing dependency deprecation
warning); seven evaluator regressions passed with zero reviewed samples and null
metrics. Independent code review found no blockers. Frontend code is unchanged.
