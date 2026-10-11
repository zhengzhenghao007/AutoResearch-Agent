# User-supplied DOI annotations

Explicitly associate a processed source with a DOI without claiming that it was
resolved or verified. No network requests, model calls, metadata enrichment or
DOI/arXiv equivalence inference occur. Citation registry and BibTeX remain unchanged.

```powershell
python research_cli.py source-doi RUN_ID SOURCE_ID set --doi "https://doi.org/10.1234/example" --reason "Printed on publisher page"
python research_cli.py source-doi RUN_ID SOURCE_ID clear --reason "Incorrect association"
python research_cli.py source-identities RUN_ID
python research_cli.py show RUN_ID
```

`POST /api/research/runs/{run_id}/source-identities` accepts `source_id`, `action`
(`set` or `clear`), `doi` (required for set, absent/null for clear) and `reason`
(1–2000 characters). It returns the updated run. Invalid bodies return 422,
unknown/inactive sources 400, and missing runs 404. Only processed sources may
receive events; search candidates alone cannot. Repeated submissions append events.

`GET /api/research/runs/{run_id}/source-identities` returns current sources followed
by historical absent sources, current DOI values, explicit `user_supplied`
provenance, and duplicate assignments among active sources. Clear yields null DOI
and provenance. Duplicate values never merge papers. Full ordered event history
is available in `source_identity_annotations` on the run.

Each event captures its source ID, content hash, URI and title, plus a server time.
Clients cannot supply those snapshot fields or timestamps. Reanalysis still replaces
unselected papers normally: their history remains visible with `active=false`.
This means only "absent from the current processed-paper set". Reprocessing a source
with matching ID/hash/URI makes its latest history active again, including a clear.
Historical annotations cannot be edited while their source is absent. Title changes
alone do not break binding. Inconsistent ID/hash/URI bindings fail validation rather
than silently rebinding annotations. This can reject reanalysis when identical bytes
are presented under a different URI for an already annotated source; the previous
snapshot stays intact. No authenticity or tamper-proof guarantee is provided.

## Supported input subset

Accept bare `10.` + 4–9 ASCII digits + `/` + a nonempty suffix containing only
ASCII letters, digits, `-._;()/:`, or that string prefixed exactly with
`https://doi.org/`. Outer whitespace is trimmed and ASCII letters lowercased.
Input length is limited to 2048 characters. Queries, fragments, percent-encoding,
other hosts, credentials, ports and arbitrary publisher URLs are rejected.

This is an intentionally conservative application subset, not exhaustive DOI
syntax validation: some real DOIs are unsupported. ASCII case-insensitive comparison
follows the [DOI Handbook](https://www.doi.org/doi-handbook/html/); the application's
character and length restrictions are narrower than the standard. A successful
input check establishes neither registration nor association with the source.

## Compatibility and limits

Old ResearchRun v1 snapshots default to empty history and are not rewritten on read.
Older strict software may reject newly written snapshots with the additive field.
History is append-only through this workflow, not authenticated review or a signed
audit log. The store remains single-user without concurrent-writer isolation.
Human scientific evaluation remains pending. An uploaded PDF with a user-provided
DOI still follows the existing BibTeX skip policy.

Validation (2026-09-28): 155 offline Python tests passed, including 17 identity
cases; seven evaluator regressions passed with zero human-reviewed records and
null metrics. Independent code review found no blockers. ChatGPT read the final
implementation and released test output and returned DONE for `c2c_e63a`, iteration 1.
