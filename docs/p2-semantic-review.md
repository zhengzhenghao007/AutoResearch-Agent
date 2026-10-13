# Explicit semantic review

The workspace offers an optional model support/contradiction review. Select 1–20
processed paper claims, then explicitly consent to sending claim text, source
metadata, quotations and complete cited pages to the configured model provider.
Normal record reads and rule-based review remain offline. Provider charges may apply.

API: POST `/api/research/runs/{run_id}/semantic-review` with
`{"claim_ids":["claim-id"],"allow_model":true}`.

CLI: `python research_cli.py semantic-review RUN_ID CLAIM_ID --allow-model`.
Multiple claim IDs can be supplied. Configure the existing LLMClient provider first.

One provider call uses a 60-second timeout, zero automatic retries and a 6000-token
output budget. Input JSON is capped at 50000 characters. Oversized inputs fail
before provider initialization; select fewer claims. Failed requests do not change
the record. A timed-out request may still incur provider usage.

Responses must include each selected claim exactly once and reference only that
claim's bound evidence IDs. Contradiction pairs must contain two distinct selected
claims with no repeated or reversed pair. Invalid JSON, IDs or oversized output
are rejected without repair calls. Reports include the exact input snapshot,
SHA-256, model, timestamp and omitted-claim count. Download JSON to retain a report;
it is not persisted to the research record.

Supported/unsupported/uncertain are model judgments of contextual support and
category, not scientific truth. Contradictions are potential conflicts requiring
matching methods and conditions. Scientific validation always remains
`not_assessed`. No findings does not prove consistency. Corrections are explicit,
category-only revisions with reasons and a 20-event budget; no model edits occur.

The frontend preserves an outstanding request across failed annotation attempts,
blocks overlapping calls, and discards obsolete output after successful revisions.
Automated tests use mocked model responses. Live provider compatibility and semantic
accuracy on representative human-labeled papers have not been validated. Human
scientific evaluation was skipped at the user's request, not passed.
