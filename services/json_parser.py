import ast
import json
import re
from typing import Any


class JSONParser:
    """
    Parse JSON objects returned by language models.

    The parser supports:

    1. Standard JSON
    2. Markdown JSON code blocks
    3. Text before or after the JSON object
    4. Python-style dictionaries using single quotes
    5. Nested JSON objects and arrays
    """

    def parse(self, content: str) -> dict[str, Any]:
        if not content or not content.strip():
            raise ValueError(
                "The LLM response is empty."
            )

        cleaned_content = self._clean_content(content)

        direct_result = self._try_json_loads(
            cleaned_content
        )

        if direct_result is not None:
            return self._validate_object(
                direct_result
            )

        extracted_objects = self._extract_json_objects(
            cleaned_content
        )

        for json_object in extracted_objects:
            parsed_result = self._try_json_loads(
                json_object
            )

            if parsed_result is not None:
                return self._validate_object(
                    parsed_result
                )

            repaired_object = self._repair_common_errors(
                json_object
            )

            parsed_result = self._try_json_loads(
                repaired_object
            )

            if parsed_result is not None:
                return self._validate_object(
                    parsed_result
                )

            python_result = self._try_python_literal(
                json_object
            )

            if python_result is not None:
                return self._validate_object(
                    python_result
                )

        raise ValueError(
            "The LLM response did not contain "
            "a valid JSON object."
        )

    @staticmethod
    def _clean_content(content: str) -> str:
        cleaned_content = content.strip()

        cleaned_content = re.sub(
            r"^```(?:json|JSON)?\s*",
            "",
            cleaned_content,
        )

        cleaned_content = re.sub(
            r"\s*```$",
            "",
            cleaned_content,
        )

        cleaned_content = cleaned_content.replace(
            "\ufeff",
            "",
        )

        return cleaned_content.strip()

    @staticmethod
    def _try_json_loads(
        content: str,
    ) -> Any | None:
        try:
            return json.loads(content)
        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return None

    @staticmethod
    def _try_python_literal(
        content: str,
    ) -> Any | None:
        try:
            return ast.literal_eval(content)
        except (
            ValueError,
            SyntaxError,
            TypeError,
        ):
            return None

    @staticmethod
    def _validate_object(
        value: Any,
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError(
                "The parsed JSON value must be an object."
            )

        return value

    @staticmethod
    def _repair_common_errors(
        content: str,
    ) -> str:
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
        objects = []

        object_start = None
        brace_depth = 0
        inside_string = False
        escape_next = False

        for index, character in enumerate(content):
            if escape_next:
                escape_next = False
                continue

            if character == "\\" and inside_string:
                escape_next = True
                continue

            if character == '"':
                inside_string = not inside_string
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
                            object_start:index + 1
                        ]
                    )

                    object_start = None

        objects.sort(
            key=len,
            reverse=True,
        )

        return objects