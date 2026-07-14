from agents.llm_reader import LLMReaderAgent


reader = LLMReaderAgent()

reflection = {
    "critique": [
        (
            "The methodology is too vague and the "
            "limitations field lacks study-specific details."
        )
    ],
    "improvement_instructions": [
        (
            "Describe the method more precisely using only "
            "the supplied text."
        ),
        (
            "Extract the explicit simulation-only limitation."
        ),
    ],
    "focus_fields": [
        "methodology",
        "limitations",
    ],
}

result = reader.analyze(
    title="Robot Navigation Test Paper",
    abstract=(
        "This paper studies language-guided robot navigation."
    ),
    extracted_text=(
        "The proposed method combines RGB camera observations "
        "with natural language instructions. A transformer-based "
        "policy predicts navigation actions. Evaluation is "
        "performed in a simulated indoor environment. The authors "
        "state that the absence of real-world experiments is a "
        "limitation."
    ),
    reflection_instructions=reflection,
)

print("Methodology:")
print(result["methodology"])

print("\nLimitations:")
print(result["limitations"])

print("\nReflection applied:")
print(result["metadata"]["reflection_applied"])

print("\nStored reflection:")
print(result["metadata"]["reflection_instructions"])