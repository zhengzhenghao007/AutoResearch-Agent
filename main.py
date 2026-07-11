from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent


def main():
    topic = "Recent advances in Vision-Language Models for robot navigation"

    planner = PlannerAgent()
    researcher = ResearcherAgent()

    plan = planner.plan(topic)
    papers = researcher.search_papers(topic)

    print("Research Plan:")
    print(plan)

    print("\nFound Papers:")
    for index, paper in enumerate(papers, start=1):
        print(f"\n{index}. {paper['title']} ({paper['year']})")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Summary: {paper['summary']}")


if __name__ == "__main__":
    main()
    