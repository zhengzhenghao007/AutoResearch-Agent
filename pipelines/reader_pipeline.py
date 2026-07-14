from typing import Any

from agents.llm_reader import LLMReaderAgent
from agents.reflection import ReflectionAgent
from agents.reviewer import ReviewerAgent


class ReaderPipeline:
    """
    Coordinate paper reading, review, reflection, and retry.

    The pipeline performs the following process:

    1. Analyze the supplied paper.
    2. Review the generated analysis.
    3. Return immediately when the review is approved.
    4. Generate reflection feedback when the review fails.
    5. Analyze the paper again using the reflection feedback.
    6. Stop when approved or when the retry limit is reached.
    """

    def __init__(
        self,
        reader: LLMReaderAgent | None = None,
        reviewer: ReviewerAgent | None = None,
        reflection_agent: ReflectionAgent | None = None,
        max_retries: int = 2,
    ) -> None:
        if max_retries < 0:
            raise ValueError(
                "max_retries must be greater than or equal to 0."
            )

        self.reader = reader or LLMReaderAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.reflection_agent = (
            reflection_agent or ReflectionAgent()
        )
        self.max_retries = max_retries

    def run(
        self,
        title: str,
        abstract: str,
        extracted_text: str,
    ) -> dict[str, Any]:
        """
        Run the complete reader improvement pipeline.

        Args:
            title:
                Paper title.

            abstract:
                Paper abstract.

            extracted_text:
                Text extracted from the paper PDF.

        Returns:
            A dictionary containing the final analysis, review,
            reflections, attempt history, and pipeline statistics.
        """

        if not title.strip():
            raise ValueError("Paper title cannot be empty.")

        if not abstract.strip() and not extracted_text.strip():
            raise ValueError(
                "At least one of abstract or extracted_text "
                "must contain paper content."
            )

        attempts: list[dict[str, Any]] = []
        reflections: list[dict[str, Any]] = []

        reflection_instructions: dict[str, Any] | None = None

        final_analysis: dict[str, Any] | None = None
        final_review: dict[str, Any] | None = None

        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_elapsed_seconds = 0.0

        maximum_attempts = self.max_retries + 1

        for attempt_number in range(1, maximum_attempts + 1):
            print(
                f"\n[ReaderPipeline] Reading attempt "
                f"{attempt_number}/{maximum_attempts}"
            )

            analysis = self.reader.analyze(
                title=title,
                abstract=abstract,
                extracted_text=extracted_text,
                reflection_instructions=reflection_instructions,
            )

            print(
                f"[ReaderPipeline] Reviewing attempt "
                f"{attempt_number}..."
            )

            review = self.reviewer.review(
                analysis
            )

            attempt_record = {
                "attempt_number": attempt_number,
                "analysis": analysis,
                "review": review,
                "reflection_applied": (
                    reflection_instructions is not None
                ),
            }

            attempts.append(attempt_record)

            final_analysis = analysis
            final_review = review

            input_tokens = int(
                analysis.get("input_tokens", 0) or 0
            )

            output_tokens = int(
                analysis.get("output_tokens", 0) or 0
            )

            analysis_metadata = (
                analysis.get("metadata", {}) or {}
            )

            attempt_total_tokens = int(
                analysis_metadata.get(
                    "total_tokens",
                    input_tokens + output_tokens,
                )
                or input_tokens + output_tokens
            )

            elapsed_seconds = float(
                analysis.get(
                    "elapsed_seconds",
                    0.0,
                )
                or 0.0
            )

            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_tokens += attempt_total_tokens
            total_elapsed_seconds += elapsed_seconds

            if review.get("approved", False):
                print(
                    f"[ReaderPipeline] Analysis approved "
                    f"on attempt {attempt_number}."
                )
                break

            if attempt_number >= maximum_attempts:
                print(
                    "[ReaderPipeline] Maximum retry count reached."
                )
                break

            print(
                f"[ReaderPipeline] Attempt {attempt_number} "
                "was not approved."
            )

            print(
                "[ReaderPipeline] Generating reflection feedback..."
            )

            reflection = self.reflection_agent.reflect(
                paper_analysis=analysis,
                review_result=review,
            )

            reflections.append(reflection)

            reflection_metadata = (
                reflection.get("metadata", {}) or {}
            )

            total_input_tokens += int(
                reflection_metadata.get(
                    "input_tokens",
                    0,
                )
                or 0
            )

            total_output_tokens += int(
                reflection_metadata.get(
                    "output_tokens",
                    0,
                )
                or 0
            )

            total_tokens += int(
                reflection_metadata.get(
                    "total_tokens",
                    0,
                )
                or 0
            )

            total_elapsed_seconds += float(
                reflection_metadata.get(
                    "elapsed_seconds",
                    0.0,
                )
                or 0.0
            )

            should_retry = reflection.get(
                "should_retry",
                True,
            )

            if not should_retry:
                print(
                    "[ReaderPipeline] Reflection decided "
                    "that another attempt is unnecessary."
                )
                break

            reflection_instructions = {
                "critique": reflection.get(
                    "critique",
                    [],
                ),
                "improvement_instructions": reflection.get(
                    "improvement_instructions",
                    [],
                ),
                "focus_fields": reflection.get(
                    "focus_fields",
                    [],
                ),
            }

        approved = bool(
            final_review
            and final_review.get(
                "approved",
                False,
            )
        )

        return {
            "success": approved,
            "approved": approved,
            "attempt_count": len(attempts),
            "retry_count": max(
                len(attempts) - 1,
                0,
            ),
            "max_retries": self.max_retries,
            "final_analysis": final_analysis,
            "final_review": final_review,
            "reflections": reflections,
            "attempts": attempts,
            "statistics": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_tokens,
                "total_elapsed_seconds": (
                    total_elapsed_seconds
                ),
            },
        }