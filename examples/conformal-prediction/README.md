# Worked case: conformal prediction with imperfect data

**Question:** How do conformal methods address missing inputs, perturbed inputs and regions with little training data—and what can we responsibly compare?

This is a complete, deliberately small workflow demonstration. It uses three real papers, original publisher PDF bytes, the normal offline importer, page extraction, rule-based claim extraction, comparison, citation registry and manuscript revision services. It is **not a systematic review, a scientific benchmark, or a human-approved manuscript**.

## The result

| Source | Parsed PDF pages | Saved quotations | Categories not extracted |
|---|---:|---:|---|
| Zaffran et al., missing values | 27 / 27 | 87 | Future work |
| Ghosh et al., robust prediction | 10 / 10 | 72 | Limitation |
| Cruz Cabezas et al., EPICSCORE | 28 / 28 | 103 | None |

The run contains **262 quotations across 65 pages**. All quotations match their saved extracted pages. That check does **not** establish correct categorization or scientific truth: the [error log](audit.md) includes counterexamples. No experiments were run, no model was called and no human approval was invented.

- [Editorial comparison and short review](review-notes.md): readable interpretation with page references, kept separate from the automated outputs.
- [Actual automatic comparison](outputs/comparison.md): unedited method-category extracts; includes extraction noise.
- [Actual automatic draft](outputs/draft.md): attributed chapter material, not a finished review.
- [Machine-readable draft](outputs/draft.json), [citation registry](outputs/citations.json), [full research record](outputs/run.json), [saved manuscript revision](outputs/manuscript-state.json), [execution record](outputs/execution.json).

## See the case in the app—no downloads or API key

From the repository root, after installing the project dependencies:

```powershell
.\.venv\Scripts\python.exe examples/conformal-prediction/reproduce.py --install
```

The command prints a URL for a **new copy** in your local JSON store. Start the backend and frontend using the [quick start](../../README.md#quick-start), then open that URL. Installation never overwrites an existing record. It imports the research snapshot; the saved manuscript file above is an audit artifact, not silently installed as your own writing.

1. **Library:** see the three imported papers. This case uses a curated corpus; it does not pretend the arXiv search found them.
2. **Reading & evidence:** choose a paper, inspect an extract beside its full extracted page. Search for a method name or filter by category. Use the publisher links below to check the original PDF; uploaded documents do not have a remotely hosted PDF viewer.
3. **Compare:** inspect the category matrix. Click **Read evidence** to return to the quotation. A blank category means “not extracted,” not “the paper has no such result.”
4. **Writing:** preview the outline, then initialize a manuscript revision. Every quoted sentence retains its source binding. The user-observations section explicitly says no data were supplied. You may edit and save; human approval and approved export remain separate actions for an actual reviewer.

## Reproduce from original PDF bytes

```powershell
# Explicitly downloads only the three publisher PDFs in sources.json.
.\.venv\Scripts\python.exe examples/conformal-prediction/reproduce.py --download --output .verification/case-replay
```

Alternatively provide `--pdf-dir PATH` containing the filenames in [sources.json](sources.json); without `--download` no network is used. The command verifies SHA256 before parsing, then creates a fresh record and writes every output. Choose a new `--output` directory for each run. Default limits remain 20 MiB per PDF and 50 pages per document. Fresh run IDs and timestamps differ; evidence text, page numbers and source hashes should match on the pinned dependency stack. `python -m pytest tests/test_worked_case.py -q` checks the committed output against the real services without downloading anything.

## Selection, attribution and license

Chosen to contrast three specific uncertainty problems, rather than rank papers that use different tasks and evaluation setups. The rejected large PDF and unsuccessful intermediate writing attempt are recorded in [audit.md](audit.md). No claims about search recall follow from this purposive selection.

1. **Margaux Zaffran, Aymeric Dieuleveut, Julie Josse, Yaniv Romano (2023).** *Conformal Prediction with Missing Values*. PMLR 202:40578–40604. [Publisher and original PDF](https://proceedings.mlr.press/v202/zaffran23a.html).
2. **Subhankar Ghosh, Yuanjie Shi, Taha Belkhouja, Yan Yan, Jana Doppa, Brian Jones (2023).** *Probabilistically robust conformal prediction*. PMLR 216:681–690. [Publisher and original PDF](https://proceedings.mlr.press/v216/ghosh23a.html). Only the main ten-page PDF is in this corpus; the separate supplement is not included.
3. **Luben Miguel Cruz Cabezas, Vagner Silva Santos, Thiago Ramos, Rafael Izbicki (2025).** *Epistemic Uncertainty in Conformal Scores: A Unified Approach*. PMLR 286:443–470. [Publisher and original PDF](https://proceedings.mlr.press/v286/cruz-cabezas25a.html).

Authors retain copyright. The [PMLR publication agreement](https://proceedings.mlr.press/pmlr-license-agreement.pdf), clauses 2–3, specifies **[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)** and attribution to the original publication. License checked 2026-10-26. Publisher PDF bytes are unmodified and not committed; extracted text, quotations, comparisons and drafts are transformations of those works and retain this attribution and license. Extraction may change whitespace, reading order and typography. No author endorsement is implied. The repository's software license does not replace these source licenses.
