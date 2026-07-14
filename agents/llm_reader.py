import re

from agents.reader_result import ReaderResult
from schemas.paper_analysis import PaperAnalysis
from services.llm_client import LLMClient


class LLMReaderAgent:
    """
    Analyze academic papers with structured LLM output.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        max_input_characters: int = 40_000,
    ) -> None:
        self.llm_client = llm_client or LLMClient(
            temperature=0.1,
            max_tokens=2000,
        )

        self.max_input_characters = (
            max_input_characters
        )

    def analyze(
        self,
        title: str,
        abstract: str,
        extracted_text: str,
    ) -> dict:
        """
        Analyze a paper and return a ReaderResult dictionary.
        """

        paper_text = self._prepare_paper_text(
            abstract=abstract,
            extracted_text=extracted_text,
        )

        response = self.llm_client.structured_chat(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(
                title=title,
                paper_text=paper_text,
            ),
            output_schema=PaperAnalysis,
        )

        analysis = response.parsed

        result = ReaderResult(
            title=title,
            research_problem=analysis.research_problem,
            methodology=analysis.methodology,
            datasets=self._format_list(
                analysis.datasets,
                empty_message=(
                    "No datasets, environments, "
                    "benchmarks, or robot platforms "
                    "were identified."
                ),
            ),
            main_contributions=(
                analysis.main_contributions
                or [
                    "No explicit contributions "
                    "were identified."
                ]
            ),
            limitations=self._format_list(
                analysis.limitations,
                empty_message=(
                    "No explicit limitations "
                    "were identified."
                ),
            ),
            model_name=response.model_name,
            elapsed_seconds=(
                response.elapsed_seconds
            ),
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            estimated_cost_usd=0.0,
            metadata={
                "reader_type": "llm-structured",
                "total_tokens": (
                    response.total_tokens
                ),
                "input_character_count": len(
                    paper_text
                ),
                "raw_response": (
                    response.raw_content
                ),
                "structured_analysis": (
                    analysis.model_dump()
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
3. List datasets, benchmarks, simulators,
   evaluation environments, and robot platforms.
4. List the paper's main technical or scientific
   contributions.
5. List explicit limitations and clearly supported
   weaknesses.
6. Do not invent information.
7. Do not treat general background problems as
   limitations.
8. Do not treat future research motivation as an
   experimental limitation unless the paper clearly
   presents it that way.
9. When information is unavailable, return an empty
   list for optional list fields.
10. Keep every statement grounded in the supplied
    content.
""".strip()

    @staticmethod
    def _build_user_prompt(
        title: str,
        paper_text: str,
    ) -> str:
        return f"""
Paper title:

{title}

Paper content:

{paper_text}

Produce a structured academic analysis of this paper.
""".strip()

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

        text = text.replace(
            "\x00",
            " ",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

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