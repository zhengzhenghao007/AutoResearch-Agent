# Research task reports implementation plan

**Goal:** Export a portable, source-bound research task report without inventing conclusions.
**Architecture:** A read-only report builder consumes a task snapshot and its current run. JSON carries checkpoints and resolved quotations; Markdown presents the same data. A GET endpoint and task-panel downloads reuse existing authentication and request locking.
**Tech stack:** Python, FastAPI, React, existing test tooling; no dependencies.
**Design:** Continue the user-authorized execution chain with an exportable handoff. Prefer deterministic report assembly over model-written synthesis, which would introduce unvalidated scientific claims. Reports are working notes, not approved manuscript exports. Keep original research records unchanged. Stale sources suppress resolved quotations, but retain checkpoint IDs and warnings for audit.

## Review focus
- Stale sources must not resolve old IDs against new text.
- Pending retrieval must not masquerade as source-checked evidence.
- Untrusted titles, quotes and questions must remain literal Markdown text.
- Late responses after record switches must not trigger downloads.
- Read-only users may export; other tenants may not access the record.

## Task 1: report service and API
- [x] Add failing tests for completed, pending, stale, missing evidence, literal Markdown and API isolation.
- [x] Implement `build_task_report(task, run)` and `render_task_report(report)` in `services/research_task_reports.py`; expose GET `/{task_id}/report?format=json|markdown`.
- [x] Run task/report tests; verify exports do not execute steps or change the source record.

## Task 2: task-panel downloads
- [x] Add failing tests for read-only export, failed export and late response suppression.
- [x] Add authenticated Blob client method and JSON/Markdown download buttons using panel request lock.
- [x] Run frontend tests, lint, types and production build; update user guide.

## Integration
- [ ] Push PR and merge after full backend regression and CI pass under existing user authorization.

