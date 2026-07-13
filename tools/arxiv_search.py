import arxiv


def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=3,
        num_retries=3,
    )

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []

    for result in client.results(search):
        papers.append(
            {
                "title": result.title.strip(),
                "authors": [author.name for author in result.authors],
                "published": result.published.strftime("%Y-%m-%d"),
                "summary": result.summary.replace("\n", " ").strip(),
                "pdf_url": result.pdf_url,
                "entry_id": result.entry_id,
                "categories": result.categories,
            }
        )

    return papers