from pathlib import Path

from agents.planner import PlannerAgent
from agents.reader import ReaderAgent
from agents.researcher import ResearcherAgent
from tools.pdf_reader import download_pdf, extract_text_from_pdf


class ResearchWorkflow:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.reader = ReaderAgent()

    @staticmethod
    def create_safe_filename(title: str) -> str:
        safe_characters = []

        for character in title:
            if character.isalnum() or character in {" ", "_", "-"}:
                safe_characters.append(character)

        safe_title = "".join(safe_characters).strip()
        safe_title = safe_title.replace(" ", "_")

        if not safe_title:
            safe_title = "paper"

        return f"{safe_title[:80]}.pdf"

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
            "plan": plan,
            "papers": papers,
            "selected_paper": None,
            "pdf_path": None,
            "extracted_text": "",
            "analysis": None,
        }

        if not papers:
            return result

        selected_paper = papers[0]
        filename = self.create_safe_filename(selected_paper["title"])

        print(f"Downloading paper: {selected_paper['title']}")

        pdf_path = download_pdf(
            pdf_url=selected_paper["pdf_url"],
            filename=filename,
        )

        print(f"Reading the first {max_pages} pages...")

        extracted_text = extract_text_from_pdf(
            pdf_path=pdf_path,
            max_pages=max_pages,
        )

        print("Analyzing paper...")

        analysis = self.reader.analyze(
            title=selected_paper["title"],
            abstract=selected_paper["summary"],
            extracted_text=extracted_text,
        )

        result["selected_paper"] = selected_paper
        result["pdf_path"] = str(Path(pdf_path))
        result["extracted_text"] = extracted_text
        result["analysis"] = analysis

        return result