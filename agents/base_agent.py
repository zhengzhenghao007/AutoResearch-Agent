from abc import ABC
from dataclasses import replace
from typing import Literal, Type

from pydantic import BaseModel

from services.academic_humanizer import humanize
from services.llm_client import (
    LLMClient,
    LLMResponse,
    StructuredLLMResponse,
)


class BaseAgent(ABC):
    """
    Base class for every agent in AutoResearch-Agent.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()

    @property
    def agent_name(self) -> str:
        return self.__class__.__name__

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        audience: Literal['user', 'internal'] = 'user',
    ) -> LLMResponse:
        print(f"[{self.agent_name}] Running...")

        response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return replace(response, content=humanize(response.content)) if audience == 'user' else response

    def structured_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
    ) -> StructuredLLMResponse:
        print(
            f"[{self.agent_name}] Structured output..."
        )

        response = self.llm.structured_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_schema=schema,
        )
        parsed = schema.model_validate(
            response.parsed.model_dump(), context={"generated_prose": True}
        )
        return replace(response, parsed=parsed)