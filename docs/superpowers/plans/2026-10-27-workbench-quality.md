# Workbench quality review

> Execute inline with superpowers:executing-plans, then independent review.

**Goal:** Make evidence limitations and next actions visible, preserve navigation, and prevent silent loss of writing.
**Architecture:** Extend existing React workbench; derive coverage from validated ResearchRun, keep manuscript revisions on server. No new runtime dependencies or model calls.
**Design:** Keep four stages and existing blue/white typography. Add a compact, left-aligned record overview with actionable warnings, not a synthetic quality score. Browser URL stores only stage and run ID. Unsaved text stays in memory; explicit discard restores saved revision. No silent persistence of sensitive text in browser storage.

## Public reference audit (2026-10-27)

| Reference | Observed design | Applicable improvement |
| --- | --- | --- |
| [Elicit systematic review](https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit) | Staged workflow, supporting quotations accessible from extraction cells | Keep quotation navigation, expose coverage warnings and a useful next step |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | Source-based research and report outputs | Preserve attribution and transparent limitations rather than imply automatic scientific validity |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | Configurable research and documented evaluation | Treat engineering and research-quality evaluation separately; archived repository is reference, not a dependency |
| [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | State persistence for interruption recovery | Preserve workflow location; guard draft loss before expanding execution architecture |

These are design observations, not head-to-head accuracy tests. No market superiority or completeness claim follows from them. Existing queued jobs and backend revisions already provide execution persistence; this change does not claim browser drafts are crash-recoverable.

## Alternatives

Cosmetic-only polish would leave data-loss risks. Replacing the system with a multi-agent framework would expand costs and validation scope without fixing these interaction defects. Selected approach: targeted reliability and evidence visibility on the current architecture, under prior autonomous execution authorization.

## Tasks

- [x] Coverage overview: show per-paper truncation, missing categories, no extracts, and source-check status separately from scientific review; offer navigation to inspect sources. Tests cover empty and partial records.
- [x] Stage URL: reload and browser history restore the stage, safely default invalid values; keep same-record draft mounted. Test deep links and back navigation.
- [x] Writing safety: warn on page close while dirty, explicit confirmed discard, guard record-changing browser navigation and session replacement. Test cancelled and accepted discards and save failures.
- [x] Run all frontend checks and browser desktop/mobile QA, independent branch review.
- [ ] Upload a PR and verify remote CI.

## Review focus

- A passing literal check must not hide truncated or missing evidence.
- No-paper records must not report evidence readiness.
- Same-record history movement must not refetch or erase the editor.
- Dirty drafts must not disappear on browser Back; a save error must preserve them.
- No automatic model calls, approvals, browser text storage, or change to original research records.

## Boundaries

Missing extraction categories mean extraction gaps, not absent scientific findings. Browser close protection is best effort and cannot survive a process crash. Human scientific evaluation remains unperformed. Full agent benchmarks, multimodal parsing, and collaboratively edited drafts require separate validated work.

## Execution ledger

- New tests failed on missing overview, missing deep-link restoration, absent close protection and unguarded session replacement; then passed after implementation.
- Full regression initially caught overly broad navigation blocking of unrelated annotation requests. Restored existing late-response isolation; manuscript navigation remains guarded.
- Independent review found blocked Back overwrote its destination entry, and slow-loading stage navigation left the URL stale. History indices now restore the cursor without overwriting records; stage changes use the requested record ID while loading.
- Real Chromium: four stages on desktop and 390px mobile, no horizontal page overflow or console exceptions. Back/Forward preserves prior records after an intercepted dirty transition; discard retains the server revision; reload restores Writing. No model calls or saved scientific approvals.
- Browser edits were temporary and discarded. Updated Library screenshot shows the actual three-paper case and its two extraction gaps.
- Final verification: 103 frontend tests passed; lint and TypeScript checks passed; production build passed. Independent follow-up review found no remaining blockers. Backend behavior is unchanged in this increment.
