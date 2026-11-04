# Scanned PDF import repair

Reproduction: user-provided 14-page PDF has zero extracted characters on every page and image XObjects. The native-only parser rejects it. Preserve the user's file and existing launcher.

Implementation: keep native parsing first; for pages without text, use a separate bounded local OCR worker with bundled RapidOCR models and PDFium rendering. Limit raster size, page count, output size and runtime. Record OCR page numbers and warn in Library/Reading that recognition needs verification. No external provider or document upload. Missing OCR dependencies must provide an actionable installation message; blank pages still fail honestly.

- [ ] Add regression tests for actual raster text, mixed native/OCR pages, missing engine, and limits.
- [ ] Implement bounded OCR fallback, provenance and dependencies; preserve native-only behavior and page numbering.
- [ ] Expose provenance and upload progress in UI, update installation guidance.
- [ ] Import the provided PDF through the actual API/browser in an isolated record; verify text/evidence and saved reload without committing the private PDF.
- [ ] Full regression, review, CI and merge under prior authorization.

2026-11-05 integration finding: the supplied PDF uses image objects on page 1 and vector-outline text on pages 2–14. Image-resource detection alone imported only the first page. Added painting-operator detection and a real vector-outline PDF regression; truly blank pages remain excluded. Initial Linux CI passed; final browser and commit CI must verify the correction.
