from pipelines.reader_pipeline import ReaderPipeline


pipeline = ReaderPipeline(
    max_retries=2,
)

result = pipeline.run(
    title="Language-Guided Robot Navigation",
    abstract=(
        "This paper studies language-guided robot navigation."
    ),
    extracted_text=(
        "The proposed method combines RGB camera observations "
        "with natural language instructions. A transformer-based "
        "policy predicts robot navigation actions. Experiments are "
        "performed in a simulated indoor environment. The authors "
        "identify the absence of real-world experiments as a "
        "limitation."
    ),
)

print("\n" + "=" * 60)
print("Reader Pipeline Result")
print("=" * 60)

print("\nApproved:")
print(result["approved"])

print("\nAttempt count:")
print(result["attempt_count"])

print("\nRetry count:")
print(result["retry_count"])

print("\nFinal research problem:")
print(
    result["final_analysis"]["research_problem"]
)

print("\nFinal methodology:")
print(
    result["final_analysis"]["methodology"]
)

print("\nFinal limitations:")
print(
    result["final_analysis"]["limitations"]
)

print("\nFinal review:")
print(
    result["final_review"]
)

print("\nReflections:")
print(
    result["reflections"]
)

print("\nStatistics:")
print(
    result["statistics"]
)