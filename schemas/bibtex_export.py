"""Standalone export contract; snapshots and CitationRegistry remain unchanged."""
from typing import Literal
from pydantic import Field
from schemas.research import Contract


class SkippedBibtexSource(Contract):
    source_id: str
    reason: Literal['missing_bibliographic_identity'] = 'missing_bibliographic_identity'


class BibtexExport(Contract):
    run_id: str
    # Preserve trailing newline for exact API/CLI byte-equivalent text.
    bibtex: str = Field()
    skipped_sources: list[SkippedBibtexSource]

    model_config = {'str_strip_whitespace': False}
