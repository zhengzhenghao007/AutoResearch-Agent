from __future__ import annotations

from datetime import date, datetime
from typing import Any

from workflow.research_workflow import ResearchWorkflow


class ResearchService:
    """
    Connect the FastAPI layer to ResearchWorkflow.
    """

    def __init__(self) -> None:
        # Search does not need the LLM reader.
        # Rule mode avoids initializing the LLM pipeline
        # for a simple paper search request.
        self.workflow = ResearchWorkflow(
            reader_mode="rule",
            max_reader_retries=0,
        )

    @staticmethod
    def _read_value(
        value: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if value is None:
            return default

        if isinstance(value, dict):
            return value.get(
                key,
                default,
            )

        return getattr(
            value,
            key,
            default,
        )

    @classmethod
    def _serialize_author(
        cls,
        author: Any,
    ) -> str:
        if isinstance(author, str):
            return author

        name = cls._read_value(
            author,
            "name",
        )

        if name:
            return str(name)

        return str(author)

    @classmethod
    def _serialize_authors(
        cls,
        authors: Any,
    ) -> list[str]:
        if not authors:
            return []

        if isinstance(authors, str):
            return [authors]

        if isinstance(authors, (list, tuple)):
            return [
                cls._serialize_author(author)
                for author in authors
            ]

        return [
            cls._serialize_author(authors)
        ]

    @staticmethod
    def _serialize_date(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, date):
            return value.isoformat()

        return str(value)

    @classmethod
    def _serialize_paper(
        cls,
        paper: Any,
    ) -> dict[str, Any]:
        return {
            "title": str(
                cls._read_value(
                    paper,
                    "title",
                    "Untitled paper",
                )
            ),
            "authors": cls._serialize_authors(
                cls._read_value(
                    paper,
                    "authors",
                    [],
                )
            ),
            "summary": str(
                cls._read_value(
                    paper,
                    "summary",
                    "",
                )
                or ""
            ),
            "published": cls._serialize_date(
                cls._read_value(
                    paper,
                    "published",
                    "",
                )
            ),
            "pdf_url": str(
                cls._read_value(
                    paper,
                    "pdf_url",
                    "",
                )
                or ""
            ),
            "entry_id": str(
                cls._read_value(
                    paper,
                    "entry_id",
                    "",
                )
                or ""
            ),
        }

    def search_papers(
        self,
        topic: str,
        max_results: int,
    ) -> dict[str, Any]:
        search_result = self.workflow.search(
            topic=topic,
            max_results=max_results,
        )

        papers = [
            self._serialize_paper(paper)
            for paper in search_result.get(
                "papers",
                [],
            )
        ]

        return {
            "topic": search_result.get(
                "topic",
                topic,
            ),
            "plan": search_result.get(
                "plan"
            ),
            "papers": papers,
            "total": len(papers),
        }