from agents.reflection import ReflectionAgent


paper_analysis = {
    "title": "Test Paper",
    "research_problem": (
        "The paper studies robot navigation."
    ),
    "methodology": (
        "The paper proposes a navigation method."
    ),
    "datasets": (
        "Simulated environment."
    ),
    "main_contributions": [
        "A new navigation method."
    ],
    "limitations": (
        "Robot navigation remains a difficult problem."
    ),
}

review_result = {
    "approved": False,
    "score": 0.78,
    "feedback": (
        "The limitations field contains general "
        "research background instead of explicit limitations."
    ),
    "issues": [
        (
            "Limitations field appears to contain "
            "research background."
        )
    ],
}

agent = ReflectionAgent()

result = agent.reflect(
    paper_analysis=paper_analysis,
    review_result=review_result,
)

print("Should retry:")
print(result["should_retry"])

print("\nCritique:")
for item in result["critique"]:
    print(f"* {item}")

print("\nImprovement instructions:")
for item in result["improvement_instructions"]:
    print(f"* {item}")

print("\nFocus fields:")
for item in result["focus_fields"]:
    print(f"* {item}")

print("\nMetadata:")
print(result["metadata"])