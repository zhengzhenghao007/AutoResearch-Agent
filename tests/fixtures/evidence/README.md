# Synthetic evidence regression corpus

These seven tiny PDFs contain original synthetic text or generated raster pixels, not published research.
They and their annotations are dedicated to the public domain under CC0-1.0
(https://creativecommons.org/publicdomain/zero/1.0/). No third-party paper text, images, or embedded fonts are redistributed. The raster-only page uses original grayscale bars. `generate.py` uses the existing
test PDF helper's construction technique; each manifest record records its
source, license, provenance, and SHA-256. Regenerate with
`python tests/fixtures/evidence/generate.py --output-dir .verification/new-corpus`
from the repository root, choosing a new output directory each time. The generator
refuses to overwrite any existing manifest or generated PDF before writing anything.
New output has pending labels; compare it separately and preserve existing human
reviews rather than replacing the reviewed corpus. The default output directory
is the shipped corpus, so running without an explicit new directory fails safely.

Cases cover normal text, a blank page, a nonblank raster-only page, bounded page
truncation, an essay without experiments, planned experiments, and a fabricated
quotation injected into otherwise valid evidence. The blank and image-only cases exercise the parser's explicit no-OCR failure.
The image-only PDF embeds pixel data and no text layer; it simulates a scanned
page, but is not a real scanned-paper or OCR-accuracy benchmark.
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

## Offline review packet

Export a new self-contained packet from the repository root:

```powershell
python -m evaluation.review_packet export tests/fixtures/evidence/manifest.json .verification/review-packet
```

Open `.verification/review-packet/index.html` in a browser. It contains original
PDF links, extracted page text, source/license/hash information, the selected
page scope, and explicit truncation or no-readable-text notices. It requires no
server or network. Existing annotations are clearly labelled as draft/reference
material; `reviews.json` always starts with blank, incomplete human review rows.

A real reviewer edits `reviews.json`. For each fully reviewed record, set
`completed` to true, provide their real `reviewer` identifier and ISO
`reviewed_at` date, and exhaustively enter `annotations` with `page`, literal
`quote`, `category`, and boolean `supported`. Categories are defined by the
existing evidence contract and shown in the packet. Leave unfinished rows
unchanged. Empty annotations are valid when no eligible evidence exists; an
image-only PDF still requires visual inspection of the linked original, since
this tool does not provide OCR. Completion records an attestation, not proof of
reviewer identity or scientific correctness.

Import into a different, nonexistent directory:

```powershell
python -m evaluation.review_packet import tests/fixtures/evidence/manifest.json .verification/review-packet/reviews.json .verification/reviewed-corpus
python -m evaluation.evaluate_evidence .verification/reviewed-corpus/manifest.json
```

Import verifies the exact source manifest hash, all record identities, PDF
hashes, page limits, reviewer/date metadata, and every completed quotation's
location. At least one completed row is required. Only completed rows replace
review metadata and annotations; incomplete rows preserve the source record.
Regression expectations remain unchanged. The new corpus includes copied PDFs
and `import_audit.json`, binding the source manifest and review file hashes.
Neither command overwrites an existing output directory, and the source corpus
is never modified. If source bytes change after export, create a new packet and
review that version. The exporter does not promote automatic labels to human
labels, and no actual human review is supplied by this implementation.
