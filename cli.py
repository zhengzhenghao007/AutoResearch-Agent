from typing import Any


SEPARATOR = "=" * 50


def get_value(
    data: Any,
    key: str,
    default: Any = None,
) -> Any:
    """
    Read a value from either a dictionary or an object.

    This allows the CLI to display normal dictionaries,
    dataclasses, and Pydantic models.
    """
    if data is None:
        return default

    if isinstance(data, dict):
        return data.get(key, default)

    return getattr(data, key, default)


def print_header() -> None:
    """
    Display the application header.
    """
    print()
    print(SEPARATOR)
    print("AutoResearch Agent")
    print(SEPARATOR)
    print()


def prompt_research_topic(
    default_topic: str,
) -> str:
    """
    Ask the user for a research topic.

    Pressing Enter uses the supplied default query.
    """
    print("Enter an arXiv research query.")
    print("Press Enter to use the default query.")
    print()
    print("Research topic:")

    topic = input("> ").strip()

    if topic:
        return topic

    print()
    print("Using the default research query.")

    return default_topic


def print_research_plan(
    plan: Any,
) -> None:
    """
    Display a research plan in a readable format.
    """
    print()
    print(SEPARATOR)
    print("Research Plan")
    print(SEPARATOR)

    if plan is None:
        print("No research plan was generated.")
        return

    if isinstance(plan, str):
        print(plan)
        return

    if isinstance(plan, dict):
        research_topic = plan.get(
            "research_topic"
        )
        steps = plan.get(
            "research_plan"
        )

        if research_topic:
            print()
            print("Research Topic:")
            print(research_topic)

        if steps:
            print()
            print("Plan:")

            if isinstance(steps, list):
                for index, step in enumerate(
                    steps,
                    start=1,
                ):
                    print(f"{index}. {step}")
            else:
                print(steps)

        remaining_items = {
            key: value
            for key, value in plan.items()
            if key
            not in {
                "research_topic",
                "research_plan",
            }
        }

        for key, value in remaining_items.items():
            readable_key = key.replace(
                "_",
                " ",
            ).title()

            print()
            print(f"{readable_key}:")
            print(value)

        return

    print(plan)


def format_authors(
    authors: Any,
) -> str:
    """
    Convert an authors field into display text.
    """
    if not authors:
        return "Unknown"

    if isinstance(authors, str):
        return authors

    if isinstance(authors, list):
        formatted_authors = []

        for author in authors:
            if isinstance(author, str):
                formatted_authors.append(author)
                continue

            author_name = get_value(
                author,
                "name",
            )

            if author_name:
                formatted_authors.append(
                    str(author_name)
                )
            else:
                formatted_authors.append(
                    str(author)
                )

        return ", ".join(formatted_authors)

    return str(authors)


def print_papers(
    papers: list[Any],
) -> None:
    """
    Display all papers returned by the search.
    """
    print()
    print(SEPARATOR)
    print(f"Found {len(papers)} Papers")
    print(SEPARATOR)

    if not papers:
        print()
        print("No papers were found.")
        return

    for index, paper in enumerate(
        papers,
        start=1,
    ):
        title = get_value(
            paper,
            "title",
            "Untitled paper",
        )
        published = get_value(
            paper,
            "published",
            "Unknown",
        )
        authors = format_authors(
            get_value(
                paper,
                "authors",
                [],
            )
        )
        pdf_url = get_value(
            paper,
            "pdf_url",
            "Unavailable",
        )

        print()
        print(f"{index}. {title}")
        print(f"   Published: {published}")
        print(f"   Authors: {authors}")
        print(f"   PDF: {pdf_url}")


def select_paper(
    papers: list[Any],
) -> int:
    """
    Ask the user to select one paper.

    Returns a zero-based index for use by the workflow.
    """
    if not papers:
        raise ValueError(
            "Cannot select a paper from an empty list."
        )

    minimum_choice = 1
    maximum_choice = len(papers)

    while True:
        print()
        print(
            "Select a paper to analyze "
            f"[{minimum_choice}-{maximum_choice}]:"
        )

        raw_choice = input("> ").strip()

        if not raw_choice:
            print(
                "Please enter a paper number."
            )
            continue

        try:
            selected_number = int(
                raw_choice
            )
        except ValueError:
            print(
                "Invalid input. Please enter a number."
            )
            continue

        if selected_number < minimum_choice:
            print(
                "Selection is out of range. "
                f"Choose a number from "
                f"{minimum_choice} to {maximum_choice}."
            )
            continue

        if selected_number > maximum_choice:
            print(
                "Selection is out of range. "
                f"Choose a number from "
                f"{minimum_choice} to {maximum_choice}."
            )
            continue

        return selected_number - 1


def print_selected_paper(
    paper: Any,
) -> None:
    """
    Display the paper selected by the user.
    """
    title = get_value(
        paper,
        "title",
        "Untitled paper",
    )
    published = get_value(
        paper,
        "published",
        "Unknown",
    )
    authors = format_authors(
        get_value(
            paper,
            "authors",
            [],
        )
    )

    print()
    print(SEPARATOR)
    print("Selected Paper")
    print(SEPARATOR)
    print()
    print(title)
    print(f"Published: {published}")
    print(f"Authors: {authors}")


def print_list_items(
    title: str,
    value: Any,
) -> None:
    """
    Display either a list or a scalar value.
    """
    print()
    print(f"{title}:")

    if value is None:
        print("Not available")
        return

    if isinstance(value, list):
        if not value:
            print("Not available")
            return

        for item in value:
            print(f"* {item}")

        return

    print(value)


def print_analysis(
    analysis: Any,
) -> None:
    """
    Display the final paper analysis.
    """
    print()
    print(SEPARATOR)
    print("Paper Analysis")
    print(SEPARATOR)

    if analysis is None:
        print()
        print("No analysis was generated.")
        return

    model_name = get_value(
        analysis,
        "model_name",
    )
    elapsed_seconds = get_value(
        analysis,
        "elapsed_seconds",
    )
    estimated_cost = get_value(
        analysis,
        "estimated_cost_usd",
    )

    if model_name is not None:
        print()
        print(f"Reader: {model_name}")

    if elapsed_seconds is not None:
        try:
            print(
                "Elapsed Time: "
                f"{float(elapsed_seconds):.6f} seconds"
            )
        except (TypeError, ValueError):
            print(
                f"Elapsed Time: {elapsed_seconds}"
            )

    if estimated_cost is not None:
        try:
            print(
                "Estimated Cost: "
                f"${float(estimated_cost):.6f}"
            )
        except (TypeError, ValueError):
            print(
                f"Estimated Cost: {estimated_cost}"
            )

    print_list_items(
        "Research Problem",
        get_value(
            analysis,
            "research_problem",
        ),
    )
    print_list_items(
        "Methodology",
        get_value(
            analysis,
            "methodology",
        ),
    )
    print_list_items(
        "Datasets",
        get_value(
            analysis,
            "datasets",
        ),
    )
    print_list_items(
        "Main Contributions",
        get_value(
            analysis,
            "main_contributions",
        ),
    )
    print_list_items(
        "Limitations",
        get_value(
            analysis,
            "limitations",
        ),
    )


def print_review(
    review: Any,
) -> None:
    """
    Display the reviewer result.
    """
    print()
    print(SEPARATOR)
    print("Review Result")
    print(SEPARATOR)

    if review is None:
        print()
        print("No review was generated.")
        return

    approved = get_value(
        review,
        "approved",
    )
    score = get_value(
        review,
        "score",
    )
    feedback = get_value(
        review,
        "feedback",
    )
    issues = get_value(
        review,
        "issues",
        [],
    )

    print()

    if approved is not None:
        print(f"Approved: {approved}")

    if score is not None:
        try:
            print(
                f"Score: {float(score):.2f}"
            )
        except (TypeError, ValueError):
            print(f"Score: {score}")

    if feedback:
        print(f"Feedback: {feedback}")

    if issues:
        print()
        print("Detected Issues:")

        if isinstance(issues, list):
            for issue in issues:
                print(f"* {issue}")
        else:
            print(issues)


def print_result(
    result: dict[str, Any],
) -> None:
    """
    Display the complete workflow result.
    """
    selected_paper = result.get(
        "selected_paper"
    )

    if selected_paper is not None:
        print_selected_paper(
            selected_paper
        )

    pdf_path = result.get(
        "pdf_path"
    )

    if pdf_path:
        print()
        print("Saved PDF:")
        print(pdf_path)

    used_fallback = result.get(
        "used_fallback",
        False,
    )

    if used_fallback:
        print()
        print(
            "ReaderPipeline fallback was used."
        )

    pipeline_error = result.get(
        "pipeline_error"
    )

    if pipeline_error:
        print()
        print("ReaderPipeline Error:")
        print(pipeline_error)

    print_analysis(
        result.get(
            "analysis"
        )
    )
    print_review(
        result.get(
            "review"
        )
    )

    print()
    print(SEPARATOR)
    print("Analysis Complete")
    print(SEPARATOR)
    print()