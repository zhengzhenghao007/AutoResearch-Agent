# P4 evidence-linked chapter preview

This first increment produces read-only drafting material from a validated saved
record. It is an outline with attributed quotations and descriptive summaries,
not a finished manuscript. It does not save versions, perform semantic review or
claim human approval. Full P4 remains in progress.

In the workspace choose **Preview chapter draft**. CLI:

```text
python research_cli.py manuscript-draft RUN_ID
```

API: GET `/api/research/runs/{run_id}/manuscript-draft`.
API/CLI JSON is an inspection preview, not an approved publication export.
All entry points are offline and read-only; no model call or file rewrite occurs.

The five sections are background, reported methods, reported findings, user
observations, and limitations/future directions. Saved paper categories determine
placement; category correctness is not inferred from literal quotation support.
Each paper block retains exact saved claim text, claim ID, source/hash/URI, every
bound evidence quote/page and document coverage/truncation. Separate user-data
blocks use descriptive-v1 statistics with dataset hash, column and complete
sample/value references. Missing/all-null data stay placeholders. Paper results
never fill an absent user-results section, and generated suggestions are not
presented as factual findings. Legacy user_observation Claims inside PaperEvidence
are omitted and counted; structured P3 datasets provide user-result material.

The builder and schema version plus input_sha256 identify the material. The hash
uses sorted-key compact UTF-8 JSON of topic, complete paper snapshots and complete
experiment snapshots. It is a content binding, not proof of source authenticity.
Mean/SD precision and interpretation follow [P3](p3-observations.md); no significance
testing, unit conversion, experimental independence or causal conclusion is added.

The UI clears the preview on record writes/revisions/navigation and ignores stale
responses. Source and statistics text is rendered as text, not HTML. Up to 100
observation references per column are shown inline; full references remain in the
API/CLI preview and P3 statistics export. Scientific validation and contradiction
review always remain not_assessed; approval remains not_requested.

Remaining P4: narrative editing, persistent revision history, linking explicit
contradiction review to the exact draft, and human approval of an exact version
before final manuscript export. Permission to merge code is not manuscript approval.
