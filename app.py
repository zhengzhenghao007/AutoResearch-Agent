from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from tools.pdf_reader import extract_text_from_pdf
from workflow.research_workflow import ResearchWorkflow


DEFAULT_TOPIC = (
    '(ti:"vision language" OR abs:"vision language") '
    "AND "
    "(ti:robot OR abs:robot "
    "OR ti:navigation OR abs:navigation)"
)

MAX_RESULTS = 5
DEFAULT_MAX_PAGES = 5


st.set_page_config(
    page_title="AutoResearch Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(74, 93, 255, 0.10),
                    transparent 32%
                ),
                linear-gradient(
                    180deg,
                    #0b1020 0%,
                    #10172a 100%
                );
        }

        [data-testid="stSidebar"] {
            background: rgba(11, 16, 32, 0.96);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        .main-title {
            font-size: 2.7rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.3rem;
            background: linear-gradient(
                90deg,
                #8ea2ff,
                #7de2d1
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 1.05rem;
            color: #aeb8d0;
            margin-bottom: 2rem;
        }

        .paper-card {
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.10);
            background: rgba(24, 34, 58, 0.72);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.16);
        }

        .paper-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #f4f7ff;
            margin-bottom: 0.65rem;
        }

        .paper-meta {
            color: #aeb8d0;
            font-size: 0.9rem;
            margin-bottom: 0.3rem;
        }

        .paper-summary {
            color: #d7ddec;
            font-size: 0.94rem;
            line-height: 1.55;
            margin-top: 0.8rem;
        }

        .result-box {
            padding: 1.15rem;
            margin-bottom: 1rem;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.09);
            background: rgba(20, 29, 50, 0.76);
        }

        .result-heading {
            font-size: 1rem;
            font-weight: 700;
            color: #91e5d4;
            margin-bottom: 0.5rem;
        }

        .small-muted {
            color: #99a6c1;
            font-size: 0.88rem;
        }

        div[data-testid="stMetric"] {
            padding: 1rem;
            border-radius: 14px;
            background: rgba(20, 29, 50, 0.76);
            border: 1px solid rgba(255, 255, 255, 0.09);
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 650;
        }

        .stDownloadButton > button {
            border-radius: 10px;
            font-weight: 650;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_value(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:
    if value is None:
        return default

    if isinstance(value, dict):
        return value.get(key, default)

    return getattr(value, key, default)


def serialize_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            str(key): serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, Path):
        return str(value)

    if hasattr(value, "model_dump"):
        return serialize_value(
            value.model_dump()
        )

    if hasattr(value, "dict"):
        return serialize_value(
            value.dict()
        )

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    return str(value)


def format_authors(authors: Any) -> str:
    if not authors:
        return "Unknown"

    if isinstance(authors, str):
        return authors

    if isinstance(authors, list):
        names = []

        for author in authors:
            if isinstance(author, str):
                names.append(author)
                continue

            name = get_value(
                author,
                "name",
            )

            if name:
                names.append(str(name))
            else:
                names.append(str(author))

        return ", ".join(names)

    return str(authors)


def truncate_text(
    text: str,
    limit: int = 500,
) -> str:
    cleaned = " ".join(
        str(text).split()
    )

    if len(cleaned) <= limit:
        return cleaned

    return cleaned[:limit].rstrip() + "..."


def initialize_state() -> None:
    defaults = {
        "search_result": None,
        "analysis_result": None,
        "selected_index": 0,
        "current_source": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def get_workflow(
    reader_mode: str,
    max_reader_retries: int,
) -> ResearchWorkflow:
    return ResearchWorkflow(
        reader_mode=reader_mode,
        max_reader_retries=max_reader_retries,
    )


def render_header() -> None:
    st.markdown(
        '<div class="main-title">'
        "AutoResearch Agent"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Search, upload, read and review academic papers "
        "with a multi-agent research workflow."
        "</div>",
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, int, int]:
    with st.sidebar:
        st.title("Settings")

        reader_mode = st.selectbox(
            "Reader mode",
            options=[
                "auto",
                "llm",
                "rule",
            ],
            index=0,
            help=(
                "Auto uses the LLM pipeline first and "
                "falls back to the rule-based reader."
            ),
        )

        max_pages = st.slider(
            "Pages to read",
            min_value=1,
            max_value=20,
            value=DEFAULT_MAX_PAGES,
        )

        max_reader_retries = st.slider(
            "Reader retries",
            min_value=0,
            max_value=5,
            value=2,
        )

        st.divider()

        st.caption(
            "The first version processes one paper at a time. "
            "Multi-paper synthesis can be added next."
        )

    return (
        reader_mode,
        max_pages,
        max_reader_retries,
    )


def render_plan(plan: Any) -> None:
    if plan is None:
        return

    with st.expander(
        "View research plan",
        expanded=False,
    ):
        if isinstance(plan, str):
            st.write(plan)
            return

        serialized = serialize_value(plan)

        if isinstance(serialized, dict):
            topic = serialized.get(
                "research_topic"
            )
            steps = serialized.get(
                "research_plan"
            )

            if topic:
                st.markdown("#### Research topic")
                st.write(topic)

            if steps:
                st.markdown("#### Research plan")

                if isinstance(steps, list):
                    for index, step in enumerate(
                        steps,
                        start=1,
                    ):
                        st.write(
                            f"{index}. {step}"
                        )
                else:
                    st.write(steps)

            remaining = {
                key: value
                for key, value in serialized.items()
                if key
                not in {
                    "research_topic",
                    "research_plan",
                }
            }

            if remaining:
                st.json(remaining)

            return

        st.write(serialized)


def render_paper_card(
    paper: dict[str, Any],
    index: int,
) -> None:
    title = paper.get(
        "title",
        "Untitled paper",
    )
    authors = format_authors(
        paper.get("authors")
    )
    published = paper.get(
        "published",
        "Unknown",
    )
    summary = paper.get(
        "summary",
        "No abstract available.",
    )
    pdf_url = paper.get(
        "pdf_url",
        "",
    )

    st.markdown(
        f"""
        <div class="paper-card">
            <div class="paper-title">
                {index + 1}. {title}
            </div>
            <div class="paper-meta">
                <strong>Published:</strong> {published}
            </div>
            <div class="paper-meta">
                <strong>Authors:</strong> {authors}
            </div>
            <div class="paper-summary">
                {truncate_text(summary)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if pdf_url:
        st.link_button(
            "Open arXiv PDF",
            pdf_url,
            use_container_width=True,
        )


def render_search_tab(
    workflow: ResearchWorkflow,
    max_pages: int,
) -> None:
    st.subheader("Search academic papers")

    topic = st.text_area(
        "Research topic or arXiv query",
        value=DEFAULT_TOPIC,
        height=110,
        placeholder=(
            "Example: vision language robot navigation"
        ),
    )

    search_clicked = st.button(
        "Search papers",
        type="primary",
        use_container_width=True,
    )

    if search_clicked:
        cleaned_topic = topic.strip()

        if not cleaned_topic:
            st.warning(
                "Please enter a research topic."
            )
        else:
            try:
                with st.status(
                    "Searching papers...",
                    expanded=True,
                ) as status:
                    st.write(
                        "Creating research plan"
                    )
                    st.write(
                        "Searching arXiv"
                    )

                    search_result = workflow.search(
                        topic=cleaned_topic,
                        max_results=MAX_RESULTS,
                    )

                    st.session_state.search_result = (
                        search_result
                    )
                    st.session_state.analysis_result = (
                        None
                    )
                    st.session_state.selected_index = 0
                    st.session_state.current_source = (
                        "search"
                    )

                    status.update(
                        label="Search complete",
                        state="complete",
                        expanded=False,
                    )

            except Exception as error:
                st.error(
                    "Paper search failed."
                )
                st.exception(error)

    search_result = st.session_state.search_result

    if not search_result:
        return

    papers = search_result.get(
        "papers",
        [],
    )

    render_plan(
        search_result.get("plan")
    )

    if not papers:
        st.info(
            "No papers were found for this query."
        )
        return

    st.markdown(
        f"### Found {len(papers)} papers"
    )

    paper_options = [
        paper.get(
            "title",
            f"Paper {index + 1}",
        )
        for index, paper in enumerate(papers)
    ]

    selected_title = st.selectbox(
        "Select a paper to analyze",
        options=paper_options,
        index=min(
            st.session_state.selected_index,
            len(paper_options) - 1,
        ),
    )

    selected_index = paper_options.index(
        selected_title
    )
    st.session_state.selected_index = (
        selected_index
    )

    selected_paper = papers[
        selected_index
    ]

    left_column, right_column = st.columns(
        [3, 1]
    )

    with left_column:
        render_paper_card(
            selected_paper,
            selected_index,
        )

    with right_column:
        st.metric(
            "Selected paper",
            f"{selected_index + 1} of {len(papers)}",
        )

        analyze_clicked = st.button(
            "Analyze selected paper",
            type="primary",
            use_container_width=True,
        )

    with st.expander(
        "Browse all search results",
        expanded=False,
    ):
        for index, paper in enumerate(papers):
            render_paper_card(
                paper,
                index,
            )

    if analyze_clicked:
        try:
            with st.status(
                "Analyzing selected paper...",
                expanded=True,
            ) as status:
                st.write(
                    "Downloading PDF"
                )
                st.write(
                    f"Reading the first {max_pages} pages"
                )
                st.write(
                    "Running ReaderPipeline"
                )
                st.write(
                    "Reviewing analysis"
                )

                result = (
                    workflow.analyze_selected_paper(
                        topic=search_result["topic"],
                        plan=search_result["plan"],
                        papers=papers,
                        selected_index=selected_index,
                        max_pages=max_pages,
                    )
                )

                st.session_state.analysis_result = (
                    result
                )
                st.session_state.current_source = (
                    "search"
                )

                status.update(
                    label="Analysis complete",
                    state="complete",
                    expanded=False,
                )

        except Exception as error:
            st.error(
                "Paper analysis failed."
            )
            st.exception(error)


def render_upload_tab(
    workflow: ResearchWorkflow,
    max_pages: int,
) -> None:
    st.subheader("Upload a PDF")

    uploaded_file = st.file_uploader(
        "Choose an academic paper",
        type=["pdf"],
        accept_multiple_files=False,
        help="Upload one PDF file for structured analysis.",
    )

    title = st.text_input(
        "Paper title",
        value=(
            Path(uploaded_file.name).stem
            if uploaded_file
            else ""
        ),
        placeholder="Enter the paper title",
    )

    abstract = st.text_area(
        "Abstract",
        value="",
        height=140,
        placeholder=(
            "Optional. Paste the abstract to improve analysis."
        ),
    )

    if uploaded_file is not None:
        st.success(
            f"Loaded {uploaded_file.name}"
        )

        st.caption(
            f"File size: "
            f"{uploaded_file.size / 1024:.1f} KB"
        )

    analyze_upload_clicked = st.button(
        "Analyze uploaded PDF",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )

    if not analyze_upload_clicked:
        return

    if uploaded_file is None:
        st.warning(
            "Please upload a PDF file."
        )
        return

    cleaned_title = title.strip()

    if not cleaned_title:
        cleaned_title = Path(
            uploaded_file.name
        ).stem

    temporary_path: Path | None = None

    try:
        with st.status(
            "Analyzing uploaded PDF...",
            expanded=True,
        ) as status:
            st.write(
                "Saving uploaded file"
            )

            with tempfile.NamedTemporaryFile(
                suffix=".pdf",
                delete=False,
            ) as temporary_file:
                temporary_file.write(
                    uploaded_file.getbuffer()
                )
                temporary_path = Path(
                    temporary_file.name
                )

            st.write(
                f"Extracting the first {max_pages} pages"
            )

            extracted_text = extract_text_from_pdf(
                pdf_path=temporary_path,
                max_pages=max_pages,
            )

            if not extracted_text.strip():
                raise ValueError(
                    "No readable text was extracted "
                    "from the uploaded PDF."
                )

            st.write(
                "Running ReaderPipeline"
            )

            paper_result = workflow.analyze_paper(
                title=cleaned_title,
                abstract=abstract.strip(),
                extracted_text=extracted_text,
            )

            result = {
                "topic": cleaned_title,
                "plan": None,
                "papers": [],
                "selected_index": None,
                "selected_paper": {
                    "title": cleaned_title,
                    "authors": [],
                    "published": "Uploaded file",
                    "summary": abstract.strip(),
                    "pdf_url": None,
                },
                "pdf_path": uploaded_file.name,
                "extracted_text": extracted_text,
                "analysis": paper_result.get(
                    "analysis"
                ),
                "review": paper_result.get(
                    "review"
                ),
                "reader_pipeline": paper_result.get(
                    "pipeline_result"
                ),
                "used_fallback": paper_result.get(
                    "used_fallback",
                    False,
                ),
            }

            if "pipeline_error" in paper_result:
                result["pipeline_error"] = (
                    paper_result["pipeline_error"]
                )

            st.session_state.analysis_result = (
                result
            )
            st.session_state.current_source = (
                "upload"
            )

            status.update(
                label="Analysis complete",
                state="complete",
                expanded=False,
            )

    except Exception as error:
        st.error(
            "Uploaded PDF analysis failed."
        )
        st.exception(error)

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink(
                missing_ok=True
            )


def render_field(
    title: str,
    value: Any,
) -> None:
    serialized = serialize_value(value)

    if serialized in (
        None,
        "",
        [],
        {},
    ):
        serialized = "Not available"

    st.markdown(
        '<div class="result-box">'
        f'<div class="result-heading">{title}</div>',
        unsafe_allow_html=True,
    )

    if isinstance(serialized, list):
        for item in serialized:
            st.markdown(
                f"* {item}"
            )
    elif isinstance(serialized, dict):
        st.json(serialized)
    else:
        st.write(serialized)

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def create_markdown_report(
    result: dict[str, Any],
) -> str:
    paper = result.get(
        "selected_paper",
        {}
    )
    analysis = result.get(
        "analysis"
    )
    review = result.get(
        "review"
    )

    title = get_value(
        paper,
        "title",
        "Paper Analysis",
    )

    sections = [
        f"# {title}",
        "",
        "## Research Problem",
        str(
            get_value(
                analysis,
                "research_problem",
                "Not available",
            )
        ),
        "",
        "## Methodology",
        str(
            get_value(
                analysis,
                "methodology",
                "Not available",
            )
        ),
        "",
        "## Datasets",
    ]

    datasets = get_value(
        analysis,
        "datasets",
        [],
    )

    if isinstance(datasets, list):
        sections.extend(
            f"* {dataset}"
            for dataset in datasets
        )
    else:
        sections.append(str(datasets))

    sections.extend(
        [
            "",
            "## Main Contributions",
        ]
    )

    contributions = get_value(
        analysis,
        "main_contributions",
        [],
    )

    if isinstance(contributions, list):
        sections.extend(
            f"* {item}"
            for item in contributions
        )
    else:
        sections.append(
            str(contributions)
        )

    sections.extend(
        [
            "",
            "## Limitations",
        ]
    )

    limitations = get_value(
        analysis,
        "limitations",
        [],
    )

    if isinstance(limitations, list):
        sections.extend(
            f"* {item}"
            for item in limitations
        )
    else:
        sections.append(
            str(limitations)
        )

    sections.extend(
        [
            "",
            "## Review",
            f"* Approved: "
            f"{get_value(review, 'approved', 'Unknown')}",
            f"* Score: "
            f"{get_value(review, 'score', 'Unknown')}",
            f"* Feedback: "
            f"{get_value(review, 'feedback', 'Not available')}",
        ]
    )

    return "\n".join(sections)


def render_result() -> None:
    result = st.session_state.analysis_result

    if not result:
        return

    st.divider()
    st.header("Analysis result")

    selected_paper = result.get(
        "selected_paper",
        {}
    )

    title = get_value(
        selected_paper,
        "title",
        "Untitled paper",
    )

    st.subheader(title)

    analysis = result.get(
        "analysis"
    )
    review = result.get(
        "review"
    )

    metric_columns = st.columns(4)

    with metric_columns[0]:
        approved = get_value(
            review,
            "approved",
            "Unknown",
        )
        st.metric(
            "Approved",
            str(approved),
        )

    with metric_columns[1]:
        score = get_value(
            review,
            "score",
            "Unknown",
        )
        st.metric(
            "Review score",
            str(score),
        )

    with metric_columns[2]:
        model_name = get_value(
            analysis,
            "model_name",
            "Unknown",
        )
        st.metric(
            "Reader model",
            str(model_name),
        )

    with metric_columns[3]:
        elapsed = get_value(
            analysis,
            "elapsed_seconds",
            "Unknown",
        )

        if isinstance(
            elapsed,
            (float, int),
        ):
            elapsed_text = f"{elapsed:.2f}s"
        else:
            elapsed_text = str(elapsed)

        st.metric(
            "Elapsed time",
            elapsed_text,
        )

    left_column, right_column = st.columns(2)

    with left_column:
        render_field(
            "Research Problem",
            get_value(
                analysis,
                "research_problem",
            ),
        )
        render_field(
            "Methodology",
            get_value(
                analysis,
                "methodology",
            ),
        )
        render_field(
            "Datasets",
            get_value(
                analysis,
                "datasets",
            ),
        )

    with right_column:
        render_field(
            "Main Contributions",
            get_value(
                analysis,
                "main_contributions",
            ),
        )
        render_field(
            "Limitations",
            get_value(
                analysis,
                "limitations",
            ),
        )
        render_field(
            "Reviewer Feedback",
            get_value(
                review,
                "feedback",
            ),
        )
        render_field(
            "Warnings",
            get_value(
                review,
                "warnings",
            ),
        )

    if result.get(
        "used_fallback",
        False,
    ):
        st.warning(
            "The rule-based reader fallback was used."
        )

    if result.get("pipeline_error"):
        with st.expander(
            "View ReaderPipeline error"
        ):
            st.code(
                result["pipeline_error"]
            )

    serialized_result = serialize_value(
        result
    )

    json_report = json.dumps(
        serialized_result,
        indent=2,
        ensure_ascii=False,
    )

    markdown_report = create_markdown_report(
        result
    )

    st.markdown("### Download results")

    download_columns = st.columns(2)

    with download_columns[0]:
        st.download_button(
            "Download JSON",
            data=json_report,
            file_name="paper_analysis.json",
            mime="application/json",
            use_container_width=True,
        )

    with download_columns[1]:
        st.download_button(
            "Download Markdown",
            data=markdown_report,
            file_name="paper_analysis.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with st.expander(
        "View extracted text",
        expanded=False,
    ):
        extracted_text = result.get(
            "extracted_text",
            ""
        )

        st.text_area(
            "Extracted PDF text",
            value=extracted_text,
            height=400,
            disabled=True,
        )


def main() -> None:
    apply_custom_styles()
    initialize_state()
    render_header()

    (
        reader_mode,
        max_pages,
        max_reader_retries,
    ) = render_sidebar()

    try:
        workflow = get_workflow(
            reader_mode=reader_mode,
            max_reader_retries=max_reader_retries,
        )

    except Exception as error:
        st.error(
            "Failed to initialize the research workflow."
        )
        st.exception(error)
        st.stop()

    search_tab, upload_tab = st.tabs(
        [
            "Search Papers",
            "Upload PDF",
        ]
    )

    with search_tab:
        render_search_tab(
            workflow=workflow,
            max_pages=max_pages,
        )

    with upload_tab:
        render_upload_tab(
            workflow=workflow,
            max_pages=max_pages,
        )

    render_result()


if __name__ == "__main__":
    main()