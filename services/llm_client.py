import json
import os
import re
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

    Supported capabilities:

    1. Normal text generation
    2. Pydantic structured output
    3. Strict JSON fallback
    4. Local JSON repair
    5. LLM-assisted JSON repair
    6. Token and latency tracking
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> None:
        self.api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

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
        Send a standard text request to the configured model.
        """

        messages = self._build_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        start_time = time.perf_counter()

        try:
            response = self.model.invoke(
                messages
            )

        except Exception as error:
            raise RuntimeError(
                f"LLM request failed: {error}"
            ) from error

        elapsed_seconds = (
            time.perf_counter() - start_time
        )

        content = self._extract_content(
            response
        )

        usage = self._extract_usage(
            response
        )

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
        Generate and validate structured LLM output.

        Processing order:

        1. Provider structured output
        2. Local repair of provider raw output
        3. Strict JSON request
        4. Local repair of strict JSON output
        5. LLM-assisted repair request
        """

        messages = self._build_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        start_time = time.perf_counter()

        structured_error: Exception | None = None

        structured_model = (
            self.model.with_structured_output(
                output_schema,
                method="json_schema",
                include_raw=True,
            )
        )

        try:
            response = structured_model.invoke(
                messages
            )

            if isinstance(response, dict):
                parsed = response.get(
                    "parsed"
                )

                raw = response.get(
                    "raw"
                )

                parsing_error = response.get(
                    "parsing_error"
                )

                if parsed is not None:
                    parsed = self._validate_structured_value(
                        value=parsed,
                        output_schema=output_schema,
                    )

                    elapsed_seconds = (
                        time.perf_counter()
                        - start_time
                    )

                    return self._build_structured_response(
                        parsed=parsed,
                        raw=raw,
                        elapsed_seconds=elapsed_seconds,
                    )

                if raw is not None:
                    repaired = (
                        self._repair_structured_response(
                            raw=raw,
                            output_schema=output_schema,
                        )
                    )

                    if repaired is not None:
                        elapsed_seconds = (
                            time.perf_counter()
                            - start_time
                        )

                        return (
                            self._build_structured_response(
                                parsed=repaired,
                                raw=raw,
                                elapsed_seconds=(
                                    elapsed_seconds
                                ),
                            )
                        )

                structured_error = (
                    parsing_error
                    or RuntimeError(
                        "No parsed structured data "
                        "was returned."
                    )
                )

            else:
                structured_error = RuntimeError(
                    "Structured response has an "
                    "unexpected format."
                )

        except Exception as error:
            structured_error = error

        print(
            "[LLMClient] Provider structured output "
            "failed. Requesting strict JSON..."
        )

        schema_text = json.dumps(
            output_schema.model_json_schema(),
            indent=2,
            ensure_ascii=False,
        )

        strict_system_prompt = f"""
{system_prompt}

You must return exactly one valid JSON object.

Strict output rules:

1. Return JSON only.
2. Start the response with an opening curly brace.
3. End the response with a closing curly brace.
4. Do not use Markdown.
5. Do not use code fences.
6. Do not add explanations before the JSON.
7. Do not add explanations after the JSON.
8. Follow the supplied JSON Schema exactly.
9. Use double quotes for all keys and string values.
10. Keep all values concise.
11. Do not include internal reasoning.

Required JSON Schema:

{schema_text}
""".strip()

        strict_messages = self._build_messages(
            system_prompt=strict_system_prompt,
            user_prompt=user_prompt,
        )

        try:
            raw_response = self.model.invoke(
                strict_messages
            )

        except Exception as fallback_error:
            raise RuntimeError(
                "Provider structured output and strict JSON "
                "fallback both failed. "
                f"Structured error: {structured_error}. "
                f"Fallback error: {fallback_error}"
            ) from fallback_error

        repaired = self._repair_structured_response(
            raw=raw_response,
            output_schema=output_schema,
        )

        if repaired is not None:
            elapsed_seconds = (
                time.perf_counter()
                - start_time
            )

            return self._build_structured_response(
                parsed=repaired,
                raw=raw_response,
                elapsed_seconds=elapsed_seconds,
            )

        malformed_content = self._extract_content(
            raw_response,
            allow_empty=True,
        )

        print(
            "[LLMClient] Strict JSON was invalid. "
            "Trying one repair request..."
        )

        repair_system_prompt = f"""
You repair malformed structured output.

Convert the supplied content into exactly one valid JSON object
matching the supplied JSON Schema.

Rules:

1. Preserve factual content supported by the input.
2. Return JSON only.
3. Do not use Markdown.
4. Do not use code fences.
5. Do not explain your changes.
6. Start with an opening curly brace.
7. End with a closing curly brace.
8. Use double quotes for all keys and string values.
9. Remove unsupported commentary.
10. Follow the JSON Schema exactly.

Required JSON Schema:

{schema_text}
""".strip()

        repair_user_prompt = f"""
Malformed output:

{malformed_content}

Return the repaired JSON object.
""".strip()

        try:
            repair_response = self.model.invoke(
                self._build_messages(
                    system_prompt=repair_system_prompt,
                    user_prompt=repair_user_prompt,
                )
            )

        except Exception as repair_error:
            raise RuntimeError(
                "Unable to repair structured output. "
                f"Structured error: {structured_error}. "
                f"Repair request error: {repair_error}"
            ) from repair_error

        final_parsed = self._repair_structured_response(
            raw=repair_response,
            output_schema=output_schema,
        )

        if final_parsed is None:
            final_content = self._extract_content(
                repair_response,
                allow_empty=True,
            )

            raise RuntimeError(
                "Unable to convert the response into the "
                "required schema. "
                f"Response preview: {final_content[:500]}"
            )

        elapsed_seconds = (
            time.perf_counter()
            - start_time
        )

        return self._build_structured_response(
            parsed=final_parsed,
            raw=repair_response,
            elapsed_seconds=elapsed_seconds,
        )

    def _build_structured_response(
        self,
        parsed: StructuredModel,
        raw: object | None,
        elapsed_seconds: float,
    ) -> StructuredLLMResponse:
        """
        Build a standard structured response object.
        """

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

        usage = self._extract_usage(
            raw
        )

        raw_content = self._extract_content(
            raw,
            allow_empty=True,
        )

        return StructuredLLMResponse(
            parsed=parsed,
            model_name=self._extract_model_name(
                raw
            ),
            elapsed_seconds=elapsed_seconds,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            raw_content=raw_content,
        )

    @staticmethod
    def _validate_structured_value(
        value: object,
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        """
        Validate a structured value against the schema.
        """

        if isinstance(
            value,
            output_schema,
        ):
            return value

        try:
            return output_schema.model_validate(
                value
            )

        except Exception as error:
            raise RuntimeError(
                "The structured response did not "
                "match the required schema."
            ) from error

    @staticmethod
    def _build_messages(
        system_prompt: str,
        user_prompt: str,
    ) -> list[dict[str, str]]:
        """
        Build OpenAI-compatible chat messages.
        """

        if not user_prompt.strip():
            raise ValueError(
                "User prompt cannot be empty."
            )

        messages: list[
            dict[str, str]
        ] = []

        if system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": (
                        system_prompt.strip()
                    ),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": (
                    user_prompt.strip()
                ),
            }
        )

        return messages

    @staticmethod
    def _extract_content(
        response: object,
        allow_empty: bool = False,
    ) -> str:
        """
        Extract text content from a LangChain response.
        """

        content = getattr(
            response,
            "content",
            "",
        )

        if isinstance(
            content,
            list,
        ):
            content_parts: list[str] = []

            for item in content:
                if isinstance(
                    item,
                    dict,
                ):
                    text = item.get(
                        "text"
                    )

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

        content = str(
            content
        ).strip()

        if (
            not content
            and not allow_empty
        ):
            raise RuntimeError(
                "The LLM returned an empty response."
            )

        return content

    @staticmethod
    def _extract_usage(
        response: object,
    ) -> dict[str, int]:
        """
        Extract token usage from a LangChain response.
        """

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
                    (
                        input_tokens
                        + output_tokens
                    ),
                ),
            )
            or (
                input_tokens
                + output_tokens
            )
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
        """
        Extract the actual model selected by OpenRouter.
        """

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

    @classmethod
    def _repair_structured_response(
        cls,
        raw: object,
        output_schema: type[StructuredModel],
    ) -> StructuredModel | None:
        """
        Recover a Pydantic object from raw model output.

        Supported cases include:

        1. Markdown code fences
        2. Text before the JSON object
        3. Text after the JSON object
        4. Trailing commas
        5. Smart quotation marks
        6. Python-style dictionaries
        """

        if raw is None:
            return None

        raw_content = cls._extract_content(
            raw,
            allow_empty=True,
        )

        if not raw_content:
            return None

        cleaned_content = (
            cls._clean_json_content(
                raw_content
            )
        )

        candidate_contents = [
            cleaned_content,
        ]

        extracted_objects = (
            cls._extract_json_objects(
                cleaned_content
            )
        )

        for extracted_object in extracted_objects:
            if (
                extracted_object
                not in candidate_contents
            ):
                candidate_contents.append(
                    extracted_object
                )

        for candidate in candidate_contents:
            repaired_candidate = (
                cls._repair_common_json_errors(
                    candidate
                )
            )

            parsed_json = cls._try_parse_json(
                repaired_candidate
            )

            if parsed_json is None:
                continue

            try:
                return output_schema.model_validate(
                    parsed_json
                )

            except (
                ValueError,
                TypeError,
            ):
                continue

        return None

    @staticmethod
    def _try_parse_json(
        content: str,
    ) -> object | None:
        """
        Parse JSON with a small Python dictionary fallback.
        """

        try:
            return json.loads(
                content
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            pass

        try:
            import ast

            parsed = ast.literal_eval(
                content
            )

            if isinstance(
                parsed,
                dict,
            ):
                return parsed

        except (
            ValueError,
            SyntaxError,
            TypeError,
        ):
            pass

        return None

    @staticmethod
    def _clean_json_content(
        content: str,
    ) -> str:
        """
        Remove common Markdown wrappers around JSON.
        """

        cleaned = content.strip()

        cleaned = cleaned.replace(
            "\ufeff",
            "",
        )

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        return cleaned.strip()

    @staticmethod
    def _repair_common_json_errors(
        content: str,
    ) -> str:
        """
        Repair small JSON formatting problems.
        """

        repaired = content.strip()

        repaired = re.sub(
            r",\s*([}\]])",
            r"\1",
            repaired,
        )

        repaired = repaired.replace(
            "\t",
            " ",
        )

        repaired = re.sub(
            r"[\u201c\u201d]",
            '"',
            repaired,
        )

        repaired = re.sub(
            r"[\u2018\u2019]",
            "'",
            repaired,
        )

        return repaired

    @staticmethod
    def _extract_json_objects(
        content: str,
    ) -> list[str]:
        """
        Extract balanced JSON objects from mixed text.
        """

        objects: list[str] = []

        object_start: int | None = None
        brace_depth = 0
        inside_string = False
        escape_next = False

        for index, character in enumerate(
            content
        ):
            if escape_next:
                escape_next = False
                continue

            if (
                character == "\\"
                and inside_string
            ):
                escape_next = True
                continue

            if character == '"':
                inside_string = (
                    not inside_string
                )
                continue

            if inside_string:
                continue

            if character == "{":
                if brace_depth == 0:
                    object_start = index

                brace_depth += 1

            elif character == "}":
                if brace_depth == 0:
                    continue

                brace_depth -= 1

                if (
                    brace_depth == 0
                    and object_start is not None
                ):
                    objects.append(
                        content[
                            object_start:
                            index + 1
                        ]
                    )

                    object_start = None

        objects.sort(
            key=len,
            reverse=True,
        )

        return objects