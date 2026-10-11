# Candidate screening history

This bounded P2 increment records user-supplied candidate screening annotations.
Each event contains `candidate_id`, `decision` (`include` or `exclude`), `reason`
(1–2000 characters after trimming surrounding whitespace), and a server-generated
timezone-aware `decided_at`. Events are appended in recording order; recording a
revised decision preserves all earlier events. The last event for a candidate is
its latest annotation. No event means no recorded screening decision.

## API and CLI

`POST /api/research/runs/{run_id}/candidate-decisions` accepts:

```json
{"candidate_id": "CANDIDATE_ID", "decision": "exclude", "reason": "Different experimental protocol"}
```

The response is the updated ResearchRun. `GET /api/research/runs/{run_id}` exposes
the same `candidate_decisions` history. Clients cannot supply timestamps or
reviewer identities. Invalid bodies return 422, unknown candidates return 400,
and missing runs return 404. Invalid writes leave the previous snapshot intact.

```powershell
python research_cli.py candidate-decision RUN_ID CANDIDATE_ID include --reason "Relevant navigation method"
python research_cli.py show RUN_ID
```

Both interfaces use the same workflow and atomic validated snapshot store.
Recording an annotation performs no download, extraction, or model call.
Repeated submissions append repeated events; this endpoint is not idempotent.

## Meaning and compatibility

Annotations do not control execution: `include` does not select or download a
paper, and `exclude` does not block an explicitly requested analysis or remove
previously processed papers. Analysis continues to use explicit `selected_ids`.
Annotations survive subsequent analysis and upload. Citation exports are unchanged.

ResearchRun remains version 1 with an additive field defaulting to an empty list.
This implementation can read old snapshots without migrating or rewriting them
on read. Older software with strict schemas cannot read newly written snapshots
containing this field; backward readability is not promised.

History is append-only through the supported workflow, not a tamper-proof audit
log. The local single-user store has no authenticated reviewer identity or
multi-writer transaction isolation. User-supplied screening reasons do not certify
scientific validity, semantic support, or completion of human evaluation. Uploads
are not search candidates and cannot receive these candidate annotations.

## Validation scope

Focused tests cover old snapshot reads, ordered revisions, reload, invalid writes,
corrupt candidate references, unchanged analysis and citation semantics, and real
API/CLI persistence. The full offline Python suite is required before delivery.

Verification (2026-09-27): 122 Python tests passed, including eight new cases;
the follow-up upload-history assertion also passed in the focused suite. Seven
evaluator regressions passed with zero human-reviewed samples and null metrics.
Independent code review found no blockers. ChatGPT read the implementation and
released test output and returned DONE for task `c2c_b47a`, iteration 1.
