from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    kind: Literal['search','analyze']
    topic: str | None = Field(default=None, min_length=1, max_length=2000)
    max_results: int = Field(default=5, ge=1, le=20)
    run_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    selected_ids: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode='after')
    def valid_operation(self):
        if self.kind == 'search' and (not self.topic or self.run_id or self.selected_ids):
            raise ValueError('Search requires a topic only')
        if self.kind == 'analyze' and (not self.run_id or self.topic or not self.selected_ids
                                      or len(set(self.selected_ids)) != len(self.selected_ids)):
            raise ValueError('Analysis requires a run and distinct selected candidates')
        if any(not 1 <= len(i) <= 200 for i in self.selected_ids):
            raise ValueError('Invalid selected candidate')
        return self
