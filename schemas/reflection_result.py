from pydantic import BaseModel, Field, field_validator


class ReflectionResult(BaseModel):
    """
    Structured feedback used to improve a paper analysis.
    """

    should_retry: bool = Field(
        ...,
        description=(
            "Whether the paper should be analyzed again."
        ),
    )

    critique: list[str] = Field(
        default_factory=list,
        description=(
            "Specific problems found in the previous analysis."
        ),
    )

    improvement_instructions: list[str] = Field(
        default_factory=list,
        description=(
            "Concrete instructions for producing a better analysis."
        ),
    )

    focus_fields: list[str] = Field(
        default_factory=list,
        description=(
            "Analysis fields that require special attention."
        ),
    )

    @field_validator(
        "critique",
        "improvement_instructions",
        "focus_fields",
        mode="before",
    )
    @classmethod
    def normalize_lists(
        cls,
        value: object,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            cleaned_value = value.strip()
            return [cleaned_value] if cleaned_value else []

        if not isinstance(value, list):
            value = [value]

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]