from workflow.research_workflow import ResearchWorkflow


DEFAULT_TOPIC = (
    '(ti:"vision language" OR abs:"vision language") '
    "AND "
    "(ti:robot OR abs:robot "
    "OR ti:navigation OR abs:navigation)"
)


def print_research_plan(plan: object) -> None:
    print("\nResearch Plan:")
    print(plan)


def print_papers(papers: list[dict]) -> None:
    print("\nFound Papers:")

    if not papers:
        print("No papers were found.")
        return

    for index, paper in enumerate(
        papers,
        start=1,
    ):
        print(f"\n{index}. {paper['title']}")
        print(f"Published: {paper['published']}")
        print(
            "Authors: "
            f"{', '.join(paper['authors'])}"
        )
        print(f"PDF: {paper['pdf_url']}")


def print_analysis(analysis: dict | None) -> None:
    if analysis is None:
        print("\nNo paper analysis was generated.")
        return

    print("\nPaper Analysis:")

    print(
        "Reader Model: "
        f"{analysis['model_name']}"
    )

    print(
        "Elapsed Time: "
        f"{analysis['elapsed_seconds']:.3f} seconds"
    )

    print(
        "Input Tokens: "
        f"{analysis['input_tokens']}"
    )

    print(
        "Output Tokens: "
        f"{analysis['output_tokens']}"
    )

    print(
        "Estimated Cost: "
        f"${analysis['estimated_cost_usd']:.6f}"
    )

    print("\nResearch Problem:")
    print(analysis["research_problem"])

    print("\nMethodology:")
    print(analysis["methodology"])

    print("\nDatasets and Environments:")
    print(analysis["datasets"])

    print("\nMain Contributions:")

    for contribution in analysis[
        "main_contributions"
    ]:
        print(f"* {contribution}")

    print("\nLimitations:")
    print(analysis["limitations"])


def print_review(review: dict | None) -> None:
    if review is None:
        print("\nNo review result was generated.")
        return

    print("\nReview Result:")
    print(f"Approved: {review['approved']}")
    print(f"Score: {review['score']:.2f}")
    print(f"Feedback: {review['feedback']}")

    issues = review.get("issues", [])

    if issues:
        print("\nDetected Issues:")

        for issue in issues:
            print(f"* {issue}")


def main() -> None:
    print("AutoResearch Agent")
    print("==================")

    print(
        "\nEnter an arXiv research query."
    )

    print(
        "Press Enter to use the default "
        "vision-language robot navigation query."
    )

    user_topic = input("\nResearch topic:\n> ").strip()

    topic = user_topic or DEFAULT_TOPIC

    workflow = ResearchWorkflow(
        reader_mode="auto",
    )

    result = workflow.run(
        topic=topic,
        max_results=3,
        max_pages=5,
    )

    print_research_plan(
        result["plan"]
    )

    print_papers(
        result["papers"]
    )

    selected_paper = result[
        "selected_paper"
    ]

    if selected_paper is None:
        return

    print("\nSelected Paper:")
    print(selected_paper["title"])

    print("\nSaved PDF:")
    print(result["pdf_path"])

    print_analysis(
        result["analysis"]
    )

    print_review(
        result["review"]
    )


if __name__ == "__main__":
    main()