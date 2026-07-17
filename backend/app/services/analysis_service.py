from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.schemas.analysis import (
    PaperAnalysisRequest,
)
from workflow.research_workflow import ResearchWorkflow


class AnalysisService:
    """
    Run paper analysis through ResearchWorkflow.
    """

    @staticmethod
    def _serialize_value(
        value: Any,
    ) -> Any:
        if value is None:
            return None

        if isinstance(value, dict):
            return {
                str(key): AnalysisService._serialize_value(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                AnalysisService._serialize_value(item)
                for item in value
            ]

        if isinstance(value, Path):
            return str(value)

        if hasattr(value, "model_dump"):
            return AnalysisService._serialize_value(
                value.model_dump()
            )

        if hasattr(value, "dict"):
            return AnalysisService._serialize_value(
                value.dict()
            )

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        return str(value)

    @staticmethod
    def _create_text_preview(
        text: str,
        limit: int = 2000,
    ) -> str:
        cleaned_text = text.strip()

        if len(cleaned_text) <= limit:
            return cleaned_text

        return (
            cleaned_text[:limit].rstrip()
            + "..."
        )

    def analyze_paper(
        self,
        request: PaperAnalysisRequest,
    ) -> dict[str, Any]:
        paper_data = request.paper.model_dump()

        topic = (
            request.topic
            or request.paper.title
        ).strip()

        workflow = ResearchWorkflow(
            reader_mode=request.reader_mode,
            max_reader_retries=(
                request.max_reader_retries
            ),
        )

        result = workflow.analyze_selected_paper(
            topic=topic,
            plan=request.plan,
            papers=[paper_data],
            selected_index=0,
            max_pages=request.max_pages,
        )

        extracted_text = str(
            result.get(
                "extracted_text",
                "",
            )
            or ""
        )

        serialized_analysis = (
            self._serialize_value(
                result.get("analysis")
            )
        )

        serialized_review = (
            self._serialize_value(
                result.get("review")
            )
        )

        serialized_pipeline = (
            self._serialize_value(
                result.get("reader_pipeline")
            )
        )

        return {
            "topic": topic,
            "paper": paper_data,
            "pdf_path": result.get(
                "pdf_path"
            ),
            "extracted_text_length": len(
                extracted_text
            ),
            "extracted_text_preview": (
                self._create_text_preview(
                    extracted_text
                )
            ),
            "analysis": serialized_analysis,
            "review": serialized_review,
            "reader_pipeline": serialized_pipeline,
            "used_fallback": bool(
                result.get(
                    "used_fallback",
                    False,
                )
            ),
            "pipeline_error": result.get(
                "pipeline_error"
            ),
        }