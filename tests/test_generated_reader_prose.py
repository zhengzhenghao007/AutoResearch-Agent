from agents.llm_reader import LLMReaderAgent
from agents.reader import ReaderAgent
from agents.reviewer import ReviewerAgent
from pipelines.reader_pipeline import ReaderPipeline
from services.llm_client import StructuredLLMResponse


SENTENCE = 'It is important to note that the sample includes 27 trials.'


class Client:
    def structured_chat(self, *, output_schema, **kwargs):
        parsed = output_schema(
            research_problem=SENTENCE,
            methodology='The researchers sampled three sites using fixed transects.',
            datasets=[SENTENCE],
            main_contributions=[SENTENCE],
            limitations=['Only one season was sampled.'],
        )
        return StructuredLLMResponse(parsed, 'offline', 1, 2, 3, 5, SENTENCE)


def test_reader_pipeline_edits_generated_analysis_before_review_and_keeps_raw_metadata():
    pipeline = ReaderPipeline(
        reader=LLMReaderAgent(Client()), reviewer=ReviewerAgent(),
        reflection_agent=object(), max_retries=0,
    )
    result = pipeline.run(SENTENCE, SENTENCE, '')
    analysis = result['final_analysis']
    assert analysis['title'] == SENTENCE
    assert analysis['research_problem'] == 'The sample includes 27 trials.'
    assert analysis['metadata']['structured_analysis']['main_contributions'] == ['The sample includes 27 trials.']
    assert analysis['metadata']['structured_analysis']['datasets'] == [SENTENCE]
    assert analysis['metadata']['raw_response'] == SENTENCE
    assert result['attempts'][0]['analysis'] == analysis


def test_rule_reader_keeps_extracted_paper_sentence():
    analysis = ReaderAgent().analyze(SENTENCE, SENTENCE, '')
    assert analysis['research_problem'] == SENTENCE
