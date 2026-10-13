# Explicit category revisions

The workspace, API and CLI lets a user correct a currently processed claim's category
without changing its text, type, timestamp, evidence references or source. It
does not certify the new classification or scientific validity.

POST `/api/research/runs/{run_id}/category-revisions` with:

```json
{
  "expected_claim": {"id":"...","text":"...","category":"experiment","claim_type":"paper_report","evidence_ids":["..."],"created_by":"...","timestamp":"..."},
  "category": "future_work",
  "reason": "The quotation describes planned work."
}
```

Use the exact current Claim object from `GET /api/research/runs/{run_id}`.
For CLI use, save that object as UTF-8 JSON, then run:

```text
python research_cli.py revise-category RUN_ID expected-claim.json future_work --reason "The quotation describes planned work."
```

The returned ResearchRun includes `category_revisions`: append-ordered events
with the claim ID, reason, timezone-aware revision time and complete before/after
PaperEvidence snapshots. The history preserves the original quotation, evidence,
source metadata and parsed pages for inspection even if the source is later
removed from the active selection. Snapshot reads validate that every historical
change was category-only and that its quotations match its saved page text.
This checks internal consistency, not tamper-proof authenticity of stored files.

Each run permits at most 20 revisions; invalid/no-op requests do not consume the
budget. Reverting a category is another explicit revision. A mismatched expected
Claim is rejected as stale. Missing claims, empty reasons, and exhausted budgets
fail without rewriting the file. The store remains single-user; this comparison
is not a concurrent transaction or multi-process lock.

Changing a category recomputes missing categories, generated suggestions, summary
artifacts and the existing literal-support review before saving atomically.
Planning-language flags are derived on the next read and may disappear after a
change to future_work; disappearance does not establish scientific correctness.

When analysis re-extracts a selected source, history is replayed in append order
only where source ID/hash/URI, prior claim attributes (excluding extraction
timestamp) and its cited evidence match. Changed or absent evidence is not
overridden. Historical snapshots are never rewritten, and reading history does
not itself reapply revisions. Old runs without history read as an empty list.

Full paper snapshots intentionally favor inspectability over compact storage;
each revision stores two copies of the paper's parsed text. The 20-event budget
bounds event count but large PDFs can still make snapshots substantial. A compact
audit store remains follow-up work. The workspace editor requires a reason, shows
the remaining budget and full history, and preserves drafts after failed saves. Human scientific evaluation
remains incomplete and is not inferred from an API user's correction.
