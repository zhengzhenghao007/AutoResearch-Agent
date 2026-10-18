# P3 observation import: design and implementation plan

Historical initial plan (2026-10-14), completed as part of the expanded
[P3 completion plan](p3-completion-plan.md) on 2026-10-17.
Goal: import explicit numeric user observations without inventing results or
mixing them with paper evidence. The initial increment below was expanded before delivery.
User has authorized autonomous implementation, verification and merge.

Architecture: add independent experiment contracts to ResearchRun, a shared
parser/import/report service, and upload/read API plus CLI commands. Reuse atomic
snapshot validation. Old runs default to an empty experiments list. No model,
new dependency, external network, generated Claim or statistical inference.

Input: UTF-8 JSON, optional BOM, at most 1 MiB; title, optional protocol and
statistical_method, 1–50 numeric columns (name, optional unit), 1–1000 rows
(unique sample_id and exactly the declared value keys). Values are finite JSON
numbers or null; no coercion from strings or booleans. Reject duplicate JSON keys,
duplicate names/IDs, nonfinite numbers and ragged rows. Null means missing;
zero is observed. Each row is one user-declared sample, not verified independence.

Store exact input text, SHA-256 of original UTF-8 bytes, parsed input, import
timestamp and fixed user_observation/user_data labels. Revalidate hash and parsed
equivalence on save/load. Up to 20 datasets per run; exact duplicate bytes reject.
Corrections are new imports, never overwrites. This is integrity checking, not
proof of authenticity. No arbitrary server paths through HTTP.

Report: run ID, per-dataset hash and metadata, sample count, nonmissing/missing
counts by column, missing protocol/method/unit notices, scientific_validation
not_assessed. Read-only; no guessed units, imputation, means or significance.

Review focus: stale or tampered snapshots; duplicate JSON keys; booleans/numeric
strings/nonfinite values; missing values versus zero; failed imports leaving disk
unchanged. Tests cover all five.

## Task 1: Complete JSON observation ingestion

- [x] Write tests/test_experiments.py for import/report, parser rejection,
  integrity, old-run compatibility, API and CLI. Run and observe missing behavior.
- [x] Add schemas/experiments.py and services/experiments.py; integrate
  schemas/research.py and services/research_validation.py.
- [x] Add multipart POST /runs/{run_id}/experiments and GET on the same path;
  add import-experiment RUN_ID PATH and experiments RUN_ID CLI commands.
- [ ] Run targeted tests then full Python suite; document input example and
  remaining P3 scope. Independent code review, fix findings, commit and push.
- [ ] Merge only after GitHub checks pass, then sync main and confirm clean tree.

Pre-flight: one task with shared parser/store interfaces; no parallel writers.
Implementation stays in the clean checkout on a dedicated codex branch.
