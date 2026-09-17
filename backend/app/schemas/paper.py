from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class PaperSearchRequest(BaseModel):
    topic: str = Field(
        min_length=1,
        max_length=1000,
        description="Research topic or arXiv query.",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of papers to return.",
    )

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Research topic cannot be empty."
            )

        return cleaned_value


class PaperResponse(BaseModel):
    title: str
    authors: list[str] = Field(
        default_factory=list
    )
    summary: str = ""
    published: str = ""
    pdf_url: str = ""
    entry_id: str = ""


class PaperSearchResponse(BaseModel):
    topic: str
    plan: Any
    papers: list[PaperResponse]
    total: int