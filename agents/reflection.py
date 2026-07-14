import json

from agents.base_agent import BaseAgent
from schemas.reflection_result import ReflectionResult
from services.llm_client import LLMClient


class ReflectionAgent(BaseAgent):
    """
    Analyze reviewer feedback and generate improvement instructions
    for a failed paper analysis.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        super().__init__(
            llm_client=llm_client,
        )

    def reflect(
        self,
        paper_analysis: dict,
        review_result: dict,
    ) -> dict:
        """
        Generate structured reflection feedback.

        Args:
            paper_analysis:
                The previous paper analysis produced by a reader.

            review_result:
                The evaluation result produced by ReviewerAgent.

        Returns:
            A dictionary containing retry decisions, critique,
            improvement instructions, and focus fields.
        """

        response = self.structured_chat(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(
                paper_analysis=paper_analysis,
                review_result=review_result,
            ),
            schema=ReflectionResult,
        )

        reflection = response.parsed

        result = reflection.model_dump()

        result["metadata"] = {
            "agent_name": self.agent_name,
            "model_name": response.model_name,
            "elapsed_seconds": response.elapsed_seconds,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
            "raw_response": response.raw_content,
        }

        return result

    @staticmethod
    def _build_system_prompt() -> str:
        return """
You are a reflection agent for an academic paper analysis system.

Your task is to inspect a paper analysis together with reviewer feedback
and decide how the analysis should be improved.

Requirements:

1. Use the reviewer feedback as the primary quality signal.
2. Identify concrete weaknesses in the paper analysis.
3. Produce precise instructions that another reader agent can follow.
4. Focus only on fields that require improvement.
5. Do not rewrite the full paper analysis.
6. Do not invent issues that are unsupported by the review.
7. Set should_retry to true when the reviewer rejected the analysis.
8. Set should_retry to false when the analysis already passed review.
9. Use valid field names when possible:
   research_problem
   methodology
   datasets
   main_contributions
   limitations
10. Keep critique and improvement instructions concise and actionable.
""".strip()

    @staticmethod
    def _build_user_prompt(
        paper_analysis: dict,
        review_result: dict,
    ) -> str:
        analysis_json = json.dumps(
            paper_analysis,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        review_json = json.dumps(
            review_result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        return f"""
Previous paper analysis:

{analysis_json}

Reviewer result:

{review_json}

Generate structured reflection feedback that can guide a new reading attempt.
""".strip()