# Research spaces and optional quick reading Implementation Plan

**Goal:** Implement the user-approved research space and optional paper quick-read design from this conversation.
**Architecture:** Keep legacy topic for compatibility, add independent project metadata; persist grounded quick reads separately from literal claims. Existing research task budgets remain unchanged; quick reads are explicit bounded single model calls, cached by source and goal.
**Tech Stack:** FastAPI/Pydantic, existing JSON/SQLite stores, Next.js/React, existing LLMClient.
**Spec:** User-approved specification captured below.

## Approved specification
Editable project name defaults to Research, independent optional research goal, uploads never rename projects. Existing filename-named projects display Research until renamed. Users can collect and read papers without a goal, compare a selection, or start research tasks with an explicit question. Navigation represents workspaces rather than ordered steps. Optional quick reading summarizes one sentence, 3–5 main points, problem, author-claimed innovations, methods/experiments, findings/applications and limitations. Every substantive point links to exact source text and page; missing information is explicit. No automatic model calls; save results for reuse. Show OCR and partial coverage caveats; reject fabricated quotations. Goal-related analysis is separate from the project title.

## Tasks
- [x] Project metadata backend: compatibility, default names, optimistic edits, in-project search, API and regression tests.
- [x] Quick-read backend: strict bounded schema, source validation, consent, cached persistence, provider errors and regression tests.
- [x] Frontend integration: editable project header, optional goal, independent navigation, selected paper comparison, optional concise quick-read with page jumps; focused component tests.
- [ ] Final checks: backend/frontend suites, build and browser flow with existing private record; review, fix, publish and merge.

## Constraints and review focus
Never commit private PDFs or user data. Preserve old evidence/manuscript hashes and user edits. Project rename must not become a research instruction. Reject stale concurrent metadata edits. Summary references must match current source text, not just invented page numbers. Cached reads consume no model calls; failed generation changes no paper record. Existing authenticated read-only permissions apply. A model result is advisory, not verified scientific novelty.

## Execution ledger
User explicitly requested implementation of the complete approved design; proceed without a second design approval. Use subagent-driven implementation for bounded backend modules and parent integration; independent final review. Work on codex/research-spaces-quick-read, preserve the two pre-existing launcher files.

Implementation validation: 441 backend tests passed and one skipped before final concurrency/rate-limit refinements; 44 focused tests passed after those refinements. 141 frontend tests, lint, typecheck and production build passed. Existing four-paper browser flow and mobile layout passed; metadata create/goal-save/upload passed; cached synthetic fixture page jumps and reload passed. Live self-authored synthetic-paper provider call returned 429, now surfaced honestly. Independent final reviewer could not run because its model quota was exhausted; parent audited metadata overwrite races and cache binding and added regressions. GitHub CI and merge pending.
