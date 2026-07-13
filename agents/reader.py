import re


class ReaderAgent:
    def analyze(
        self,
        title: str,
        abstract: str,
        extracted_text: str,
    ) -> dict:
        clean_abstract = self._clean_text(abstract)
        clean_text = self._clean_text(extracted_text)

        abstract_sentences = self._split_sentences(clean_abstract)
        paper_sentences = self._split_sentences(clean_text)
        all_sentences = abstract_sentences + paper_sentences

        research_problem = self._find_first_match(
            abstract_sentences,
            (
                "lack",
                "challenge",
                "remain underdeveloped",
                "limited",
                "has not been",
            ),
            fallback=(
                abstract_sentences[0]
                if abstract_sentences
                else "Research problem could not be identified."
            ),
        )

        methodology = self._find_first_match(
            abstract_sentences,
            (
                "we propose",
                "we introduce",
                "our framework",
                "our approach",
                "specifically",
            ),
            fallback="Methodology could not be identified.",
        )

        dataset_sentences = self._find_matches(
            all_sentences,
            (
                "dataset",
                "benchmark",
                "simulation environment",
                "real-world office",
                "robotic platform",
            ),
            limit=3,
        )

        contribution_sentences = self._find_matches(
            abstract_sentences,
            (
                "demonstrate",
                "significantly enhances",
                "outperform",
                "achieve",
                "improve",
            ),
            limit=3,
        )

        limitation_sentences = self._find_matches(
            all_sentences,
            (
                "limitation",
                "future work",
                "however",
                "only",
                "restricted",
                "cannot",
                "fails",
                "remains to be",
            ),
            limit=2,
        )

        return {
            "title": title,
            "research_problem": research_problem,
            "methodology": methodology,
            "datasets": (
                " ".join(dataset_sentences)
                if dataset_sentences
                else "No dataset or experimental environment was identified."
            ),
            "main_contributions": (
                contribution_sentences
                if contribution_sentences
                else ["No explicit contribution statement was identified."]
            ),
            "limitations": (
                " ".join(limitation_sentences)
                if limitation_sentences
                else (
                    "No explicit limitation was found in the extracted pages. "
                    "A complete-paper or LLM-based analysis may be required."
                )
            ),
            "abstract": clean_abstract,
            "text_preview": clean_text[:1500],
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\u2019", "'")
        text = text.replace("\u2018", "'")
        text = text.replace("\u201c", '"')
        text = text.replace("\u201d", '"')

        text = re.sub(r"-\s+", "", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        if not text:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text)

        cleaned_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()

            if len(sentence) < 35:
                continue

            if sentence.startswith("TABLE "):
                continue

            if sentence.startswith("--- Page"):
                continue

            cleaned_sentences.append(sentence)

        return cleaned_sentences

    @staticmethod
    def _find_first_match(
        sentences: list[str],
        keywords: tuple[str, ...],
        fallback: str,
    ) -> str:
        for sentence in sentences:
            lower_sentence = sentence.lower()

            if any(keyword.lower() in lower_sentence for keyword in keywords):
                return sentence

        return fallback

    @staticmethod
    def _find_matches(
        sentences: list[str],
        keywords: tuple[str, ...],
        limit: int,
    ) -> list[str]:
        results = []
        normalized_results = set()

        for sentence in sentences:
            lower_sentence = sentence.lower()

            if not any(
                keyword.lower() in lower_sentence
                for keyword in keywords
            ):
                continue

            normalized = re.sub(
                r"[^a-z0-9]+",
                "",
                lower_sentence,
            )

            duplicate = any(
                normalized in existing or existing in normalized
                for existing in normalized_results
            )

            if duplicate:
                continue

            results.append(sentence)
            normalized_results.add(normalized)

            if len(results) >= limit:
                break

        return results