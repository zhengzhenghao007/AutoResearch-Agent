# P5 completion: bounded deployment

Goal: finish the existing final milestone, not introduce additional research features.
The user authorizes implementation, validation and merging without another code review
approval. Scientific evaluation remains unassessed; model/network actions remain explicit.

## Design

SQLite is the deployment storage boundary, with transactions and optimistic revision
checks on runs. Manuscripts and their approvals participate in the same database
transactions as source reads. Existing JSON files remain readable in local mode;
an explicit validated migration imports them without overwriting database records.
SQLite is appropriate for one deployment host with one supported API worker (CAS is also tested across independent processes); distributed
multi-host queues/databases are outside this version.

Deployment uses explicit server-managed bearer tokens, writer/reader roles and isolated
user storage roots. Tokens are configured outside version control, never logged or
embedded in frontend builds. Local offline mode remains available on loopback only.
Public deployment requires TLS termination and configured authentication. Stateless
legacy paper endpoints must not bypass deployment restrictions.

Background jobs cover explicit literature search and selected-paper analysis. Status,
cancel and retry endpoints plus UI allow leaving the current operation. Jobs persist,
have bounded workers/queue/retry budgets, and never silently replay paid calls. Work
uses staged snapshots; failed/cancelled/stale tasks must not replace a live run.
Interrupted tasks are reported as such rather than claimed successful. Manual retry
has a new attempt identity. Cancellation may wait for an in-flight bounded operation
but must prevent committing its result.

Ingress retains 22 MiB body limits and adds a body-read deadline and concurrent request
admission. PDF parsing receives OS CPU/address-space limits before parsing on supported
deployment hosts, plus existing wall-clock/input/text limits. Deployment must fail
closed on unsupported parser isolation; local mode clearly reports its weaker boundary.

## Parallel ownership and interfaces

1. Storage: `services/sqlite_store.py`, schema private persistence token if needed,
   manuscript storage integration, migration CLI/tests. Public class
   `SQLiteResearchStore(root)` exposes ResearchStore-compatible create/load/save/history,
   `.transaction()` context for same-thread atomic work, `ConflictError(ValueError)`.
   `save` rejects snapshots loaded before another successful write, including across
   independent store instances/processes. Send private token details to other workers.
2. Deployment/security: `backend/app/security.py`, main middleware wiring,
   request admission/deadline, PDF worker isolation, configuration/tests.
   `AUTORESEARCH_DEPLOYMENT=1`, `AUTORESEARCH_DATA_ROOT` and
   `AUTORESEARCH_USERS_FILE` are server-only configuration.
   Users file JSON: `{\"alice\":{\"token\":\"at-least-32-random-characters\",\"role\":\"writer\"}}`.
   Middleware sets `scope['state']['principal']` as `{id,role}`.
   `workflow_for_request(request)` in security returns a workflow with isolated SQLite
   storage for configured users and existing default local workflow otherwise.
   Parent wires research dependency to this function. `/api/research/session` returns
   `{mode:'local'|'deployment',user_id,role}`. Never return tokens.
3. Jobs: separate `services/research_jobs.py`, `backend/app/api/jobs.py`, schema/tests
   and standalone `frontend/components/ResearchJobs.tsx`/types/api files.
   Router base `/api/research/jobs`: GET list, POST submit
   `{kind:'search'|'analyze',topic?,max_results?,run_id?,selected_ids?}`;
   GET `/{id}`, POST `/{id}/cancel`, POST `/{id}/retry`.
   Use research.get_workflow dependency, so authorization/storage isolation applies.
   Parent wires router and frontend component. State includes id/status/kind/progress/
   created_at/updated_at/attempt/run_id/error with sanitized errors.
4. Parent: integration, frontend token/session controls, deployment docs, end-to-end
   tests and independent review. No new services or cloud resources provisioned.

## Acceptance

- [x] Two concurrent run updates cannot silently overwrite; manuscript source/version/
  review approval checks are transactional across processes; legacy migration tested.
- [x] Two configured users cannot access each other's runs, manuscripts or jobs;
  reader cannot mutate, unauthenticated access denied before reading request bodies.
- [x] Jobs survive browser navigation; cancellation, stale commits, retry limits,
  restart/interruption and saturation are tested.
- [x] Body limit/deadline/concurrency and parser CPU/memory boundaries verified;
  deployment startup validates support/configuration and explains limitations.
- [x] UI supports credentials/session and background job lifecycle without leaking
  tokens or applying stale results. Existing synchronous/offline workflows still work.
- [x] Offline regression, frontend checks, real browser tests and independent review.
  GitHub CI must pass on the submitted commit before merge; PR checks record that gate.
  Report exact operational boundary rather than universal security.
