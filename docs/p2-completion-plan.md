# P2 completion plan — 2026-10-14

User authorizes implementation, validation and merge into main without a separate
approval gate. Human scientific evaluation is explicitly skipped, not passed.

1. Category revision UI: show current paper claims, category-only editor, required
   reason, remaining budget and complete before/after audit history. Use existing
   serialized annotation writes and exact expected Claim. Preserve drafts after
   failure, isolate records, leave quotations read-only. Add frontend regressions.
2. Semantic support/contradiction review: optional clarification received no answer; proceeding with an
   explicit model call using the existing LLM client, default offline, bounded
   input/output, grounded IDs, no automatic edits. Do not mark heuristic or model
   review as scientific verification. Provide API/CLI and UI with failure states.
3. Run full regression and independent review, update the roadmap with engineering
   completion versus unverified scientific evaluation, push and merge after CI.

P2 does not imply P3 experimental data import or P4 manuscript writing. Existing
DOI annotations and duplicate clues remain conservative; unverified identities
must not become externally verified bibliographic facts.
