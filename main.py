from workflow.research_workflow import ResearchWorkflow


def main() -> None:
    topic = (
    '(ti:"vision language" OR abs:"vision language") '
    'AND (ti:robot OR abs:robot OR ti:navigation OR abs:navigation)'
    )

    workflow = ResearchWorkflow()

    result = workflow.run(
        topic=topic,
        max_results=3,
        max_pages=5,
    )

    print("\nResearch Plan:")
    print(result["plan"])

    print("\nFound Papers:")

    for index, paper in enumerate(result["papers"], start=1):
        print(f"\n{index}. {paper['title']}")
        print(f"Published: {paper['published']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"PDF: {paper['pdf_url']}")

    if result["selected_paper"] is None:
        print("\nNo papers were found.")
        return

    print("\nSelected Paper:")
    print(result["selected_paper"]["title"])

    print("\nSaved PDF:")
    print(result["pdf_path"])

    print("\nExtracted Text Preview:")
    print(result["extracted_text"][:3000])


if __name__ == "__main__":
    main()