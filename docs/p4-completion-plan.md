# P4 manuscript completion design and plan

Goal: complete the roadmap's evidence-linked writing workflow, preserving offline defaults and explicit human export approval. The user authorized implementation and verified merging; this does not approve any manuscript.

Architecture: keep ResearchRun unchanged. Store an atomic, bounded manuscript sidecar under the ResearchStore root, with immutable revisions containing the original deterministic evidence draft snapshot. Each editable text unit (sentence) has an explicit type and references to snapshot block IDs. Every factual unit must cite the matching paper or computation kind; citations establish traceability, not semantic truth. Placeholders remain explicit, including missing experimental results. Sections can be reordered and renamed without removing required missing-data notices.

Rejected alternatives: adding manuscripts to ResearchRun would couple large histories to unrelated writes and create circular schema imports; free-form Markdown without structured citations would lose sentence-level traceability. No automatic narrative generation is necessary: the existing evidence draft supplies material, with explicit user editing.

## Shared API contract

Base `/api/research/runs/{run_id}/manuscript`.

- GET returns `{run_id,current_input_sha256,revisions,reviews,approvals}`. Empty arrays before creation.
- POST `/revisions`: `{expected_revision: string|null,expected_input_sha256:string,reason:string,sections:Section[]|null}`. Null sections initializes from the current preview. Otherwise saves the supplied full chapter plan and sentences. Returns whole state.
- Section: `{id:string,title:string,sentences:Sentence[]}`.
- Sentence: `{id:string,text:string,kind:'paper_report'|'user_observation'|'hypothesis'|'suggestion'|'placeholder',reference_ids:string[]}`. IDs unique in document; references are draft block IDs. At least one reference of matching kind for factual units. Nonfacts cannot become factual via export; placeholders and speculative units retain visible labels.
- Revision: `{id:string,number:number,created_at:string,reason:string,content_sha256:string,input_sha256:string,sections:Section[],source:ManuscriptDraft}`. Hash includes source snapshot and content. Limit 20 revisions.
- POST `/review`: `{revision_id:string,allow_model:true}`. Explicit call only; exact revision with all referenced evidence/computations, no silent omission, reject oversized input. Returns whole state. Review: `{id,revision_id,content_sha256,input_sha256,model,created_at,findings:[{sentence_id,status:'supported'|'unsupported'|'uncertain',rationale}],contradictions:[{sentence_ids:[string,string],rationale}],scientific_validation:'not_assessed'}`. All factual sentences covered exactly once; pairs valid and unique. Report persisted without text modification; recheck current revision/input after remote response.
- POST `/approval`: `{revision_id,expected_review_count,reviewer,note,confirm:true}`. Explicit human attestation scoped to current revision/hash/input and the review count the human saw. Returns whole state. Approval: `{revision_id,content_sha256,input_sha256,review_count,reviewer,note,created_at}`. A new report invalidates old approval; concurrent unseen reports reject approval. Human can assess offline; model review is advisory, not a prerequisite or substitute. UI requires unchecked confirmation and notes after viewing current findings.
- GET `/export?revision_id=...`: returns `{filename,markdown,revision_id,content_sha256}` only for the current nonstale approved revision. Include all evidence/compute references, placeholders, speculative labels, review and approval provenance; scientific validation remains not_assessed. Escape untrusted Markdown/HTML.

Separate sidecar means run changes do not destroy history. Old revisions remain viewable but cannot be approved/exported as current. Source change requires an explicit new revision; invalid references must be corrected or reset. Check expected revision and input hash on every write. Reject corrupt sidecars rather than silently reset them. Single-process locking prevents conflicting manuscript mutations; multi-process transactions remain P5.

## Implementation tasks

- [x] Backend schemas/service/store, API/CLI and regression tests: persistence, exact hashes, citation validation, invalid/missing observations, stale writes, stale model responses, forged IDs, provider failure, corrupt storage, approval/export gating and escaping. Write failing tests before implementation.
- [x] Frontend types/client/editor: create from preview, edit/reorder chapters, add/remove typed sentences and select citations, save reason/history, explicit model consent, display findings, human approval, download. Failed saves preserve input, pending actions serialize, source/revision changes invalidate stale responses. Tests first.
- [x] Integrate, run full Python/frontend suites, lint/type/build, real browser persistence/edit/export and small viewport checks. Never call a real paid provider or approve a real manuscript during tests.
- [ ] Independent code review, fix findings, update roadmap/readme with precise limits, push PR, verify CI, merge main.

Review focus: malformed storage must fail closed; new data must invalidate old approval; stale remote responses cannot bind to newer text; zero/missing statistics must remain distinguishable; citations and user text cannot inject exported HTML or fake structural headings.

## Verification record

2026-10-19: 302 Python tests and 84 frontend tests passed; frontend lint and typecheck
passed. Real Chromium checks used synthetic data only: initialize, edit, serialize
source writes, save/reopen/history, explicit approval, download bound Markdown, invalidate
approval after editing, 390px viewport and no browser errors. Seven evidence regression
fixtures passed; all seven human labels remain pending and metrics null.

Independent review identified stale human approval across tabs when a new model report
arrives. The fix requires `expected_review_count` and compares it under the persistence
lock. The failing reproduction now passes; independent re-review found no blockers.
Windows full tests run with local sockets available for asyncio; Linux CI uses
`--disable-socket --allow-unix-socket`. No actual model/provider evaluation was performed.
