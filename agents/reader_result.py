from dataclasses import dataclass, field


@dataclass
class ReaderResult:
    title: str
    research_problem: str
    methodology: str
    datasets: str
    main_contributions: list[str]
    limitations: str

    model_name: str = "unknown"
    elapsed_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "research_problem": self.research_problem,
            "methodology": self.methodology,
            "datasets": self.datasets,
            "main_contributions": self.main_contributions,
            "limitations": self.limitations,
            "model_name": self.model_name,
            "elapsed_seconds": self.elapsed_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "metadata": self.metadata,
        }