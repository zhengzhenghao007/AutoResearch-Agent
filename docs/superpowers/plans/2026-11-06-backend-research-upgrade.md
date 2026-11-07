# Backend research agent upgrade implementation plan

Goal: integrate saved-paper analysis, optional model reasoning, acquisition and supervision into the existing research workbench. Preserve legacy APIs, data and explicit model consent.
Architecture: extend the existing versioned task executor for deterministic research stages; isolated services own model generation and acquisition journals. Never equate source matching with scientific validity.
Tech stack: existing Python/Pydantic/FastAPI/SQLite and React; no new orchestration dependency.

- [x] Task 1: extend research task schema/registry/executor with research workflow mode, evidence matrix, grounded directions, review synthesis and quality supervision; bind goal changes, support replanning, export artifacts. Test restart, cancellation, source/goal changes and provenance.
- [x] Task 2: add bounded single-call model research synthesis with structured evidence IDs, hypothesis/author claim distinctions, cached immutable reports, durable call reservations and explicit consent; API and tests for budget, invalid references, failure, stale inputs.
- [x] Task 3: add explicit batch paper acquisition for existing metadata hits, verified allowed URLs, bounded downloads, cached originals and per-item outcomes/retries; reuse PDF processing, protect user data, API and tests.
- [x] Task 4: expose research workflow and model report controls in existing task view without expanding homepage clutter; meaningful tests and actual browser verification.
- [x] Task 5: evaluate full integration, update capability/limitation documentation, run offline suites and frontend checks, review and merge after CI.

Constraints: preserve optional research goals and project names; do not make model calls by default; do not auto-approve manuscripts; no fabricated citations or results; no automatic arbitrary code execution; exclude user launcher files from commits.
Review focus: goal edits during calls, crash after provider send, source identity ambiguity, hostile PDF URLs/redirects, read-only tenant access, incomplete coverage, unavailable provider credentials.
Ruling: prior detailed requirements and repeated autonomous implementation authorization cover this plan. Reuse current stack and implement in bounded increments; genuine scientific validity remains a separate uncompleted evaluation, not inferred from tests.
