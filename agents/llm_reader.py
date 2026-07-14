import re

from agents.base_agent import BaseAgent
from agents.reader_result import ReaderResult
from schemas.paper_analysis import PaperAnalysis
from services.llm_client import LLMClient


class LLMReaderAgent(BaseAgent):
    """
    Analyze academic papers with structured LLM output.

    The agent supports an optional reflection step. When a previous
    analysis fails review, reflection feedback can be supplied to guide
    the next reading attempt.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        max_input_characters: int = 40_000,
    ) -> None:
        if llm_client is None:
            llm_client = LLMClient(
                temperature=0.1,
                max_tokens=2000,
            )

        super().__init__(
            llm_client=llm_client,
        )

        self.max_input_characters = max_input_characters

    def analyze(
        self,
        title: str,
        abstract: str,
        extracted_text: str,
        reflection_instructions: dict | None = None,
    ) -> dict:
        """
        Analyze a paper and return a standard ReaderResult dictionary.

        Args:
            title:
                Paper title.

            abstract:
                Paper abstract.

            extracted_text:
                Text extracted from the PDF.

            reflection_instructions:
                Optional feedback generated after a previous analysis
                failed review. The feedback may contain critique,
                improvement instructions, and fields requiring attention.

        Returns:
            A dictionary generated from ReaderResult.
        """

        paper_text = self._prepare_paper_text(
            abstract=abstract,
            extracted_text=extracted_text,
        )

        response = self.structured_chat(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(
                title=title,
                paper_text=paper_text,
                reflection_instructions=reflection_instructions,
            ),
            schema=PaperAnalysis,
        )

        analysis = response.parsed

        result = ReaderResult(
            title=title,
            research_problem=analysis.research_problem,
            methodology=analysis.methodology,
            datasets=self._format_list(
                analysis.datasets,
                empty_message=(
                    "No datasets, environments, benchmarks, "
                    "or robot platforms were identified."
                ),
            ),
            main_contributions=(
                analysis.main_contributions
                or [
                    "No explicit contributions were identified."
                ]
            ),
            limitations=self._format_list(
                analysis.limitations,
                empty_message=(
                    "No explicit limitations were identified."
                ),
            ),
            model_name=response.model_name,
            elapsed_seconds=response.elapsed_seconds,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            estimated_cost_usd=0.0,
            metadata={
                "agent_name": self.agent_name,
                "reader_type": "llm-structured",
                "total_tokens": response.total_tokens,
                "input_character_count": len(paper_text),
                "raw_response": response.raw_content,
                "structured_analysis": analysis.model_dump(),
                "reflection_applied": (
                    reflection_instructions is not None
                ),
                "reflection_instructions": (
                    reflection_instructions or {}
                ),
            },
        )

        return result.to_dict()

    @staticmethod
    def _build_system_prompt() -> str:
        return """
You are an academic paper analysis agent.

Analyze only the supplied paper content.

Requirements:

1. Identify the central research problem.
2. Explain the proposed methodology precisely.
3. List datasets, benchmarks, simulators, evaluation environments,
   and robot platforms.
4. List the paper's main technical or scientific contributions.
5. List explicit limitations and clearly supported weaknesses.
6. Do not invent information.
7. Do not treat general background problems as limitations.
8. Do not treat future research motivation as an experimental
   limitation unless the paper clearly presents it that way.
9. When information is unavailable, return an empty list for
   optional list fields.
10. Keep every statement grounded in the supplied content.
11. When reflection feedback is supplied, follow it carefully.
12. Reflection feedback must not cause unsupported claims.
13. Prefer precise technical details over vague summaries.
14. Distinguish datasets, environments, benchmarks, and robot
   platforms from general background information.
15. Keep the complete response concise.
16. Each list should contain at most five items.
17. Avoid internal reasoning, planning notes, or explanations.
""".strip()

    @staticmethod
    def _build_user_prompt(
        title: str,
        paper_text: str,
        reflection_instructions: dict | None = None,
    ) -> str:
        reflection_section = ""

        if reflection_instructions:
            critique = reflection_instructions.get(
                "critique",
                [],
            )

            improvement_instructions = (
                reflection_instructions.get(
                    "improvement_instructions",
                    [],
                )
            )

            focus_fields = reflection_instructions.get(
                "focus_fields",
                [],
            )

            critique_text = LLMReaderAgent._format_prompt_list(
                critique,
                empty_message="No critique was provided.",
            )

            instruction_text = (
                LLMReaderAgent._format_prompt_list(
                    improvement_instructions,
                    empty_message=(
                        "No additional improvement instructions "
                        "were provided."
                    ),
                )
            )

            focus_text = ", ".join(
                str(field).strip()
                for field in focus_fields
                if str(field).strip()
            )

            if not focus_text:
                focus_text = "No specific fields were provided."

            reflection_section = f"""
Previous analysis review feedback:

Critique:
{critique_text}

Improvement instructions:
{instruction_text}

Fields requiring special attention:
{focus_text}

Apply this feedback carefully.

Use the supplied paper text as the only source of evidence.
Do not add a limitation, method, dataset, contribution, or result
unless it is supported by the paper content.
""".strip()

        prompt_parts = [
            f"""
Paper title:

{title}
""".strip(),
            f"""
Paper content:

{paper_text}
""".strip(),
        ]

        if reflection_section:
            prompt_parts.append(
                reflection_section
            )

        prompt_parts.append(
            """
Produce a structured academic analysis of this paper.
""".strip()
        )

        return "\n\n".join(prompt_parts)

    def _prepare_paper_text(
        self,
        abstract: str,
        extracted_text: str,
    ) -> str:
        clean_abstract = self._clean_text(
            abstract
        )

        clean_extracted_text = self._clean_text(
            extracted_text
        )

        combined_text = (
            "ABSTRACT\n"
            f"{clean_abstract}\n\n"
            "EXTRACTED PAPER TEXT\n"
            f"{clean_extracted_text}"
        )

        return combined_text[
            :self.max_input_characters
        ]

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:
        if not text:
            return ""

        cleaned_text = str(text)

        cleaned_text = cleaned_text.replace(
            "\x00",
            " ",
        )

        cleaned_text = re.sub(
            r"[ \t]+",
            " ",
            cleaned_text,
        )

        cleaned_text = re.sub(
            r"\n{3,}",
            "\n\n",
            cleaned_text,
        )

        return cleaned_text.strip()

    @staticmethod
    def _format_list(
        values: list[str],
        empty_message: str,
    ) -> str:
        clean_values = [
            str(value).strip()
            for value in values
            if str(value).strip()
        ]

        if not clean_values:
            return empty_message

        return "\n".join(
            f"* {value}"
            for value in clean_values
        )

    @staticmethod
    def _format_prompt_list(
        values: object,
        empty_message: str,
    ) -> str:
        if values is None:
            return empty_message

        if isinstance(values, str):
            clean_values = [
                values.strip()
            ]
        elif isinstance(values, list):
            clean_values = [
                str(value).strip()
                for value in values
                if str(value).strip()
            ]
        else:
            clean_value = str(values).strip()
            clean_values = (
                [clean_value]
                if clean_value
                else []
            )

        if not clean_values:
            return empty_message

        return "\n".join(
            f"* {value}"
            for value in clean_values
        )