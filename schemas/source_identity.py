"""User declarations, never externally verified bibliographic identity."""
import re
from datetime import datetime, timezone
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class IdentityContract(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class SourceIdentityRequest(IdentityContract):
    source_id: str = Field(min_length=1)
    action: Literal['set', 'clear']
    doi: str | None = Field(default=None, max_length=2048)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator('doi')
    @classmethod
    def normalize_doi(cls, value):
        if value is None:
            return None
        if value.startswith('https://doi.org/'):
            value = value[len('https://doi.org/'):]
        # Deliberately supported ASCII subset, not a complete DOI validator.
        if not re.fullmatch(r'10\.[0-9]{4,9}/[-._;()/:A-Za-z0-9]+', value):
            raise ValueError('Unsupported DOI syntax; use a bare DOI or canonical https://doi.org/ DOI URL')
        return value.lower()

    @model_validator(mode='after')
    def validate_action(self):
        if (self.action == 'set') != (self.doi is not None):
            raise ValueError('set requires a DOI; clear requires no DOI')
        return self


class IdentitySourceSnapshot(IdentityContract):
    id: str = Field(min_length=1)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    uri: str = Field(min_length=1)
    title: str = Field(min_length=1)


class SourceIdentityAnnotation(SourceIdentityRequest):
    source: IdentitySourceSnapshot
    provenance: Literal['user_supplied'] = 'user_supplied'
    recorded_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode='after')
    def validate_source(self):
        if self.source_id != self.source.id:
            raise ValueError('Identity annotation source does not match captured source')
        return self


class CurrentSourceIdentity(IdentityContract):
    source: IdentitySourceSnapshot
    active: bool
    doi: str | None
    provenance: Literal['user_supplied'] | None


class IdentityConflict(IdentityContract):
    doi: str
    source_ids: list[str]


class SourceIdentities(IdentityContract):
    run_id: str
    sources: list[CurrentSourceIdentity]
    conflicts: list[IdentityConflict]
