from tools.arxiv_search import search_arxiv


class ResearcherAgent:
    def search_papers(
        self,
        research_topic: str,
        max_results: int = 5
    ) -> list[dict]:
        return search_arxiv(
            query=research_topic,
            max_results=max_results
        )