# Evidence-aware writing coach

Goal: Bring advisor-style reasoning into the current manuscript editor, grounded in the actual draft rather than a simulated professor identity.

Design: Reuse the current client-side manuscript and source blocks, including unsaved edits. A collapsed coaching panel offers a research-type selector, prioritized mechanically detectable issues, paragraph navigation, and tailored questions about the argument, evaluation and interpretation. Export a JSON working-note snapshot for later discussion. No model calls, automatic rewrites, approval or claim of semantic assessment. Browser-session research-type choice is explicitly transient; manuscript revisions remain the source of persistence.

References inspected 2026-11-03: HKUSTDial/Supervisor-Skills technical-paper-template and pre-submission-reviewer; Scottthe3rd/academic-researcher-skill. Adopt high-level principles of pre-writing argument planning, paradigm-aware review and actionable feedback; implement original prompts/code. Do not bundle third-party skills or their text. License labels differ across upstream repository/files; no dependency or relicensing claim is made.

Plan:
- [x] Close pending report-export review: snapshot reads must not update task state; test actual reader/tenant access.
- [x] Test and implement pure writing-coach diagnostics: missing/mismatched references, placeholders, empty chapters, source staleness, conservative language flags explicitly marked heuristic; never treat hypotheses as observations.
- [x] Add compact disclosure panel using existing page typography and colors; actionable issue list before research-type questions; keyboard-accessible jump to sentence; export notes with run/revision and unsaved/stale flags.
- [x] Verify live edits, navigation, type selection, no false success badge, read-only browsing, JSON export and full regressions.
- [x] Document capability limits/public sources and complete independent review (no blockers).
- [ ] Push and merge after remaining full backend checks and CI pass.

Review focus: untrusted manuscript text remains text; unsaved drafts not labeled saved; current references not confused with semantic proof; theory/review not forced into experimental criteria; export cannot mutate task ownership.

