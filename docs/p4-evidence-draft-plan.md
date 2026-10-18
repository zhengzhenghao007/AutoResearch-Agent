# P4 first increment: evidence-linked draft preview

2026-10-19. User authorizes feature development and verified merge into main.
Purpose: assemble a reviewable chapter outline from saved evidence, without
inventing prose, results, citations or scientific approval. This is the first P4
increment, not all P4. No model, external service or paid call is needed.

Five deterministic sections: background, reported methods, reported findings,
user observations and limitations/future directions. Paper claim text is retained
verbatim with claim ID, source identity/hash/URI, all bound evidence quotes and
pages. P3 statistics produce explicitly descriptive summary blocks bound to
dataset hash, column and full observation references. Missing sections/columns
have explicit placeholders; paper results never fill user results.

The read-only preview includes an input SHA-256 and schema/builder version.
Revalidate current ResearchRun before building. No stored state, approval, revision
history or publication-ready export is added. Contradiction review and scientific
validation stay not_assessed. A later P4 increment will provide editable narrative,
saved revision history, review linkage and explicit human approval before export.

Implementation: schemas/manuscript_draft.py, services/manuscript_draft.py,
GET /api/research/runs/{id}/manuscript-draft, CLI manuscript-draft RUN_ID,
frontend ManuscriptDraft preview with stale-response and mismatched-run protection.
No changes to source data or saved ResearchRun schema.

Tests: empty records, paper-only vs experimental results, all-null columns,
quote/source/compute bindings, altered snapshot rejection, deterministic hashes,
read-only file contents/mtime, API/CLI, explicit UI loads and revision/navigation.
Independent review, Python/frontend suites and CI precede merge.
