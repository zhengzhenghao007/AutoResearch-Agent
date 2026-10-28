"""Bounded immutable research material specifications; clients never supply markup."""
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class WorkspaceItemRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    kind: Literal['note', 'table', 'figure']
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(default='', max_length=10000)
    dataset_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    columns: list[str] = Field(default_factory=list, max_length=50)
    x_column: str | None = Field(default=None, max_length=64)
    chart_type: Literal['bar', 'line', 'scatter'] = 'bar'

    @field_validator('title', 'text')
    @classmethod
    def utf8_text(cls, value):
        value.encode('utf-8')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            raise ValueError('Control characters are not supported')
        return value

    @model_validator(mode='after')
    def valid_spec(self):
        if len(self.columns) != len(set(self.columns)):
            raise ValueError('Duplicate selected columns')
        if self.kind == 'note':
            if not self.text or self.columns or self.x_column:
                raise ValueError('Notes require text and cannot select plot columns')
        else:
            if not self.dataset_id or not self.columns:
                raise ValueError('Tables and figures require a dataset and numeric columns')
            if self.kind == 'figure' and (len(self.columns) != 1 or
                    (self.chart_type in ('line', 'scatter') and not self.x_column)):
                raise ValueError('Figures require one Y column; line/scatter require X')
        return self


class WorkspaceItem(WorkspaceItemRequest):
    id: str = Field(default_factory=lambda: uuid4().hex, pattern=r'^[a-f0-9]{32}$')
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dataset_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')


class WorkspacePreview(BaseModel):
    model_config = ConfigDict(extra='forbid')
    item: WorkspaceItemRequest
    dataset_sha256: str | None
    headers: list[str]
    rows: list[list[str | int | float | None]]
    svg: str | None
    markdown: str
    warnings: list[str]


class AssetBinding(WorkspacePreview):
    item_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    title: str
