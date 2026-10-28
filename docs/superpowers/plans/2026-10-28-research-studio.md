# Research studio implementation plan

> Execute with superpowers:subagent-driven-development; shared contract below, isolated file ownership, independent review before delivery.

## Intent and design

User wants a complete research workspace: durable papers/references, experiment data and records, automatic tables/charts, and web writing with reference material open beside the document. They explicitly chose web editing. Existing local-first Next.js/FastAPI architecture stays; no autonomous model calls or fabricated data. Continue from PR #25 without merging it implicitly.

Use an expanded workspace: Library, Reading & evidence, Compare, Data & figures, Writing. Library stores parsed papers and citation metadata; Data & figures exposes existing imports, a visible data table, chart creation, saved figures/tables and append-only experiment notes. Writing has an independently scrollable reference drawer alongside the editor, search/filter, original quotations/pages, and insertion of typed evidence or saved visual assets into a selected chapter. Narrow screens stack the drawer without losing the draft.

## Shared contracts

ResearchRun gains `workspace_items?: WorkspaceItem[]` (default empty, max100). Item requests: `{kind:'note'|'table'|'figure',title:string,text:string,dataset_id:string|null,columns:string[],x_column:string|null,chart_type:'bar'|'line'|'scatter'}`. Defaults: text empty, dataset null, columns [], x null, chart_type bar. Saved item adds `id` UUID hex, `created_at` ISO date, `dataset_sha256:string|null` bound by server. Notes may link to a dataset. Tables/figures require an existing dataset and selected numeric columns; figures accept one Y column; scatter/line require X. Saved items immutable; corrections create new records. No arbitrary HTML/SVG from the client.

API paths under `/api/research/runs/{run_id}`:
- `POST /workspace/items`: save validated item; returns ResearchRun. Bounded to100 items; JSON process lock / SQLite transaction.
- `POST /workspace/preview`: read-only render request; returns `{item:WorkspaceItemRequest,dataset_sha256:string|null,headers:string[],rows:(string|number|null)[][],svg:string|null,markdown:string,warnings:string[]}`. Tables include sample IDs and units. Rendering uses Matplotlib with Agg, fixed bounded figure sizes and escaped text; missing values excluded with counts, no imputation, no line interpolation across missing observations. Bar baseline zero; numeric X for scatter/line, deterministic sorted X. No misleading uncertainty or significance.
- `GET /workspace/items/{item_id}`: same render response from saved spec.

`DraftBlock` gains kind `research_asset` and optional `asset` containing the saved rendering plus `item_id` and title. Existing blocks keep asset absent/None; historical manuscript hashes must remain valid by excluding absent new field from hash serialization. Only figure/table assets enter the draft; notes never become results. Input hash includes workspace figure/table items only when present, preserving old records exactly. Sentence kind `research_asset` must bind exactly one matching asset block and retain its caption. Exports contain rendered tables and SVG images; add approved ZIP export (`GET /manuscript/bundle?revision_id=...`) with manuscript.md, SVG files, reference JSON and data provenance. Same exact-revision human approval gate; markdown export remains compatible.

Frontend `types/workspace.ts` owns shared types. API helpers `saveWorkspaceItem`, `previewWorkspaceItem`, `workspaceItem`, `manuscriptBundle`. Library component `ResearchMaterials` props `{run,busy,readOnly,onSave:(request)=>Promise<boolean>}`. It previews before save, shows table/chart gallery, supports downloading SVG/CSV (escape CSV formula strings), raw data table, note entry/list. Root mounts existing Experiments import under Data & figures instead of hidden comparison details. All writes use existing serialized annotation pathway.

## Tasks and ownership

- [x] Backend: contracts, validation, storage/API, deterministic renders, draft asset bindings, backward-compatible manuscript hashes and approved bundle; tests including persistence, malformed columns, missing values, stale approval and legacy case.
- [x] Materials frontend: types/API helpers, ResearchMaterials with data preview, charts/table/note creation and saved library; component tests.
- [x] Writing frontend/root: new stage, source drawer, search and insert quotation/reference/statistics/assets, visual asset rendering, approved ZIP download, responsive layout; regression tests.
- [x] Integration: clearly labelled synthetic dataset walkthrough, production browser verification including reload, tests/lint/type/build, independent review and documentation. Real scientific evaluation remains unassessed. GitHub delivery tracked in the PR.

## Constraints and acceptance

Do not mutate original research datasets, auto-approve a manuscript, or replace missing values with zero. Retain existing storage/auth protections and legacy manuscripts. New note/chart save must not erase dirty writing. UI distinguish raw data, researcher notes, computed charts and cited paper reports. Data remains per research record; this increment is not a global cross-project search engine. Original uploaded PDF binaries are not currently retained (parsed source pages are); document this honestly and do not label extracted text an original PDF. No XLSX import in this increment; CSV/JSON input and SVG/CSV output are explicit.

End-to-end acceptance: import data -> inspect rows -> preview chart/table -> save -> reload -> reopen saved material -> open Writing and a reference side-by-side -> insert a quote and saved asset -> save revision -> human-approved export includes asset and provenance. Scientific evaluation remains separate.
