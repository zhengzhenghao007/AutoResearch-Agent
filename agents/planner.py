class PlannerAgent:
    def plan(self, research_topic: str) -> str:
        return f"""
Research Topic:
{research_topic}

Research Plan:
1. Define the research scope.
2. Search recent papers.
3. Extract methods, datasets, and limitations.
4. Compare different approaches.
5. Generate a structured literature review.
"""