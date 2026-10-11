# Read-only duplicate clues

`GET /api/research/runs/{run_id}/source-duplicates` and
`python research_cli.py source-duplicates RUN_ID` share a deterministic builder.
The report does not write snapshots, merge/delete sources, filter by screening
annotations, or change selection, citation JSON or BibTeX.

Groups have independent kinds: `exact_arxiv_identifier` for candidate IDs with
the same strictly recognized literal arXiv identifier; `same_pdf_bytes` for
processed source IDs sharing stored full SHA-256 metadata; and
`shared_user_supplied_doi` for current active DOI conflicts. The last is explicitly
`user_supplied_unverified`, not a verified equivalence. Clear and absent historical
sources do not contribute current DOI groups. Groups contain at least two members.

Unversioned, v1 and v2 arXiv identifiers remain separate. No title matching,
network lookup, DOI/arXiv equivalence inference or cross-kind transitive merging
occurs. Candidate-to-source arXiv matches appear separately in
`candidate_source_links`: a candidate and its processed source are not counted
as duplicate papers. Group kinds and member order are deterministic.

Normal search already deduplicates normalized URLs; normal PDF processing uses
content hashes as source IDs and suppresses repeated content. Consequently groups
may be empty. Historical candidates and valid externally constructed v1 snapshots
can still carry clues. Hash groups compare stored metadata, without reopening or
rehashing original PDF bytes, and do not establish authenticity or paper identity.
Every report validates the entire run first; corrupt snapshots are rejected.
No schema migration is required. Human scientific evaluation remains unfinished
and is skipped at the user's request; the offline review editor is not implemented.
