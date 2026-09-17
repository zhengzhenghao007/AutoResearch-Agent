from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.paper import PaperResponse


class PaperAnalysisRequest(BaseModel):
    paper: PaperResponse

    topic: str | None = Field(
        default=None,
        max_length=1000,
        description=(
            "Original research topic. "
            "The paper title is used when omitted."
        ),
    )

    plan: Any = Field(
        default=None,
        description="Optional research plan from the search response.",
    )

    max_pages: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of PDF pages to read.",
    )

    reader_mode: Literal[
        "auto",
        "llm",
        "rule",
    ] = Field(
        default="auto",
        description="Reader implementation used for analysis.",
    )

    max_reader_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Number of ReaderPipeline retry attempts.",
    )

    @field_validator("topic")
    @classmethod
    def clean_topic(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            return None

        return cleaned_value


class PaperAnalysisResponse(BaseModel):
    topic: str
    paper: PaperResponse

    pdf_path: str | None = None
    extracted_text_length: int = 0
    extracted_text_preview: str = ""

    analysis: Any = None
    review: Any = None
    reader_pipeline: Any = None

    used_fallback: bool = False
    pipeline_error: str | None = None