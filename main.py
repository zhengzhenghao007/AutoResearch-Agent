from agents.planner import PlannerAgent


def main():
    planner = PlannerAgent()
    topic = "Recent advances in Vision-Language Models for robot navigation"
    result = planner.plan(topic)
    print(result)


if __name__ == "__main__":
    main()