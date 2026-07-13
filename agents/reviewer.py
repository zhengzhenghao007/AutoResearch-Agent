import re


class ReviewerAgent:
    REQUIRED_FIELDS = (
        "research_problem",
        "methodology",
        "datasets",
        "main_contributions",
        "limitations",
    )

    PLACEHOLDER_PHRASES = (
        "could not be identified",
        "no dataset",
        "no explicit contribution",
        "no explicit limitation",
        "may be required",
    )

    DATASET_KEYWORDS = (
        "dataset",
        "benchmark",
        "simulation",
        "environment",
        "platform",
        "s3dis",
        "habitat",
        "matterport",
        "real-world",
    )

    LIMITATION_KEYWORDS = (
        "however",
        "limitation",
        "limited",
        "only",
        "cannot",
        "fails",
        "restricted",
        "future work",
        "remains",
        "depend",
    )

    METHOD_KEYWORDS = (
        "propose",
        "introduce",
        "framework",
        "approach",
        "method",
        "model",
        "algorithm",
    )

    def review(self, analysis: dict) -> dict:
        issues = []

        self._check_required_fields(
            analysis=analysis,
            issues=issues,
        )

        self._check_placeholders(
            analysis=analysis,
            issues=issues,
        )

        self._check_methodology(
            analysis=analysis,
            issues=issues,
        )

        self._check_datasets(
            analysis=analysis,
            issues=issues,
        )

        self._check_limitations(
            analysis=analysis,
            issues=issues,
        )

        self._check_contributions(
            analysis=analysis,
            issues=issues,
        )

        score = self._calculate_score(issues)

        critical_issue_keywords = (
            "Methodology does not describe",
            "Dataset field contains no recognizable",
            "Dataset field may contain unrelated",
            "Limitations field does not contain",
            "Limitations field appears to contain",
        )

        has_critical_issue = any(
            any(keyword in issue for keyword in critical_issue_keywords)
            for issue in issues
        )

        approved = score >= 0.8 and not has_critical_issue

        return {
            "approved": approved,
            "score": score,
            "issues": issues,
            "feedback": self._build_feedback(issues),
        }

    def _check_required_fields(
        self,
        analysis: dict,
        issues: list[str],
    ) -> None:
        for field in self.REQUIRED_FIELDS:
            value = analysis.get(field)

            if value is None:
                issues.append(f"Missing field: {field}")
                continue

            if isinstance(value, str) and not value.strip():
                issues.append(f"Empty field: {field}")

            if isinstance(value, list) and not value:
                issues.append(f"Empty field: {field}")

    def _check_placeholders(
        self,
        analysis: dict,
        issues: list[str],
    ) -> None:
        searchable_text = self._flatten_analysis(analysis).lower()

        for phrase in self.PLACEHOLDER_PHRASES:
            if phrase in searchable_text:
                issues.append(
                    f"Placeholder content detected: {phrase}"
                )

    def _check_methodology(
        self,
        analysis: dict,
        issues: list[str],
    ) -> None:
        methodology = str(
            analysis.get("methodology", "")
        ).lower()

        if not any(
            keyword in methodology
            for keyword in self.METHOD_KEYWORDS
        ):
            issues.append(
                "Methodology does not describe a concrete method."
            )

    def _check_datasets(
        self,
        analysis: dict,
        issues: list[str],
    ) -> None:
        datasets = str(
            analysis.get("datasets", "")
        ).lower()

        if not any(
            keyword in datasets
            for keyword in self.DATASET_KEYWORDS
        ):
            issues.append(
                "Dataset field contains no recognizable dataset, "
                "benchmark, platform, or environment."
            )

        sentences = self._split_sentences(datasets)

        unrelated_sentences = [
            sentence
            for sentence in sentences
            if not any(
                keyword in sentence
                for keyword in self.DATASET_KEYWORDS
            )
        ]

        if unrelated_sentences:
            issues.append(
                "Dataset field may contain unrelated background sentences."
            )

    def _check_limitations(
        self,
        analysis: dict,
        issues: list[str],
    ) -> None:
        limitations = str(
            analysis.get("limitations", "")
        ).lower()

        if not any(
            keyword in limitations
            for keyword in self.LIMITATION_KEYWORDS
        ):
            issues.append(
                "Limitations field does not contain an explicit limitation."
            )

        background_phrases = (
            "is a critical concern",
            "significant challenges",
            "vast amounts of personal",
            "remain underdeveloped",
        )

        if any(
            phrase in limitations
            for phrase in background_phrases
        ):
            issues.append(
                "Limitations field appears to contain research background."
            )

    def _check_contributions(
        self,
        analysis: dict,
        issues: list[str],
    ) -> None:
        contributions = analysis.get(
            "main_contributions",
            [],
        )

        if not contributions:
            issues.append(
                "No main contribution was extracted."
            )
            return

        if self._has_duplicates(contributions):
            issues.append(
                "Duplicate contributions were detected."
            )

    @staticmethod
    def _flatten_analysis(analysis: dict) -> str:
        values = []

        for value in analysis.values():
            if isinstance(value, list):
                values.extend(
                    str(item)
                    for item in value
                )
            elif isinstance(value, dict):
                values.extend(
                    str(item)
                    for item in value.values()
                )
            else:
                values.append(str(value))

        return " ".join(values)

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        return [
            sentence.strip()
            for sentence in re.split(
                r"(?<=[.!?])\s+",
                text,
            )
            if sentence.strip()
        ]

    @staticmethod
    def _has_duplicates(items: list[str]) -> bool:
        normalized = [
            re.sub(
                r"[^a-z0-9]+",
                "",
                item.lower(),
            )
            for item in items
        ]

        return len(normalized) != len(set(normalized))

    @staticmethod
    def _calculate_score(
        issues: list[str],
    ) -> float:
        penalty_per_issue = 0.12

        score = 1.0 - (
            len(issues) * penalty_per_issue
        )

        return max(
            0.0,
            round(score, 2),
        )

    @staticmethod
    def _build_feedback(
        issues: list[str],
    ) -> str:
        if not issues:
            return (
                "The paper analysis passed "
                "all current checks."
            )

        return " ".join(
            f"{index}. {issue}"
            for index, issue in enumerate(
                issues,
                start=1,
            )
        )