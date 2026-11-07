from services.academic_humanizer import humanize


class PlannerAgent:
    def plan(self, research_topic: str) -> str:
        steps = humanize("""Research Plan:
1. Define the research scope.
2. Search recent papers.
3. Extract methods, datasets, and limitations.
4. Compare different approaches.
5. Generate a structured literature review.
""")
        return f"\nResearch Topic:\n{research_topic}\n\n{steps}"