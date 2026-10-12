# Advisory claim review

Run `python research_cli.py claim-review RUN_ID` or read
`GET /api/research/runs/{run_id}/claim-review` to inspect saved claims for a narrow
class of classification risks. The CLI writes JSON that can be redirected to a file.

Version `planning-language-en-v1` checks experiment and result claims for the
English phrases `future work`, `future research`, `we plan to`, `we intend to`,
and `we will` followed by evaluate/test/investigate/measure/conduct/perform/study.
Matching is case-insensitive and permits whitespace between words. At most one
flag is emitted per claim, carrying the first matched phrase, the full claim,
source ID and all cited evidence (including page numbers and quotations).

For example, an `experiment` claim saying “We will evaluate this method on
additional data” receives a planning-language flag. A claim already classified
as `future_work` is outside the checked categories and is not flagged.

This is an advisory lexical check, **not semantic validation**. A sentence may
legitimately discuss completed work alongside future plans. Other wording and
languages may be missed, and absence of a flag is never approval. The report
always states `semantic_validation: not_assessed`. It does not assess scientific
truth, contradictions, entailment, or whether an experiment actually occurred.

`claim_count` counts paper-level claims; `checked_claim_count` counts the subset
in experiment/result categories; `flagged_claim_count` counts flagged claims.
Generated run-level suggestions are excluded. Existing literal-support review
and extraction behavior remain unchanged. Reads validate the complete snapshot
and never rewrite claims, categories, review state, suggestions or artifacts.

The evidence workspace also provides **Load claim review** and **Download claim
review JSON**. The panel shows counts, matched phrases and all cited quotations
with source IDs and page numbers. Empty results explicitly do not mean semantic
approval. Starting a record mutation clears the loaded report, even if the write
fails; switching record or revision discards late responses. Reads leave drafts
and selections untouched. Correction history and broader semantic review remain
future work. Real human scientific evaluation
is still incomplete; synthetic tests check behavior, not scientific accuracy.
