# Real-corpus bounded research execution evaluation

Run from the repository root, with project dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m evaluation.evaluate_research_tasks --output examples/research-execution/results.json --repeats 3
.\.venv\Scripts\python.exe -m pytest tests/test_research_task_evaluation.py -q
```

[Raw measured output](results.json) contains 15 trials: five queries repeated three times, source/license hashes, exact selections, full executor traces, gaps, counters and measured wall times. No download, model call or fabricated paper is involved. Each trial uses a fresh temporary store; the executor service is recreated after each step to exercise durable continuation. UUIDs, timestamps and latency vary on replay; selections and deterministic metrics should agree.

The corpus is the three licensed papers in [the conformal-prediction case](../conformal-prediction/README.md). Their authors, titles, publisher links, original PDF hashes and CC-BY-4.0 attribution are preserved in the raw provenance. The saved corpus JSON and license/source manifest are hashed during evaluation. Original PDF bytes are not re-downloaded or verified by this offline command. Extracted quotations remain CC-BY-4.0; the software license does not replace that license.

Text provenance hashes use UTF-8 with LF newlines so Windows and Linux checkouts can be compared. Original PDF hashes remain byte hashes; this normalization does not apply to PDFs.

## Comparison and observed results

The fixed baseline selects existing method-category evidence, round robin across papers, capped at six quotations. This is a bounded version of the existing comparison workflow's category input, not a claim to benchmark its entire UI or generation pipeline. The executor receives explicit subquestions and the same six-quotation cap. Cases and lexical facet synonyms are visible in the evaluator and raw output; they are not expert relevance labels.

| Query | Baseline lexical facet coverage | Executor lexical facet coverage | Executor stop |
|---|---:|---:|---|
| Missing inputs / imputation | 0.50 | 1.00 | completed |
| Perturbations / coverage | 0.50 | 1.00 | completed |
| Epistemic / conditional coverage | 0.00 | 1.00 | completed |
| Lexical decoy | 0.00 | 0.33 | completed |
| Absent topic | 0.00 | 0.00 | incomplete |

All nonempty selections have exact saved-ID/source/page/quote binding and literal page support. The empty executor selection has a **null**, not perfect, binding rate. All five cases select the same evidence IDs across three repetitions. Model tokens and API cost are exactly zero. In the committed run median baseline selection time was approximately 0.00017 seconds; median executor time was 0.65 seconds. Executor timing includes planning, persistence and service reloads; baseline timing only includes selection. These are local observed timings, not general speed claims. Use raw per-trial times when comparing another run.

## Errors, omissions and limits

The decoy query `zygomorphic quasicrystals superconductivity` exposes a useful failure: superconductivity appears in reference text, so lexical retrieval returns real quotations and marks the plan completed even though the other two query facets are absent. This case was retained after an initial negative-query trial discovered that collision. The truly absent-topic query uses only the two absent terms. Neither is a fabricated source. This is a development evaluation, not a held-out benchmark.

The fixed baseline omits imputation, perturbation and both epistemic/conditional facets in its bounded selections. The executor improves these literal term proxies on this small corpus, but that does not prove relevance, adequate coverage or correct interpretation. It can select bibliography text, miss synonyms, prioritize the wrong paper, and omit assumptions or contradictory conclusions. The missing-input selections come from one source; this does not establish representative coverage. A `completed` executor state means the retrieval plan finished, not that a scientific answer is complete.

No human semantic labels were supplied. Semantic support, scientific accuracy, cross-paper comparability and expert completeness remain **pending**, with null metrics. The [pending per-quote review packet](results-human-review.json) binds each case/method/quote to the pinned corpus and provides null reviewer identity, semantic judgments and case-level omission assessments. Repeated identical quotations are deduplicated; the two retrieval methods remain separately assessable. The raw report includes a human rubric: inspect each quote against its question, preserve assumptions/limitations, assess comparison validity, and record missing evidence. An actual independent reviewer must supply judgments before quality rates can be calculated. Nothing here grants manuscript approval.

The regression tests tamper with quote/source/ID bindings, verify empty selections receive no quality credit, and run the actual executor twice per case. The broader executor suite covers budgets, cancellation and stale-source rejection; those are engineering checks, separate from this real-corpus retrieval evaluation.
