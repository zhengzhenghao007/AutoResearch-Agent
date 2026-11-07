"""Explicit selections from saved metadata; acquisition is not evidence validation."""
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import Field, model_validator
from schemas.research import Contract
from schemas.multi_source_search import Provider, SearchHit


class AcquisitionSelection(Contract):
    batch_id: str = Field(min_length=1, max_length=64)
    source: Provider
    source_id: str = Field(min_length=1, max_length=2000)


class AcquisitionRequest(Contract):
    selections: list[AcquisitionSelection] = Field(min_length=1, max_length=5)

    @model_validator(mode='after')
    def distinct(self):
        if len({(x.batch_id, x.source, x.source_id) for x in self.selections}) != len(self.selections):
            raise ValueError('Select distinct saved metadata hits')
        return self


class AcquisitionOutcome(Contract):
    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    selection: AcquisitionSelection
    metadata: SearchHit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal['pending', 'downloaded', 'cached', 'unsupported', 'failed'] = 'pending'
    url: str = ''
    sha256: str | None = None
    error: str | None = None
    scope: str = 'Metadata is provider-reported, not verified evidence. Import explicitly to extract page-level evidence. Only canonical arXiv PDFs are supported; redirects are rejected.'
