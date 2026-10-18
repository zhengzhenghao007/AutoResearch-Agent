# P3 completion — 2026-10-17

The user requests completion of P3 and already authorizes implementation, tests,
GitHub upload and merge. Human scientific evaluation remains skipped/unverified.

Keep the independent user-observation store from the initial JSON increment.
Deliver the remaining roadmap scope without statistical inference or fabricated
results: CSV + explicit metadata, offline new records, webpage import/inspection,
descriptive statistics and cell-level provenance exports. P4 prose is not P3.

## Interfaces and ownership

1. CSV parser task: schemas/experiments.py, services/experiments.py and dedicated
   tests. Strict comma CSV, explicit header sample_id then declared columns,
   empty numeric cell means missing. Exact CSV plus metadata form an import
   envelope; hash the envelope for dataset identity and hash original CSV
   separately. Reparse envelopes on snapshot load/save. CSV <=1MiB, envelope
   <=2MiB, 1000 rows, 50 columns, 20 datasets. JSON imports retain existing hashes.
2. Statistics task: independent schema/service/test modules. Validated runs,
   per-column observed/missing counts, mean, extrema, sample SD (n-1), explicit
   insufficient/missing states. Decimal strings with documented deterministic
   rounding; preserve exact input references as dataset hash, sample ID, column
   and value. No imputation, p-values, independent-sample assumptions or model.
3. Integration/UI: offline create, existing JSON and new CSV upload, metadata
   entry, shared serialized writes, durable failure drafts, stale report guards,
   raw input view/download, completeness/stats and provenance JSON export.

Tests must cover malformed/ragged CSV, duplicate keys/IDs, unknown metadata,
exact raw byte recovery, near-limit numerics, missing vs zero, atomic failures,
unchanged paper derivatives, UI retries/drafts/navigation, and end-to-end API/CLI.
Parallel tasks edit disjoint files. Root integrates after their interfaces land.
Final independent review and complete offline suites precede GitHub CI and merge.

Completion means engineering capability, not proof that uploaded data are real
or scientific interpretation is valid. JSON remains a trusted single-user store.

## Validation and review

API/CLI integration, browser offline creation, CSV import, refresh persistence,
exact original byte download and statistics/reference export were exercised.
No model or real experimental data was used. Independent review found one
important boundary issue: CSV metadata envelopes could exceed the JSON transport
limit. API/CLI/UI now accept envelopes up to 2 MiB while the parser keeps ordinary
JSON and original CSV at 1 MiB. Dedicated API/CLI and UI regressions reproduced
the issue before the fix and passed afterward. No other important findings.
Mean/SD rounding, extreme values, missing data, integrity failures and atomic
write failure are covered by offline regression tests.
