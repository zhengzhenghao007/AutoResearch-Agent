from schemas.paper_analysis import PaperAnalysis
from services.llm_client import LLMClient


client = LLMClient()

result = client.structured_chat(
    system_prompt=(
        "You analyze academic papers. "
        "Use only the supplied information."
    ),
    user_prompt=(
        "Analyze this paper summary:\n\n"
        "The paper studies robot navigation using "
        "vision-language models. It proposes a framework "
        "that combines visual observations with language "
        "instructions. Experiments are conducted in a "
        "simulated indoor environment. The main limitation "
        "is the lack of real-world evaluation."
    ),
    output_schema=PaperAnalysis,
)

print("Parsed result:")
print(result.parsed.model_dump())

print("\nModel:")
print(result.model_name)

print("\nElapsed seconds:")
print(result.elapsed_seconds)

print("\nTokens:")
print(
    result.input_tokens,
    result.output_tokens,
    result.total_tokens,
)