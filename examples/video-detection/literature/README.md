# Literature selection and replay

On 8 November 2026 UTC, the repository search adapters requested the first 20 provider-ranked records for “AI-generated video detection” from each of arXiv, OpenAlex, Crossref and Semantic Scholar. No year or language filters were set. The first three returned 60 hits in total. Semantic Scholar returned HTTP 429. The adapter grouped these into 59 identities using its exact DOI or provider-record rule. See `queries.json` for complete request parameters, timestamps, retry information, results and groups.

We built a purposive reading set around cross-generator transfer, source-domain shift, degradation, detector cues and decision reliability. Supplementary primary-source searches used terms including “GenVidBench”, “DeMamba”, “Chameleon”, “AI generated video detection temporal frequency optical flow”, “forensic-oriented augmentation”, “motion-based shortcut learning” and “D3 training-free second-order features”. Three facial manipulation papers provide adjacent evidence. The title and author list for each entry came from the primary arXiv citation metadata. Dates identify the arXiv submission and titles reflect the record as retrieved. Metadata-only entries establish scope. Quantitative claims in the evidence file come from the specified paper pages.

The 23 records are distinct by arXiv identifier. Among provider hits, eight distinct included titles match after normalization, with three additional records for those same titles. The remaining 49 hits fall outside the curated set. These include background records about generated text, still images, video compression, quality assessment and further detector designs outside this sample. The separate targeted searches supply the remaining included papers. This is a reproducible record of a purposive review, with no claim of exhaustive coverage. One search result associated arXiv 2406.19568 with a Sora detector title. Its primary record identifies a 3D generation evaluation paper and it was excluded.

Run these commands from the repository root using its installed Python environment.

```shell
python examples/video-detection/literature/retrieve.py search
python examples/video-detection/literature/retrieve.py
python examples/video-detection/literature/retrieve.py screen
```

The retrieval script writes local PDFs and page text under the ignored `.verification/video-pdfs` directory. It applies the repository PDF worker's 20 MiB input limit, a maximum of 60 pages and a 45-second parser timeout. Four arXiv PDFs were parsed completely. Three attempted arXiv PDFs exceeded the size limit, including the excluded candidate. The retained hashes and extraction counts identify the exact files behind the page notes. Metadata and retrieval coverage are machine-readable. Evidence notes are human-readable paraphrases selected after inspection and retained separately from automated extraction.

The workflow also imported the 11-page ICCV edition of D3 from CVF and verified its page anchors. Its SHA-256 is eae035922f465a8245969a95a7e8d9e06f11ed022b06bb2c11ce4f6a5d265981. The D3 notes cite the conference PDF directly.
