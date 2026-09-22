# Synthetic evidence regression corpus

These six tiny PDFs contain original AI-authored text, not published research.
They and their annotations are dedicated to the public domain under CC0-1.0
(https://creativecommons.org/publicdomain/zero/1.0/). No third-party paper text,
images, or embedded fonts are redistributed. `generate.py` uses the existing
test PDF helper's construction technique; each manifest record records its
source, license, provenance, and SHA-256. Regenerate with
`python tests/fixtures/evidence/generate.py` from the repository root. This
resets every annotation to pending; never use it to overwrite real reviews.

Cases cover normal text, a blank page with no extractable text, bounded page
truncation, an essay without experiments, planned experiments, and a fabricated
quotation injected into otherwise valid evidence. The empty-text case exercises
the parser's no-OCR failure; it is not an image-based scanning/OCR benchmark.
The PDF text is intentionally short and does not represent real paper layout.

Run `python -m evaluation.evaluate_evidence` from the repository root. No network
or model key is needed. Exit status is nonzero when deterministic regressions
fail or manifest validation fails. `regressions` tests parser/extractor behavior
against synthetic expectations; it is never an accuracy result.

## Human review workflow

All shipped records are `pending_human_review`, so `reviewed_count` is zero and
`metrics` is null. An actual reviewer must read the exact hashed PDF, inspect
the selected page scope and truncation, exhaustively mark the eligible literal
quotes and categories, and independently judge whether each quote supports its
reported assertion (`supported`). Record their real reviewer identifier and
ISO review date, then change that record to `human_reviewed`. Never put a model
name or a fictitious person into reviewer provenance. Have another person
resolve disagreements before treating these labels as a benchmark. Add licensed
real literature with the same provenance requirements before assessing research
performance. Keep truncated labels limited to the selected pages; missing text
is not a scientific research gap.

The evaluator requires provenance fields but cannot authenticate a human's
identity or guarantee that review actually happened. Repository tests simulate
reviewed records only in temporary copies to verify metric arithmetic; these
are not human evaluations and do not modify the shipped manifest.

## Metric definitions and limits

Only `human_reviewed` records contribute metrics. Matching is exact after
whitespace normalization, keyed by page, quote, and category, one-to-one per
record. Per-category precision is matching predictions / predictions; recall
is matching predictions / annotations; missingness is unmatched annotations /
annotations. Counts are pooled across reviewed records. Zero denominators
produce null, not perfect scores. Categorization is assessed separately from
support, so an annotation with `supported: false` can still define its category.

Quote location is the fraction of predicted claims whose referenced quotes
all occur on their cited pages with matching source identity. Support is the
fraction of predicted claims referencing a quote independently marked supported
by a reviewer; unannotated quotes do not count as supported. With this literal
extractor these measure narrow traceability and annotation agreement, not
scientific truth, entailment of generated prose, or validity of experiments.
There are no confidence intervals, representative-domain guarantees, or model
performance claims. The manifest's expected categories are regression checks
only and are not silently promoted to human ground truth.
