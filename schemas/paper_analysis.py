from schemas.generated_prose import GeneratedProse
from pydantic import BaseModel, Field, field_validator


class PaperAnalysis(BaseModel):
    """
    Structured analysis generated from an academic paper.

    This schema is used as the structured output format
    for the LLM Reader Agent.
    """

    research_problem: GeneratedProse = Field(
        ...,
        min_length=1,
        description=(
            "The central research problem or question "
            "addressed by the paper."
        ),
    )

    methodology: GeneratedProse = Field(
        ...,
        min_length=1,
        description=(
            "A clear description of the proposed method, "
            "framework, model, or experimental procedure."
        ),
    )

    datasets: list[str] = Field(
        default_factory=list,
        description=(
            "Datasets, benchmarks, simulators, environments, "
            "robot platforms, or evaluation settings."
        ),
    )

    main_contributions: list[GeneratedProse] = Field(
        default_factory=list,
        description=(
            "The main technical or scientific contributions "
            "claimed by the paper."
        ),
    )

    limitations: list[GeneratedProse] = Field(
        default_factory=list,
        description=(
            "Explicit limitations, weaknesses, unresolved "
            "issues, or restrictions identified in the paper."
        ),
    )

    @field_validator(
        "research_problem",
        "methodology",
        mode="before",
    )
    @classmethod
    def clean_required_text(
        cls,
        value: object,
    ) -> str:
        if value is None:
            return "Not identified in the supplied paper text."

        cleaned_value = str(value).strip()

        if not cleaned_value:
            return "Not identified in the supplied paper text."

        return cleaned_value

    @field_validator(
        "datasets",
        "main_contributions",
        "limitations",
        mode="before",
    )
    @classmethod
    def normalize_string_lists(
        cls,
        value: object,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return []

            return [cleaned_value]

        if isinstance(value, tuple):
            value = list(value)

        if not isinstance(value, list):
            return [str(value).strip()]

        cleaned_items = []

        for item in value:
            cleaned_item = str(item).strip()

            if cleaned_item:
                cleaned_items.append(cleaned_item)

        return cleaned_items