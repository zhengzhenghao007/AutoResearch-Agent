from typing import Literal

from pydantic import BaseModel, Field, field_validator


ReflectionField = Literal[
    "research_problem",
    "methodology",
    "datasets",
    "main_contributions",
    "limitations",
]


class ReflectionResult(BaseModel):
    """
    Structured feedback used to improve a paper analysis.
    """

    should_retry: bool = Field(
        ...,
        description=(
            "Whether another paper analysis attempt is required."
        ),
    )

    critique: list[str] = Field(
        default_factory=list,
        max_length=5,
        description=(
            "Specific weaknesses found in the previous analysis. "
            "Each item must be a concise complete sentence."
        ),
    )

    improvement_instructions: list[str] = Field(
        default_factory=list,
        max_length=5,
        description=(
            "Concrete instructions for improving the next analysis. "
            "Each item must be directly actionable."
        ),
    )

    focus_fields: list[ReflectionField] = Field(
        default_factory=list,
        description=(
            "Fields requiring improvement. Values must use "
            "the supported paper analysis field names."
        ),
    )

    @field_validator(
        "critique",
        "improvement_instructions",
        mode="before",
    )
    @classmethod
    def normalize_text_lists(
        cls,
        value: object,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            value = [value]

        cleaned_items = []

        for item in value:
            cleaned_item = str(item).strip()

            if not cleaned_item:
                continue

            if len(cleaned_item) > 500:
                cleaned_item = cleaned_item[:500].rstrip()

            cleaned_items.append(cleaned_item)

        return cleaned_items[:5]

    @field_validator(
        "focus_fields",
        mode="before",
    )
    @classmethod
    def normalize_focus_fields(
        cls,
        value: object,
    ) -> list[str]:
        allowed_fields = {
            "research_problem",
            "methodology",
            "datasets",
            "main_contributions",
            "limitations",
        }

        if value is None:
            return []

        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            value = [value]

        cleaned_fields = []

        for item in value:
            cleaned_item = str(item).strip()

            if cleaned_item in allowed_fields:
                cleaned_fields.append(cleaned_item)

        return list(dict.fromkeys(cleaned_fields))