from pathlib import Path

from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from tools.pdf_reader import download_pdf, extract_text_from_pdf


class ResearchWorkflow:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()

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

        result["selected_paper"] = selected_paper
        result["pdf_path"] = str(Path(pdf_path))
        result["extracted_text"] = extracted_text

        return result