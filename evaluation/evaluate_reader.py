from agents.reader import ReaderAgent


TEST_CASES = [
    {
        "name": "PANav",
        "title": "PANav: Toward Privacy-Aware Robot Navigation via Vision-Language Models",
        "abstract": (
            "Current robotic systems still lack the functionality of "
            "privacy-aware navigation in public environments. "
            "We propose a framework that combines A* path generation "
            "with a vision-language model for privacy-aware path selection. "
            "Experimental results on the S3DIS dataset demonstrate improved "
            "privacy awareness in navigation."
        ),
        "text": (
            "The framework was evaluated using the S3DIS dataset and a "
            "real-world robotic platform in office environments. "
            "However, the method relies on predefined candidate paths and "
            "has only been tested in a limited number of environments."
        ),
        "expected_keywords": {
            "research_problem": ["lack", "privacy-aware navigation"],
            "methodology": ["propose", "vision-language model"],
            "datasets": ["S3DIS"],
            "limitations": ["limited", "predefined candidate paths"],
        },
    }
]


def keyword_score(text: str, expected_keywords: list[str]) -> float:
    lower_text = text.lower()

    matched = sum(
        1
        for keyword in expected_keywords
        if keyword.lower() in lower_text
    )

    return matched / len(expected_keywords)


def main() -> None:
    reader = ReaderAgent()
    total_scores = []

    for case in TEST_CASES:
        analysis = reader.analyze(
            title=case["title"],
            abstract=case["abstract"],
            extracted_text=case["text"],
        )

        print(f"\nEvaluation Case: {case['name']}")

        case_scores = {}

        for field, expected_keywords in case["expected_keywords"].items():
            predicted_text = analysis[field]

            if isinstance(predicted_text, list):
                predicted_text = " ".join(predicted_text)

            score = keyword_score(
                predicted_text,
                expected_keywords,
            )

            case_scores[field] = score

            print(f"{field}: {score:.2f}")

        average_score = sum(case_scores.values()) / len(case_scores)
        total_scores.append(average_score)

        print(f"Case Average: {average_score:.2f}")

    overall_score = sum(total_scores) / len(total_scores)

    print(f"\nOverall Reader Score: {overall_score:.2f}")


if __name__ == "__main__":
    main()