from pathlib import Path

from agents.llm_reader import LLMReaderAgent
from agents.planner import PlannerAgent
from agents.reader import ReaderAgent
from agents.researcher import ResearcherAgent
from agents.reviewer import ReviewerAgent
from tools.pdf_reader import download_pdf, extract_text_from_pdf


class ResearchWorkflow:
    """
    Coordinate the complete academic research pipeline.

    Reader modes:
        rule:
            Always use the rule-based ReaderAgent.

        llm:
            Always use the LLMReaderAgent.
            An LLM error will stop the workflow.

        auto:
            Try the LLM reader first.
            Fall back to the rule-based reader if the LLM fails.
    """

    VALID_READER_MODES = {"rule", "llm", "auto"}

    def __init__(
        self,
        reader_mode: str = "auto",
    ) -> None:
        if reader_mode not in self.VALID_READER_MODES:
            valid_modes = ", ".join(
                sorted(self.VALID_READER_MODES)
            )

            raise ValueError(
                f"Invalid reader mode: {reader_mode}. "
                f"Valid modes are: {valid_modes}."
            )

        self.reader_mode = reader_mode

        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.rule_reader = ReaderAgent()
        self.reviewer = ReviewerAgent()

        self.llm_reader = None

        if self.reader_mode in {"llm", "auto"}:
            try:
                self.llm_reader = LLMReaderAgent()

            except Exception as error:
                if self.reader_mode == "llm":
                    raise RuntimeError(
                        "Failed to initialize the LLM reader."
                    ) from error

                print(
                    "LLM Reader initialization failed: "
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
                or character in {" ", "_", "-"}
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
    ) -> dict:
        """
        Analyze one paper using the configured reader mode.
        """

        if self.reader_mode == "rule":
            print("Analyzing paper with Rule-Based Reader...")

            return self.rule_reader.analyze(
                title=title,
                abstract=abstract,
                extracted_text=extracted_text,
            )

        if self.reader_mode == "llm":
            if self.llm_reader is None:
                raise RuntimeError(
                    "LLM Reader is not available."
                )

            print("Analyzing paper with LLM Reader...")

            return self.llm_reader.analyze(
                title=title,
                abstract=abstract,
                extracted_text=extracted_text,
            )

        if self.llm_reader is not None:
            try:
                print("Analyzing paper with LLM Reader...")

                return self.llm_reader.analyze(
                    title=title,
                    abstract=abstract,
                    extracted_text=extracted_text,
                )

            except Exception as error:
                print(
                    "LLM Reader failed: "
                    f"{error}"
                )
                print(
                    "Falling back to Rule-Based Reader..."
                )

        return self.rule_reader.analyze(
            title=title,
            abstract=abstract,
            extracted_text=extracted_text,
        )

    def run(
        self,
        topic: str,
        max_results: int = 3,
        max_pages: int = 5,
    ) -> dict:
        print("Creating research plan...")

        plan = self.planner.plan(topic)

        print("Searching arXiv papers...")

        papers = self.researcher.search_papers(
            research_topic=topic,
            max_results=max_results,
        )

        result = {
            "topic": topic,
            "reader_mode": self.reader_mode,
            "plan": plan,
            "papers": papers,
            "selected_paper": None,
            "pdf_path": None,
            "extracted_text": "",
            "analysis": None,
            "review": None,
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

        analysis = self.analyze_paper(
            title=selected_paper["title"],
            abstract=selected_paper["summary"],
            extracted_text=extracted_text,
        )

        print("Reviewing analysis...")

        review = self.reviewer.review(
            analysis
        )

        result["selected_paper"] = selected_paper
        result["pdf_path"] = str(
            Path(pdf_path)
        )
        result["extracted_text"] = extracted_text
        result["analysis"] = analysis
        result["review"] = review

        return result