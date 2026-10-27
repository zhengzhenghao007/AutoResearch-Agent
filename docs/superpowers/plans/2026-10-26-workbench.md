# Research workbench implementation plan

**Goal:** Four focused stages, one reproducible licensed research case, product-first README.
**Architecture:** Keep API and storage contracts; add frontend stage orchestration, focused source reading and a comparison matrix. Generate case outputs through existing Python services.
**Spec:** ../specs/2026-10-26-workbench-design.md
**Tech:** Existing Next.js 16, React 19, Python/Pydantic; no new production dependencies.

- [x] Session/entry: tests for no local credentials and explicit remote authentication; separate legacy route.
- [x] Workspace: persistent four-stage panels, preserve unsaved drafts, collapse advanced reviews, source reading and linked comparison; test navigation and evidence targets.
- [x] Case: verify licenses, pin PDFs, run services, preserve outputs and audit omissions; add replay/install tooling and integrity checks.
- [x] Presentation: screenshot actual UI and rewrite README; keep engineering docs accessible.
- [x] Verify: frontend tests/lint/build, backend tests, replay corpus, desktop/mobile browser, fresh-context final review, commit/push and PR.

## Review focus
Unsaved writing on stage switch; stale run responses; deployment reader restrictions; evidence navigation across panels; case reproducibility without credentials or forged human approval.

## Execution notes
2026-10-26: clean main, branch codex/research-workbench. C2C doctor twice reports workspace_mismatch, cannot confirm the existing bridge; no restart or connector changes performed, to avoid interrupting other projects. Continue authorized local work; external review unavailable until connection is healthy.

2026-10-27: Local checks complete: 341 backend tests passed, one skip; 95 frontend tests passed; lint/typecheck/production build passed. Seven evaluation regressions passed; seven human reviews remain pending and metrics are null. Three licensed PDFs independently replayed with identical hashes, pages, all 262 quotes, categories and bindings. Production-browser checks at 1440px and 390px passed, including reading/page navigation, real manuscript initialization, stage switching and no horizontal document overflow. Screenshots contain only the case workspace, not unrelated research history.

Ruling: the original PCP PDF exceeds the existing 20 MiB limit. Retain its exclusion in the manifest/audit and replace it with Ghosh's perturbation paper; final scope is missing inputs, perturbations and sparse regions.

Ruling: the real case exposed a 215-block chapter exceeding the per-section bound. Split into bounded parts without dropping references; retain the 500-sentence document limit. Added a red/green persistence regression.

Independent review found and resolved selection of papers without quotes, access to pages without extracts, and recovery after a failed replacement token. Browser-scale verification additionally led to deferred chapter/reference rendering to avoid quadratic hidden controls. Follow-up review found no important defects. No human approval or model call was made for the case.

Delivery: dedicated branch and ready pull request; no automatic merge into main.
