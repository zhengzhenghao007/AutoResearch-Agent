# P0 + P1 implementation record

Scope approved by the user: `docs/roadmap.md`, “下一轮建议：P0 + P1 的最小闭环”.
ChatGPT plan: task `c2c_a71f`, planning and review through codex-with-chatgpt.

## Delivery sequence

1. Add failing history/API tests, then implement validated, paginated summaries without changing existing run JSON.
2. Add redistributable synthetic fixtures, annotation provenance validation and evaluation. Pending labels never count as human-reviewed data.
3. Add an evidence workspace alongside the existing frontend: search, explicit selection, upload, history, saved-page citations and URL restoration.
4. Add offline CI, dependency policy, regression and real browser verification.
5. Independently review, address findings, commit and push the development branch.

## Decisions

- Work on `codex/p0-p1-evidence-workspace` in the current checkout so existing untracked frontend work and the ChatGPT project connection stay available. No reset/stash of user work.
- Keep the legacy frontend and `requirements-dev.txt` changes. New CI uses a separate, directly pinned `requirements-ci.txt` covering actual offline/API imports; optional developer tools remain separate. Transitive dependencies are resolved by pip, so this is a direct-dependency baseline, not a full hash lock. Upgrade pins in a dedicated PR with the same regression checks.
- History ordering uses snapshot modification time and run ID as a tie-breaker. No incompatible timestamps added to persisted v1 documents. A corrupt snapshot fails history explicitly. JSON remains single-user; pagination is not transactional during concurrent writes.
- Synthetic material and AI-authored labels are regression fixtures, not a completed human evaluation set. Human annotation acceptance remains pending until a real reviewer records provenance.
- Push the new branch without force-push or merging. CI branch-protection settings require repository administration and are not implied by adding a workflow.

## Verification baseline

44 existing offline Python tests passed before implementation. Sandbox temporary-directory restrictions required running pytest with normal Windows permissions; no production-code fix was needed.

## Review and dependency decision

An independent code review found that hash-only navigation reloaded the current run and erased unsaved selection. The fix compares the URL run ID before restoration. Citation DOM IDs and encoded fragments now resolve consistently for real colon-containing evidence IDs; regression tests cover both issues.

Next.js and eslint-config-next are pinned exactly to 16.3.5, retaining Next 16 and React 19. This is a scoped security update from 16.2.10, which falls in the affected range of the official Windows remote-code-execution advisory: https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36 . The production build and existing UI remain compatible. npm audit on the installed lockfile reports zero known vulnerabilities.

## Browser verification (2026-09-21/22)

Production Next build against the isolated synthetic fixture server:

- Search produced two unchecked candidates and no evidence; analysis stayed disabled until explicit selection.
- Selecting both papers produced a method comparison, four quotations, separately labelled suggestions and page-level sources.
- Clicking a real colon-containing evidence link reached its highlighted quotation; clicking the extracted-page link reached the page text. An unsaved selection remained intact during the hash navigation.
- Hard refresh restored the persisted record and selected IDs.
- Uploading normal.pdf kept the same run ID and increased the paper count from two to three. Duplicate upload reported “This PDF is already in the research run”; history retained three papers.
- Searching the fixture topic empty showed explicit no-candidate and no-evidence states; history reopened the earlier three-paper record.
- Malformed/empty PDF preservation is covered by API tests. The additional browser empty-PDF chooser attempt timed out in the browser harness before upload, so it is not counted as a browser pass.

These are application-flow checks with synthetic materials, not human scientific evaluation or live arXiv availability tests.

## Final local checks

- Clean CI Python 3.12 environment: 66 tests passed with external hosts blocked (Windows loopback exception for asyncio); one dependency deprecation warning.
- npm ci: clean lockfile installation, zero reported vulnerabilities.
- Frontend: 17 tests passed; lint, generated-type check and production build passed.
- Evaluation: 6 regression fixtures passed, 0 human-reviewed records, metrics null.
- Git staged PDF bytes match all six manifest hashes; .gitattributes marks PDFs binary to avoid CRLF conversion.
- Remote Linux Python 3.11/3.12 and Node 22 workflow results are separate from these local checks.

## External review limitation

ChatGPT independently reviewed the implementation and Python output during iteration 1, finding no core P0/P1 functional defect. It requested the frontend logs and questioned the Next update; it subsequently accepted the security-update rationale. Final connector reads failed despite repair and re-pairing, so ChatGPT did not issue a final DONE. All frontend outputs were recorded, the separate local code review finding was fixed and tested, and the verified development branch is published without merging. This limitation must not be represented as completed external sign-off.

## Offline human-review tooling (2026-09-24)

This follow-up closes a tooling gap in P0 without declaring the human-evaluation
gate complete. Export produces a self-contained HTML page, copied PDFs, and
blank review rows. Import binds the exact manifest/PDF hashes and page scope,
validates reviewer/date and literal quote locations, and writes a separate
corpus with an audit file. Both operations reject existing output directories;
validation precedes staged publication. The original corpus and its regression
expectations remain intact. See tests/fixtures/evidence/README.md for commands.

Implementation follows failing contract tests, module implementation, full
Python regression checks, and independent review. Tests use simulated reviewer
metadata only in temporary directories. The shipped seven records remain
pending_human_review; obtaining real reviewers and representative licensed
papers remains outstanding. ChatGPT connection diagnostics currently cannot
confirm this workspace, so external sign-off remains pending.

Verification completed 2026-09-25: 90 Python tests passed (one existing dependency
deprecation warning), the CLI exported a usable seven-PDF packet, and all seven
original regressions passed with reviewed_count 0 and metrics null. Independent
code review found no blockers in identity binding, escaping, provenance,
quotation validation, preservation, or staged publication. Frontend code was
unchanged by this follow-up; remote CI rechecks the complete branch.
