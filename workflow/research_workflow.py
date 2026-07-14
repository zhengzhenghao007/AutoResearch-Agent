from pathlib import Path
from typing import Any

from agents.llm_reader import LLMReaderAgent
from agents.planner import PlannerAgent
from agents.reader import ReaderAgent
from agents.reflection import ReflectionAgent
from agents.researcher import ResearcherAgent
from agents.reviewer import ReviewerAgent
from pipelines.reader_pipeline import ReaderPipeline
from tools.pdf_reader import download_pdf, extract_text_from_pdf


class ResearchWorkflow:
    """
    Coordinate the complete academic research workflow.

    Reader modes:

    rule
        Use the deterministic rule-based reader.

    llm
        Use the LLM ReaderPipeline.
        Any LLM or pipeline error stops the workflow.

    auto
        Use the LLM ReaderPipeline first.
        Fall back to the rule-based reader when the pipeline fails.
    """

    VALID_READER_MODES = {
        "rule",
        "llm",
        "auto",
    }

    def __init__(
        self,
        reader_mode: str = "auto",
        max_reader_retries: int = 2,
    ) -> None:
        if reader_mode not in self.VALID_READER_MODES:
            valid_modes = ", ".join(
                sorted(self.VALID_READER_MODES)
            )

            raise ValueError(
                f"Invalid reader mode: {reader_mode}. "
                f"Valid modes are: {valid_modes}."
            )

        if max_reader_retries < 0:
            raise ValueError(
                "max_reader_retries must be greater than "
                "or equal to 0."
            )

        self.reader_mode = reader_mode
        self.max_reader_retries = max_reader_retries

        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()

        self.rule_reader = ReaderAgent()
        self.rule_reviewer = ReviewerAgent()

        self.reader_pipeline: ReaderPipeline | None = None
        self.pipeline_initialization_error: Exception | None = None

        if self.reader_mode in {
            "llm",
            "auto",
        }:
            try:
                llm_reader = LLMReaderAgent()
                reviewer = ReviewerAgent()
                reflection_agent = ReflectionAgent()

                self.reader_pipeline = ReaderPipeline(
                    reader=llm_reader,
                    reviewer=reviewer,
                    reflection_agent=reflection_agent,
                    max_retries=self.max_reader_retries,
                )

            except Exception as error:
                self.pipeline_initialization_error = error

                if self.reader_mode == "llm":
                    raise RuntimeError(
                        "Failed to initialize ReaderPipeline."
                    ) from error

                print(
                    "ReaderPipeline initialization failed: "
                    f"{error}"
                )

                print(
                    "The workflow will use the "
                    "rule-based reader."
                )

    @staticmethod
    def create_safe_filename(
        title: str,
    ) -> str:
        safe_characters = []

        for character in title:
            if (
                character.isalnum()
                or character in {
                    " ",
                    "_",
                    "-",
                }
            ):
                safe_characters.append(character)

        safe_title = "".join(
            safe_characters
        ).strip()

        safe_title = safe_title.replace(
            " ",
            "_",
        )

        if not safe_title:
            safe_title = "paper"

        return f"{safe_title[:80]}.pdf"

    def analyze_paper(
        self,
        title: str,
        abstract: str,
        extracted_text: str,
    ) -> dict[str, Any]:
        """
        Analyze one paper using the configured reader mode.
        """

        if self.reader_mode == "rule":
            return self._run_rule_reader(
                title=title,
                abstract=abstract,
                extracted_text=extracted_text,
            )

        if self.reader_pipeline is None:
            if self.reader_mode == "llm":
                raise RuntimeError(
                    "ReaderPipeline is unavailable."
                )

            print(
                "ReaderPipeline is unavailable. "
                "Using Rule-Based Reader..."
            )

            return self._run_rule_reader(
                title=title,
                abstract=abstract,
                extracted_text=extracted_text,
            )

        try:
            print(
                "Analyzing paper with ReaderPipeline..."
            )

            pipeline_result = self.reader_pipeline.run(
                title=title,
                abstract=abstract,
                extracted_text=extracted_text,
            )

            final_analysis = pipeline_result.get(
                "final_analysis"
            )

            final_review = pipeline_result.get(
                "final_review"
            )

            if final_analysis is None:
                raise RuntimeError(
                    "ReaderPipeline returned no final analysis."
                )

            if final_review is None:
                raise RuntimeError(
                    "ReaderPipeline returned no final review."
                )

            return {
                "analysis": final_analysis,
                "review": final_review,
                "pipeline_result": pipeline_result,
                "used_fallback": False,
            }

        except Exception as error:
            if self.reader_mode == "llm":
                raise RuntimeError(
                    "ReaderPipeline failed."
                ) from error

            print(
                "ReaderPipeline failed: "
                f"{error}"
            )

            print(
                "Falling back to Rule-Based Reader..."
            )

            fallback_result = self._run_rule_reader(
                title=title,
                abstract=abstract,
                extracted_text=extracted_text,
            )

            fallback_result["pipeline_error"] = str(error)

            return fallback_result

    def _run_rule_reader(
        self,
        title: str,
        abstract: str,
        extracted_text: str,
    ) -> dict[str, Any]:
        print(
            "Analyzing paper with Rule-Based Reader..."
        )

        analysis = self.rule_reader.analyze(
            title=title,
            abstract=abstract,
            extracted_text=extracted_text,
        )

        print(
            "Reviewing Rule-Based Reader analysis..."
        )

        review = self.rule_reviewer.review(
            analysis
        )

        return {
            "analysis": analysis,
            "review": review,
            "pipeline_result": None,
            "used_fallback": (
                self.reader_mode == "auto"
            ),
        }

    def run(
        self,
        topic: str,
        max_results: int = 3,
        max_pages: int = 5,
    ) -> dict[str, Any]:
        """
        Run the complete research workflow.
        """

        if not topic.strip():
            raise ValueError(
                "Research topic cannot be empty."
            )

        if max_results < 1:
            raise ValueError(
                "max_results must be at least 1."
            )

        if max_pages < 1:
            raise ValueError(
                "max_pages must be at least 1."
            )

        print("Creating research plan...")

        plan = self.planner.plan(
            topic
        )

        print("Searching arXiv papers...")

        papers = self.researcher.search_papers(
            research_topic=topic,
            max_results=max_results,
        )

        result: dict[str, Any] = {
            "topic": topic,
            "reader_mode": self.reader_mode,
            "max_reader_retries": (
                self.max_reader_retries
            ),
            "plan": plan,
            "papers": papers,
            "selected_paper": None,
            "pdf_path": None,
            "extracted_text": "",
            "analysis": None,
            "review": None,
            "reader_pipeline": None,
            "used_fallback": False,
        }

        if not papers:
            return result

        selected_paper = papers[0]

        filename = self.create_safe_filename(
            selected_paper["title"]
        )

        print(
            "Downloading paper: "
            f"{selected_paper['title']}"
        )

        pdf_path = download_pdf(
            pdf_url=selected_paper["pdf_url"],
            filename=filename,
        )

        print(
            f"Reading the first {max_pages} pages..."
        )

        extracted_text = extract_text_from_pdf(
            pdf_path=pdf_path,
            max_pages=max_pages,
        )

        paper_result = self.analyze_paper(
            title=selected_paper["title"],
            abstract=selected_paper["summary"],
            extracted_text=extracted_text,
        )

        result["selected_paper"] = selected_paper
        result["pdf_path"] = str(
            Path(pdf_path)
        )
        result["extracted_text"] = extracted_text
        result["analysis"] = paper_result[
            "analysis"
        ]
        result["review"] = paper_result[
            "review"
        ]
        result["reader_pipeline"] = paper_result.get(
            "pipeline_result"
        )
        result["used_fallback"] = paper_result.get(
            "used_fallback",
            False,
        )

        if "pipeline_error" in paper_result:
            result["pipeline_error"] = paper_result[
                "pipeline_error"
            ]

        return result