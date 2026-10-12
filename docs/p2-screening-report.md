# Screening audit export

Read the saved candidate annotations with
`GET /api/research/runs/{run_id}/screening-report` or
`python research_cli.py screening-report RUN_ID`.
The CLI writes JSON to stdout, so it can be redirected to a report file.

The report preserves candidate order, metadata and each candidate's complete
decision history. The last appended event is authoritative, regardless of its
timestamp. Candidates without events are `undecided`; no decision is inferred.
Counts cover the current candidates and their latest decisions, not historical
events, uploaded papers or a systematic-review population.

Selection stays independent of screening. `selected_for_analysis` means the ID
is in the saved explicit selection; it does not prove that a download or analysis
succeeded. Notices identify `excluded_but_selected`, `included_but_not_selected`
and `selected_without_decision`. These are informational, never automatic
changes to eligibility, selection, downloads or exports.

The builder validates the full research record and fails on invalid references.
Old records without decision history produce undecided candidates. Reading the
report does not migrate or rewrite snapshots. No reviewer identity, scientific
assessment or semantic-validation result is inferred from a user annotation.

The evidence workspace offers Load screening report and Download screening JSON.
It displays saved counts, decision history and selection notices. Unsaved checkboxes
and drafts are not included. Starting any record mutation clears the report, even
when a write fails; load it again explicitly afterward.
