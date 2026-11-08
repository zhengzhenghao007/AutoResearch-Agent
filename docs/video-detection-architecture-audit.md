# AI-generated video detection case · execution audit

The [case receipt](../examples/video-detection/workflow/run.json) records one local run on original PDF bytes. Its source hashes, one-based physical PDF pages and quotation digests support replay without distributing the papers. The research question asks how detectors behave on unseen generators and under compression. A literature workflow can locate statements about these conditions. Measuring robustness requires detector predictions on held-out videos and a specified transformation protocol.

## Execution boundaries

| Boundary | Implementation and role | Exercised here |
| --- | --- | --- |
| Paper ingestion | `workflow/evidence_workflow.py` sends uploaded bytes to `services/paper_processing.py`. Its worker extracts page text using pypdf. The default limits are 20 MiB and 50 pages per paper. Image-only pages may take the optional OCR path. | Real local uploads, hash checks, page counts and OCR provenance in the receipt. |
| Extractive reading | `services/evidence_extraction.py` splits page text into sentences and assigns the first matching category from an ordered set of regular expressions. `services/evidence_review.py` checks source IDs, page membership, literal support and claim bindings. | Rule mode on every supplied PDF. References and headers can also match the rules. |
| Task orchestration | `services/research_tasks.py` stores a source-bound task, leases and checkpoints in SQLite. `services/skill_registry.py` resolves an explicit skill ID and version and validates its result. | Research retrieval, source inspection, evidence matrix, brainstorming, literature review and supervision. All six are registered Python handlers. The alternate evidence-mode lexical retrieval skill was outside this run. |
| Agent pipeline | `workflow/research_workflow.py` coordinates planner, researcher, reader and reviewer. In its model-backed mode `pipelines/reader_pipeline.py` calls reader, reviewer and reflection with bounded retries. Auto mode can fall back to the rule reader. | Inspected in source. The case uses the separate evidence workflow, so these agents do not appear in its execution trace. |
| Optional model calls | The evidence extractor accepts an explicit LLM mode and validates schema-constrained selections against page text. Separately, `services/research_reasoning.py` validates quotations, selects up to 40 within a 60,000-character JSON budget and reserves optional model generations against a snapshot. | Offline task usage records zero tokens and cost. Source-derived artifacts come from the registered handlers. |
| UI and API | `frontend/components/ResearchTasks.tsx` and `frontend/lib/research-api.ts` connect the task controls to FastAPI. `backend/app/api/research_tasks.py` delegates create, next, status, budget and report operations to the same executor used here. | The case driver calls the service entry points directly. Browser interactions and deployment authentication are outside this trace. |

## Academic Humanizer

The repository ships an upstream skill and lexicon under `vendor/academic_humanizer/`. Its local runtime in `services/academic_humanizer.py` edits eligible paragraph openings, preserves protected regions and checks consistency before returning a revision. Its publication policy lives in `services/humanizer_policy.py`. The case creates a standard-profile policy file inside its private run store. The receipt instruments the actual Python function by code object, which captures direct imports across modules. It counts returned calls and text changes separately. The standalone edit probe records its own input and output separately from workflow counts.

In the model-backed branch, `agents/base_agent.py` applies the editor to user-facing chat and invokes schema validation with generated-prose context for structured responses. `backend/app/academic_output.py` handles eligible plain text, standalone JSON strings and a dedicated prose SSE encoder. Typed records can contain source quotations or tool arguments, so their generated fields require explicit ownership at construction time. See the [publication policy and integration details](academic-humanizer.md).

## Interpreting and reproducing the receipt

From the repository root, use the project's Python environment and put the source files in a private directory. Name arXiv PDFs by identifier to preserve their public links. Run the command below after installing the repository's dependencies.

```powershell
python examples/video-detection/workflow/run_case.py --pdf-dir .verification/video-pdfs --private-store .verification/video-workflow --output .verification/video-replay.json
python -m pytest -q tests/test_academic_humanizer.py
```

Each source records its byte SHA-256, parsed and nonblank page counts, extraction categories and evidence anchors. To inspect an anchor, extract the cited PDF page using the project's worker, collapse whitespace with `" ".join(text.split())`, slice the string at the recorded offset and length, then hash the UTF-8 bytes. Multiple appearances resolve to the first matching span. Processing timestamps and generated run IDs differ on replay. Compare PDF identities, evidence anchors, category counts, gaps and step outputs. Full quotations, original PDFs and native task artifacts remain in the private store.

The default research budget selects 30 items across paper/category buckets. The executor marks a task incomplete whenever a finished step reports a gap. Each receipt lists these gaps. A missing category can reflect phrasing, extraction or selection. Literal review can approve a bibliography entry, a table fragment or a statement about someone else's method. A reviewer must read the source context before adopting a scientific finding. Extracted claims count candidate spans, which may include many mentions of the same result.

## Observed results and corrections to interpretation

Five PDFs yielded 47 of 47 pages and 327 literal candidate claims. The 30 selected anchors produced 30 matrix entries, six proposals, seven review artifacts and nine quality artifacts across the review and supervision steps. All six steps finished. The terminal status was `incomplete` because retrieval omitted 297 candidate spans and the selected matrix lacked some categories. D3 used the conference edition named `d3-iccv2025.pdf`; its SHA-256 matches the experiment's [Table 4 source](../examples/video-detection/experiment/results.json). The other four inputs were arXiv PDFs. The receipt includes exact provenance for each.

A manual spot check found the same VideoCrafter2 bibliography title tagged as a limitation in arXiv 2404.15955 (PDF p. 9, evidence suffix 84) and GenVidBench (PDF p. 8, suffix 77). Both passed literal inspection and entered the task selection. Their wording describes the cited paper's title. These two entries cannot support limitations of either host paper. Likewise, AIGVDet p. 2, suffix 11, is a section roadmap classified as an experiment. The case uses directly inspected source tables for its quantitative conclusions. The runtime labels and proposals should retain their provisional status. A future extractor could identify bibliography regions before category assignment and evaluate that filter against manually labeled pages.

The actual case invoked the humanizer 107 times, including repeated synthesis as each PDF was imported. Its input templates already passed the local editorial rules and all returned unchanged. The isolated edit probe removed a qualifying opener and retained the citation marker and modal verb. The eight tests in `tests/test_academic_humanizer.py` passed with one Starlette test-client deprecation warning. The Windows sandbox initially blocked the internal asyncio loopback socket; the same tests completed with loopback available. The tests cover output conservation, idempotence, streams, fallback behavior, profile persistence, agent audience and HTTP publication.
