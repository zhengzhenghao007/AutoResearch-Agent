# Conservative BibTeX export

`GET /api/research/runs/{run_id}/bibtex` returns JSON with `run_id`, `bibtex`
and `skipped_sources`. The CLI emits UTF-8 BibTeX to stdout:

```powershell
python research_cli.py bibtex RUN_ID > references.bib
```

Use a UTF-8-capable shell redirection (older Windows PowerShell may transcode
native output). Skipped-source diagnostics go to stderr. A successful export
with no eligible sources has empty stdout and exit status 0; missing/corrupt
records fail with nonzero status. API missing runs return 404 and invalid
snapshots return 400.

Only processed paper sources with strictly recognized arXiv URIs are exported.
Each `@misc` entry contains the stored title, literal arXiv identifier as `eprint`,
`archivePrefix = {arXiv}`, and canonical arXiv abstract URL. Explicit `vN` suffixes
are preserved; unversioned identifiers remain unversioned. No author, DOI, year,
journal or other unknown metadata is inferred, including from candidate authors
or dates encoded in identifiers. Stored titles may be user supplied; they are
not independently verified publication metadata.

Local uploads and unrecognized URIs are skipped with
`missing_bibliographic_identity`. Search-only candidates are not export sources.
Screening decisions do not filter exports: this is a view of processed provenance,
not an automatically approved bibliography.

Entry order follows persisted source order. Citation keys are `source_` followed
by the UTF-8 hexadecimal encoding of the complete source ID. This is deterministic,
title-independent and preserves distinct legacy IDs even when content hashes match.
Titles escape TeX special characters and normalize whitespace; Unicode remains
UTF-8 and requires compatible bibliography/TeX tooling.

The builder derives from the validated citation registry with no network or model
calls. It changes no snapshots, citation registry fields, or research schema.
Repeated exports are identical and leave snapshot contents and mtime unchanged.
This is a minimal export, not complete bibliographic metadata or scientific review.
Human scientific evaluation remains pending.

Verification (2026-09-27): 138 offline Python tests passed, including 16 new
BibTeX cases; seven evaluator regressions passed with zero reviewed samples.
Independent code review found a lone-title-brace defect, reproduced by failing
tests and fixed with balanced text-brace macros before the final full suite.
ChatGPT independently read the final changes and released test output and returned
DONE for `c2c_d92f`, iteration 1. No merge or scientific acceptance is implied.
