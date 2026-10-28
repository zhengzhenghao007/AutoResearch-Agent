# Structured research execution implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. User authorized implementation and direct merge after verification; prior autonomous-work preference applies.

**Goal:** Turn saved-paper research into explicit question plans, durable resumable steps, enforced budgets and reproducible real-corpus evaluation.
**Architecture:** Add an offline bounded executor alongside EvidenceWorkflow. Reuse validated source documents and IDs. Store task state transactionally in a per-store SQLite file; do not alter legacy ResearchRun/manuscript contracts. UI executes one durable step per request and can continue, pause between steps, cancel or reopen. No model/network calls in this execution mode.
**Tech stack:** Python/Pydantic/SQLite/FastAPI, React/Next.js; no new dependency.
**Spec:** This document plus docs/agent-readiness-review.md acceptance principles.

## Design and scope

The first executor answers explicit subquestions against saved papers, not the open web. User supplies the main question and optional newline-delimited subquestions (up to 6); default planning derives distinct question fragments or evidence facets with topic terms. Each question has evidence requirements and source-inspection steps, with dependencies and explicit success/partial outcomes. Bounded lexical evidence selection is labelled as retrieval, never semantic verification. Record gaps and stopping decisions. External paper text is data, never executable instructions.

One next-step request claims a step, reserves the attempt budget, computes outside the transaction, then commits only if task ownership/cancellation/source hash still match. Completed checkpoints are reused on restart. Interrupted pure read steps can be reclaimed after lease expiry; no paid or arbitrary side-effect tool is exposed. Source changes block stale results. Per-task max_steps, max_seconds, max_evidence are enforced, including exhausted budgets and explicit budget increases. Costs/tokens are exactly zero for this offline executor; future model tools require pre-reservation and idempotent paid-call handling before being enabled.

## API shared contract

All under `/api/research/runs/{run_id}/tasks`, existing principal/store isolation and writer guards apply.

- GET collection => `{items: ResearchTask[]}` (max 20 per record).
- POST collection body `{question:string,subquestions:string[],budget:{max_steps:number,max_seconds:number,max_evidence:number}}` => ResearchTask.
- GET `/{task_id}` => ResearchTask.
- POST `/{task_id}/next` => ResearchTask (one step; idempotent after terminal state).
- POST `/{task_id}/cancel` => ResearchTask.
- POST `/{task_id}/budget` body budget => ResearchTask; only explicit increases, no historical reset.

ResearchTask fields: `id,run_id,question,source_sha256,created_at,updated_at,status,stop_reason,budget,usage,subquestions,steps,events`.
Status: `ready|running|paused|completed|incomplete|cancelled|budget_exhausted|stale|failed`.
Budget: `max_steps,max_seconds,max_evidence`. Usage: `steps:number,seconds:number,evidence:number,input_tokens:0,output_tokens:0,cost_usd:0`.
Subquestion: `{id,question,requirements:string[]}`.
Step: `{id,question_id,title,tool,depends_on:string[],status:'pending'|'running'|'completed'|'failed',attempts:number,input_sha256:string,result:{evidence_ids:string[],gaps:string[],summary:string}|null}`.
Event: `{at,type,message}`. Frontend ignores extra server fields; backend publish any deviations before implementation.

## Ownership and tests

- [x] Backend worker: schemas/research_tasks.py, services/research_tasks.py, backend/app/api/research_tasks.py plus router integration, tests/test_research_tasks.py. Cover plan variance, dependencies, exact bindings, durable reload, crash/lease recovery, concurrent claim/cancel, source-change rejection, all budget exhaustion/increase boundaries, tenant/read-only/path isolation, malicious paper text inert.
- [x] Evaluation worker: evaluation/evaluate_research_tasks.py, tests/test_research_task_evaluation.py, examples/research-execution/. Real licensed conformal-prediction corpus already checked in; baseline vs executor retrieval/coverage, exact quote verification, failure cases, latency, zero cost. Human rubric packet remains honestly pending; no invented approvals. Publish actual output and reproducible command.
- [x] Root frontend: task API/types/panel, Library mount, responsive plan/status/usage/results, resume/cancel/budget controls, error and read-only tests. No automatic start on mount and no record data writes.
- [ ] Independent review, full tests, production browser checks, docs and CI; merge existing studio PR #26 and executor PR only after required checks pass.

## Scientific evaluation boundary

Real-data automated evaluation can establish source linkage, coverage proxies and observed failure behavior. It cannot establish expert semantic support or scientific truth. Separate pending human rubric judgments from deterministic metrics. No paid model experiment is needed to evaluate this offline mode.

## Verification ledger

2026-10-29: independent review corrected final validation time accounting; cancelled-source stale regression added. Full backend run: 390 passed, 1 skipped; final task/evaluation regression: 24 passed. Frontend: 124 passed; final panel tests 6 passed. ESLint, typecheck and production build passed. Real-browser flow validated budget stop/increase/resume, saved checkpoints after reload, evidence navigation, absent-topic incomplete state, and 390px layout without horizontal overflow or page errors. Real-corpus evaluator ran 15 trials; expert judgments remain pending. PR #26 was already merged when checked. Executor PR CI and merge remain delivery steps.
