import os
import time
from dataclasses import dataclass
from typing import Optional, TypeVar

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


load_dotenv()


StructuredModel = TypeVar(
    "StructuredModel",
    bound=BaseModel,
)


@dataclass
class LLMResponse:
    """
    Standard text response returned by the shared LLM client.
    """

    content: str
    model_name: str
    elapsed_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class StructuredLLMResponse:
    """
    Structured response returned by the shared LLM client.
    """

    parsed: BaseModel
    model_name: str
    elapsed_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    raw_content: str


class LLMClient:
    """
    Shared LLM client used by AutoResearch-Agent.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        self.base_url = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        )

        self.model_name = (
            model_name
            or os.getenv("OPENROUTER_MODEL")
            or "openrouter/free"
        )

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY was not found. "
                "Please add it to the project .env file."
            )

        self.model = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse:
        """
        Send a normal text request to the configured LLM.
        """

        messages = self._build_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        start_time = time.perf_counter()

        try:
            response = self.model.invoke(messages)

        except Exception as error:
            raise RuntimeError(
                f"LLM request failed: {error}"
            ) from error

        elapsed_seconds = (
            time.perf_counter() - start_time
        )

        content = self._extract_content(response)

        usage = self._extract_usage(response)

        return LLMResponse(
            content=content,
            model_name=self._extract_model_name(
                response
            ),
            elapsed_seconds=elapsed_seconds,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
        )

    def structured_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[StructuredModel],
    ) -> StructuredLLMResponse:
        """
        Ask the configured LLM to return a Pydantic model.

        Args:
            system_prompt:
                Instructions defining the model role.

            user_prompt:
                The task and source content.

            output_schema:
                A Pydantic model class describing the
                required structured output.

        Returns:
            A StructuredLLMResponse containing the parsed
            Pydantic object and request metadata.
        """

        messages = self._build_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        structured_model = (
            self.model.with_structured_output(
                output_schema,
                method="json_schema",
                include_raw=True,
            )
        )

        start_time = time.perf_counter()

        try:
            response = structured_model.invoke(
                messages
            )

        except Exception as error:
            raise RuntimeError(
                "Structured LLM request failed: "
                f"{error}"
            ) from error

        elapsed_seconds = (
            time.perf_counter() - start_time
        )

        if not isinstance(response, dict):
            raise RuntimeError(
                "Structured LLM response has an "
                "unexpected format."
            )

        parsed = response.get("parsed")
        raw = response.get("raw")
        parsing_error = response.get(
            "parsing_error"
        )

        if parsing_error is not None:
            raise RuntimeError(
                "Structured output parsing failed: "
                f"{parsing_error}"
            )

        if parsed is None:
            raise RuntimeError(
                "The structured LLM response did "
                "not contain parsed data."
            )

        if not isinstance(parsed, output_schema):
            try:
                parsed = output_schema.model_validate(
                    parsed
                )

            except Exception as error:
                raise RuntimeError(
                    "The structured response did not "
                    "match the required schema."
                ) from error

        if raw is None:
            return StructuredLLMResponse(
                parsed=parsed,
                model_name=self.model_name,
                elapsed_seconds=elapsed_seconds,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                raw_content="",
            )

        usage = self._extract_usage(raw)

        raw_content = self._extract_content(
            raw,
            allow_empty=True,
        )

        return StructuredLLMResponse(
            parsed=parsed,
            model_name=self._extract_model_name(raw),
            elapsed_seconds=elapsed_seconds,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            raw_content=raw_content,
        )

    @staticmethod
    def _build_messages(
        system_prompt: str,
        user_prompt: str,
    ) -> list[dict[str, str]]:
        if not user_prompt.strip():
            raise ValueError(
                "User prompt cannot be empty."
            )

        messages = []

        if system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": user_prompt.strip(),
            }
        )

        return messages

    @staticmethod
    def _extract_content(
        response: object,
        allow_empty: bool = False,
    ) -> str:
        content = getattr(
            response,
            "content",
            "",
        )

        if isinstance(content, list):
            content_parts = []

            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")

                    if text:
                        content_parts.append(
                            str(text)
                        )
                    else:
                        content_parts.append(
                            str(item)
                        )

                else:
                    content_parts.append(
                        str(item)
                    )

            content = "\n".join(
                content_parts
            )

        content = str(content).strip()

        if not content and not allow_empty:
            raise RuntimeError(
                "The LLM returned an empty response."
            )

        return content

    @staticmethod
    def _extract_usage(
        response: object,
    ) -> dict[str, int]:
        usage_metadata = getattr(
            response,
            "usage_metadata",
            None,
        ) or {}

        response_metadata = getattr(
            response,
            "response_metadata",
            None,
        ) or {}

        token_usage = response_metadata.get(
            "token_usage",
            {},
        ) or {}

        input_tokens = int(
            usage_metadata.get(
                "input_tokens",
                token_usage.get(
                    "prompt_tokens",
                    0,
                ),
            )
            or 0
        )

        output_tokens = int(
            usage_metadata.get(
                "output_tokens",
                token_usage.get(
                    "completion_tokens",
                    0,
                ),
            )
            or 0
        )

        total_tokens = int(
            usage_metadata.get(
                "total_tokens",
                token_usage.get(
                    "total_tokens",
                    input_tokens + output_tokens,
                ),
            )
            or input_tokens + output_tokens
        )

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    def _extract_model_name(
        self,
        response: object,
    ) -> str:
        response_metadata = getattr(
            response,
            "response_metadata",
            None,
        ) or {}

        return str(
            response_metadata.get(
                "model_name",
                self.model_name,
            )
        )