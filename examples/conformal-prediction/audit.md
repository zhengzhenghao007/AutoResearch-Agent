# Case audit: omissions, errors and limits

Observed during the 2026-10-26 case preparation. This is an **AI-assisted qualitative spot check**, not independent human validation and not a measured accuracy/recall score. The existing human-evaluation backlog remains unchanged.

| Observation | Reproducible location | Consequence / treatment |
|---|---|---|
| Original PCP PDF is 34,802,189 bytes | Excluded `wang23n` in `sources.json`; importer rejects above 20 MiB | Recorded rejection; replaced with Ghosh et al. Do not silently shrink the PDF or weaken the importer limit. This changes the topic from multimodal regression to imperfect-data uncertainty more broadly. |
| Writing initialization failed at 215 method-section blocks | Three-paper outline; `Reported methods` combines method, data and experiment extracts | Fixed automatic initialization to split chapters into parts of at most 200 sentences without dropping references. Total 500-sentence document limit remains. Regression test covers 215 evidence-bound claims. |
| Title, authors and abstract merged into a “method” extract | Zaffran, PDF p. 1, claim suffix `:1` | A literal match can still be a poor excerpt. Full saved text is retained; original PDF must be consulted. |
| Empirical sentence categorized as “method” | Zaffran, PDF p. 1, claim suffix `:5`; Ghosh, PDF p. 1, suffix `:5` | Early method keywords win over result/experiment categories. The comparison does not correct these automatically or treat category presence as quality. Use explicit category revisions after review. |
| Bibliography becomes method evidence | Ghosh, PDF p. 10, final three method claims | Rule matching does not distinguish references from the authors' contribution. “Algorithmic learning in a random world” is a cited title, not this paper's method. Retained in raw output; do not use the automatic draft as a finished review. |
| Expected uncertainty widening classified as future work | EPICSCORE, PDF p. 2, claim suffix `:6` | The phrase “we expect” triggers a future-work rule although the passage explains a motivation. The generated suggestion inherits that error. |
| Important abstract statements not captured | EPICSCORE, PDF p. 1: introduction of EPICSCORE and finite-sample marginal coverage statements | Keyword extraction is not exhaustive. Use the whole page to recover context; zero extracted items cannot be interpreted as absence from the paper. |
| Publisher/PDF volume mismatch | EPICSCORE landing page says volume 286; PDF first-page footer says 244 | Manifest uses publisher bibliographic metadata and records the exact PDF hash. Do not infer volume from PDF footer alone. |
| Separate supplement excluded | Ghosh landing page links a supplementary PDF, but manifest pins only main paper | “10/10 pages” means the selected file, not all associated research material. |
| Local uploads lack publisher metadata in their source URI | Every imported source has an `upload:` URI | Publisher links/authors/license are recorded in `sources.json`; app reading uses saved page text. The source registry remains honest about original import provenance. |

## Integrity versus usefulness

All 262 quotations occur literally on their saved pages; this is the scope of the automatic source-support pass. It does not eliminate any of the issues above. “Future work not extracted” and “limitation not extracted” are missing categories in the selected parsed text, not scientific claims about the papers.

The automated outputs are preserved unchanged after the successful run. Editorial interpretation is in a separate file. No numerical precision, recall, novelty, reproducibility-of-experiments or scientific-validity score is claimed. No human approval is present; the final artifact is a review draft with explicit missing observations.
