from typing import Final

from cli import (
    print_header,
    print_papers,
    print_research_plan,
    print_result,
    prompt_research_topic,
    select_paper,
)
from workflow.research_workflow import ResearchWorkflow


DEFAULT_TOPIC: Final[str] = (
    '(ti:"vision language" OR abs:"vision language") '
    "AND "
    "(ti:robot OR abs:robot "
    "OR ti:navigation OR abs:navigation)"
)

MAX_RESULTS: Final[int] = 5
MAX_PAGES: Final[int] = 5
READER_MODE: Final[str] = "auto"
MAX_READER_RETRIES: Final[int] = 2


def run_application() -> None:
    """
    Run the interactive research workflow.
    """
    print_header()

    topic = prompt_research_topic(
        default_topic=DEFAULT_TOPIC,
    )

    workflow = ResearchWorkflow(
        reader_mode=READER_MODE,
        max_reader_retries=MAX_READER_RETRIES,
    )

    search_result = workflow.search(
        topic=topic,
        max_results=MAX_RESULTS,
    )

    plan = search_result["plan"]
    papers = search_result["papers"]

    print_research_plan(
        plan
    )
    print_papers(
        papers
    )

    if not papers:
        print()
        print(
            "No papers were found for this query."
        )
        return

    selected_index = select_paper(
        papers
    )

    selected_title = papers[
        selected_index
    ].get(
        "title",
        "Untitled paper",
    )

    print()
    print(
        f"Selected: {selected_title}"
    )
    print()
    print("Starting paper analysis...")

    result = workflow.analyze_selected_paper(
        topic=search_result["topic"],
        plan=plan,
        papers=papers,
        selected_index=selected_index,
        max_pages=MAX_PAGES,
    )

    print_result(
        result
    )


def main() -> None:
    """
    Application entry point.
    """
    try:
        run_application()

    except KeyboardInterrupt:
        print()
        print()
        print(
            "Operation cancelled by the user."
        )

    except EOFError:
        print()
        print()
        print(
            "Input stream was closed."
        )

    except ValueError as error:
        print()
        print()
        print(
            f"Invalid input: {error}"
        )

    except IndexError as error:
        print()
        print()
        print(
            f"Paper selection error: {error}"
        )

    except FileNotFoundError as error:
        print()
        print()
        print(
            f"File error: {error}"
        )

    except ConnectionError as error:
        print()
        print()
        print(
            f"Network error: {error}"
        )

    except Exception as error:
        print()
        print()
        print(
            "The research workflow failed."
        )
        print(
            f"Error type: "
            f"{type(error).__name__}"
        )
        print(
            f"Details: {error}"
        )


if __name__ == "__main__":
    main()