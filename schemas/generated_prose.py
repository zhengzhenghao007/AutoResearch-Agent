"""Prose only receives editorial treatment when a fresh model response is parsed."""
from typing import Annotated

from pydantic import BeforeValidator, ValidationInfo

from services.academic_humanizer import humanize


def _edit_generated(value: object, info: ValidationInfo) -> object:
    if isinstance(value, str) and info.context and info.context.get("generated_prose"):
        return humanize(value)
    return value


GeneratedProse = Annotated[str, BeforeValidator(_edit_generated)]
