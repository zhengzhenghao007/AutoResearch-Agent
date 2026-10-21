# Evidence-linked manuscripts

P4 extends the read-only chapter preview with editable chapter plans, attributed text,
persistent revision history, optional version-specific model review and human-approved
Markdown export. This is a single-user writing tool, not an automatic publication or
scientific certification system.

## Writing workflow

1. Open a research record in the evidence workspace and load its manuscript. Create the
   first revision from the current evidence preview. No model request is made.
2. Edit chapter titles and order. Add or edit text units, recording one sentence per
   unit where practical. Choose the type explicitly: paper report, user observation,
   hypothesis, suggestion or missing-material placeholder. Select the evidence or
   computation references that support every factual unit. References apply to all
   text in that unit; they do not prove that a paraphrase is semantically supported.
3. Save with a revision reason. Saved versions preserve both the chapter text and the
   source/compute snapshot. Earlier versions remain available for inspection.
4. Optionally enable the explicit model-review consent and review the saved version.
   This sends its text and bound evidence/calculations to the configured provider.
   The report records support assessments and potential contradictions for that exact
   version; it never rewrites the manuscript. Oversized requests are rejected instead
   of silently dropping evidence. No model is called on load, save, approval or export.
5. A human checks the saved manuscript and its references, examines any model findings,
   supplies their name and review note, and explicitly confirms approval for export.
   Offline human review is supported. A model report cannot approve a manuscript.
6. Download the approved Markdown. It includes reference provenance, missing-material
   and speculation labels, and the approval/version identifiers. It does not claim the
   manuscript is ready for submission.

Saving new text or changing source material requires approval of the new current
version. A new model report also requires reapproval, and a stale page cannot approve
reports the human has not loaded. Old approvals and reviews are retained as history, never transferred to a
different version. Failed saves preserve the editor text. Reload before resolving an
outdated-version conflict; source additions may require recreating or editing the
reference selections.

## Evidence and limitations

- Paper facts cite saved paper claims with original evidence, page and source hash.
- User observations cite descriptive computations with dataset hash, column, sample
  references and algorithm. An all-missing column is not a computed result.
- Missing experimental material remains a placeholder. No missing value, measurement,
  citation or scientific conclusion is invented to complete a chapter.
- Text/reference consistency checks establish traceability. A misleading paraphrase
  can still have real citations; semantic review and human judgment remain necessary.
- Scientific validation stays `not_assessed`, including after export approval. The
  user's request to skip the project-level human scientific evaluation does not mark
  that evaluation passed, and permission to merge code is not manuscript approval.
- Markdown/HTML control characters in user text and references are escaped in export.
- Sidecar files preserve existing ResearchRun compatibility. The local filesystem is
  the trust boundary; a hash detects accidental inconsistency, not a malicious local
  actor able to replace all data and hashes. There is no authenticated reviewer identity.
- Bounded histories and local locking fit the existing single-user deployment. P5 adds
  transactional manuscript storage and authenticated user namespaces in SQLite deployment
  mode; see [deployment](p5-deployment.md). Reviewer names remain user-entered metadata.

The original `manuscript-draft` API/CLI remain read-only previews. See
[the shared contract and implementation plan](p4-completion-plan.md) for the persistent
manuscript endpoints, request fields and version checks.

## CLI

`manuscript-show RUN_ID` returns revision and review history. Initialize with
`manuscript-save RUN_ID --expected-input-sha256 HASH --reason "Initial draft"`.
For editing, supply `--expected-revision REVISION_ID --sections sections.json`, where
the file contains the structured section array. Omitting `--sections` resets material
from the current evidence preview as a new revision; earlier versions remain intact.

`manuscript-review RUN_ID REVISION_ID --allow-model` is the explicit provider call.
After inspecting the complete version and reports, the human may run
`manuscript-approve RUN_ID REVISION_ID --reviewer NAME --note NOTE --expected-review-count COUNT --confirm`.
COUNT is the number of saved reports for that revision, including zero for offline
review. `manuscript-export RUN_ID REVISION_ID` returns JSON with a filename and
Markdown string. It refuses stale or unapproved versions.

Limits: 20 saved revisions, 100 reports and 100 approval events; 30 chapters and 500
text units per document (up to 200 per chapter), 10,000 characters per unit; 20 MiB
sidecar file. Model input is capped at 50,000 characters and output at 100,000, with
one request and no automatic provider retry or repair loop.
