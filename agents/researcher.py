class ResearcherAgent:
    def search_papers(self, research_topic: str) -> list[dict]:
        return [
            {
                "title": "Vision-Language Navigation: A Survey",
                "year": 2024,
                "authors": ["Example Author"],
                "summary": "A survey of vision-language navigation methods, datasets, and challenges."
            },
            {
                "title": "Large Language Models for Embodied AI",
                "year": 2024,
                "authors": ["Example Author"],
                "summary": "Discusses how LLMs can support planning and decision-making in embodied agents."
            },
            {
                "title": "Multimodal Foundation Models for Robotics",
                "year": 2025,
                "authors": ["Example Author"],
                "summary": "Explores how vision-language models are used for robotic perception and control."
            }
        ]
    