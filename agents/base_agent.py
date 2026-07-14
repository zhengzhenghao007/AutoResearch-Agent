from abc import ABC
from typing import Type

from pydantic import BaseModel

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
    ) -> LLMResponse:
        print(f"[{self.agent_name}] Running...")

        return self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def structured_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
    ) -> StructuredLLMResponse:
        print(
            f"[{self.agent_name}] Structured output..."
        )

        return self.llm.structured_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_schema=schema,
        )