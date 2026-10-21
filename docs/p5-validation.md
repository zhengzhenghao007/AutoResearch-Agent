# P5 validation — 2026-10-21

Local verification on Windows / Python 3.12:

- `python -m pytest tests -q`: **339 passed, 1 skipped**. The skipped test executes
  Linux resource-limit assertions in a disposable process and runs in Linux CI.
- `npm test`: **90 passed**; lint, type checking and production build passed.
- SQLite tests include two real writer processes, rollback revision invalidation,
  atomic run/manuscript rollback, approval invalidation and migration preservation.
- Security tests cover authentication before body reading, writer/reader permissions,
  cross-user run/manuscript/job isolation, hostile local Host/client rejection,
  request deadline/admission and unsupported deployment platform rejection.
- Job tests cover persisted queues, stale source rejection, cancellation without
  commit, expired leases, bounded/idempotent retries, queue capacity, successful
  disposable subprocess output and termination of a real sleeping child.
- Headless Chromium at desktop and 390-pixel mobile widths verified login,
  account switching, empty other-user history, cancellation/retry, explicit result
  opening, persisted jobs after reload, memory-only credentials and reader controls.
  No page errors or horizontal overflow. Job results and credentials were synthetic;
  browser tests made no real literature/provider calls.
- Independent code review identified a rollback revision reuse bug. The fix invalidates
  every snapshot read/saved inside a rolled-back transaction; both retained-object
  paths have regression coverage. Follow-up review found no remaining important issues.
- `python -m evaluation.evaluate_evidence`: 7 fixture regressions passed;
  **0 reviewed, 7 pending, metrics null**. Human scientific assessment remains skipped
  at the user's request, not passed. No paid model calls were performed.

GitHub's Python 3.11/3.12 and frontend checks must pass on the PR commit before merge.
See the PR check results for the Linux run, and [deployment limits](p5-deployment.md)
for the supported one-host/one-worker configuration and operator responsibilities.
