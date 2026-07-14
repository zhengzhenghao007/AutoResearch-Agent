import re
from typing import Any


class ReviewerAgent:
    """
    Review the quality and completeness of a paper analysis.

    The reviewer uses deterministic checks so that evaluation is
    fast, reproducible, and free of additional LLM cost.
    """

    REQUIRED_FIELDS = {
        "research_problem",
        "methodology",
        "datasets",
        "main_contributions",
        "limitations",
    }

    LIMITATION_SIGNALS = {
        "limitation",
        "limitations",
        "limited",
        "restrict",
        "restricted",
        "restriction",
        "weakness",
        "weaknesses",
        "shortcoming",
        "shortcomings",
        "drawback",
        "drawbacks",
        "lack",
        "lacks",
        "lacking",
        "absence",
        "absent",
        "without",
        "only",
        "not evaluated",
        "not tested",
        "not addressed",
        "not considered",
        "no evaluation",
        "no real-world",
        "no real world",
        "simulation only",
        "simulated only",
        "single environment",
        "small dataset",
        "small sample",
        "future work",
        "fails to",
        "unable to",
        "cannot",
        "may not",
        "does not",
        "dependency",
        "depends on",
        "sensitive to",
        "scalability",
        "computational cost",
    }

    BACKGROUND_SIGNALS = {
        "remains a challenge",
        "is a difficult problem",
        "presents significant challenges",
        "is an important topic",
        "has attracted attention",
        "is widely studied",
        "privacy is a central topic",
        "considerations remain underdeveloped",
    }

    UNAVAILABLE_LIMITATION_SIGNALS = {
        "no explicit limitations were identified",
        "no explicit limitation was identified",
        "no limitations were identified",
        "no limitation was identified",
        "limitations were not identified",
        "limitation was not identified",
        "not identified in the supplied paper text",
        "not stated in the supplied paper text",
        "not provided in the supplied paper text",
    }

    GENERAL_PLACEHOLDER_SIGNALS = {
        "unknown",
        "not available",
        "n/a",
        "none",
    }

    def review(
        self,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Review one paper analysis.

        Returns:
            A dictionary containing approval status, score,
            issues, warnings, and feedback.
        """

        issues: list[str] = []
        warnings: list[str] = []
        penalties = 0.0

        if not isinstance(analysis, dict):
            return {
                "approved": False,
                "score": 0.0,
                "issues": [
                    "The paper analysis must be a dictionary."
                ],
                "warnings": [],
                "feedback": (
                    "1. The paper analysis must be a dictionary."
                ),
            }

        missing_fields = [
            field
            for field in self.REQUIRED_FIELDS
            if field not in analysis
        ]

        for field in sorted(missing_fields):
            issues.append(
                f"Required field is missing: {field}."
            )
            penalties += 0.2

        if missing_fields:
            return self._build_result(
                issues=issues,
                warnings=warnings,
                penalties=penalties,
            )

        research_problem = self._normalize_text(
            analysis.get("research_problem")
        )

        methodology = self._normalize_text(
            analysis.get("methodology")
        )

        datasets = self._normalize_text(
            analysis.get("datasets")
        )

        limitations = self._normalize_text(
            analysis.get("limitations")
        )

        contributions = self._normalize_contributions(
            analysis.get("main_contributions")
        )

        if self._is_too_short(
            research_problem,
            minimum_words=4,
        ):
            issues.append(
                "Research problem is too short or insufficiently specific."
            )
            penalties += 0.12

        if self._is_too_short(
            methodology,
            minimum_words=6,
        ):
            issues.append(
                "Methodology is too short or insufficiently specific."
            )
            penalties += 0.12

        if self._is_general_placeholder(datasets):
            warnings.append(
                "Datasets or evaluation environments were not identified."
            )

        if not contributions:
            issues.append(
                "No main contributions were identified."
            )
            penalties += 0.12

        elif all(
            self._is_too_short(
                contribution,
                minimum_words=3,
            )
            for contribution in contributions
        ):
            issues.append(
                "Main contributions are too vague."
            )
            penalties += 0.08

        limitation_issue, limitation_warning = (
            self._review_limitations(
                limitations
            )
        )

        if limitation_issue:
            issues.append(
                limitation_issue
            )
            penalties += 0.12

        if limitation_warning:
            warnings.append(
                limitation_warning
            )

        approved = len(issues) == 0

        return self._build_result(
            issues=issues,
            warnings=warnings,
            penalties=penalties,
            approved=approved,
        )

    def _review_limitations(
        self,
        limitations: str,
    ) -> tuple[str | None, str | None]:
        """
        Review the limitations field.

        A truthful statement that the supplied text contains no
        explicit limitations is accepted with a warning.
        """

        if not limitations:
            return (
                "Limitations field is empty.",
                None,
            )

        normalized = limitations.lower().strip()

        if any(
            signal in normalized
            for signal in self.UNAVAILABLE_LIMITATION_SIGNALS
        ):
            return (
                None,
                (
                    "No explicit limitations were found in the "
                    "supplied paper content."
                ),
            )

        if self._is_general_placeholder(
            limitations
        ):
            return (
                "Limitations field contains a placeholder value.",
                None,
            )

        has_limitation_signal = any(
            signal in normalized
            for signal in self.LIMITATION_SIGNALS
        )

        has_background_signal = any(
            signal in normalized
            for signal in self.BACKGROUND_SIGNALS
        )

        if (
            has_background_signal
            and not has_limitation_signal
        ):
            return (
                (
                    "Limitations field appears to contain "
                    "research background."
                ),
                None,
            )

        if not has_limitation_signal:
            return (
                (
                    "Limitations field does not contain "
                    "a clear study-specific constraint."
                ),
                None,
            )

        return None, None

    def _build_result(
        self,
        issues: list[str],
        warnings: list[str],
        penalties: float,
        approved: bool | None = None,
    ) -> dict[str, Any]:
        score = max(
            0.0,
            min(
                1.0,
                1.0 - penalties,
            ),
        )

        if approved is None:
            approved = len(issues) == 0

        feedback_lines: list[str] = []

        if approved:
            feedback_lines.append(
                "The paper analysis passed all required checks."
            )
        else:
            feedback_lines.extend(
                f"{index}. {issue}"
                for index, issue in enumerate(
                    issues,
                    start=1,
                )
            )

        if warnings:
            feedback_lines.append(
                "Warnings:"
            )

            feedback_lines.extend(
                f"* {warning}"
                for warning in warnings
            )

        return {
            "approved": approved,
            "score": round(score, 2),
            "issues": issues,
            "warnings": warnings,
            "feedback": "\n".join(
                feedback_lines
            ),
        }

    def _is_general_placeholder(
        self,
        text: str,
    ) -> bool:
        normalized = text.lower().strip()

        if not normalized:
            return True

        return normalized in self.GENERAL_PLACEHOLDER_SIGNALS

    @staticmethod
    def _normalize_text(
        value: object,
    ) -> str:
        if value is None:
            return ""

        if isinstance(value, list):
            return " ".join(
                str(item).strip()
                for item in value
                if str(item).strip()
            )

        return str(value).strip()

    @staticmethod
    def _normalize_contributions(
        value: object,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return []

            return [cleaned_value]

        if not isinstance(value, list):
            value = [value]

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    @staticmethod
    def _is_too_short(
        text: str,
        minimum_words: int,
    ) -> bool:
        words = re.findall(
            r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?",
            text,
        )

        return len(words) < minimum_words