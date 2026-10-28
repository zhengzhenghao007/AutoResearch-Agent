from pathlib import Path
from schemas.research import ResearchRun
from evaluation.evaluate_research_tasks import measure_selection, evaluate

ROOT = Path(__file__).resolve().parents[1]

def corpus():
    return ResearchRun.model_validate_json((ROOT / 'examples/conformal-prediction/outputs/run.json').read_text(encoding='utf-8'))

def test_binding_rejects_valid_quote_attached_to_wrong_source_or_page():
    run = corpus()
    evidence = run.papers[0].evidence[0]
    good = measure_selection(run, [evidence.model_dump()], [['conformal']])
    assert good['exact_binding_rate'] == 1
    bad = evidence.model_dump()
    bad['source_id'] = run.papers[1].document.source.id
    assert measure_selection(run, [bad], [['conformal']])['exact_binding_rate'] == 0
    bad = evidence.model_dump()
    bad['quote'] += ' invented addition'
    assert measure_selection(run, [bad], [['conformal']])['exact_binding_rate'] == 0

def test_empty_and_unknown_evidence_never_receive_quality_credit():
    run = corpus()
    result = measure_selection(run, [], [['unobtainium']])
    assert result['exact_binding_rate'] is None
    assert result['lexical_facet_coverage'] == 0
    assert result['omitted_facets'] == [0]
    ev = run.papers[0].evidence[0].model_dump()
    ev['id'] = 'unknown'
    assert measure_selection(run, [ev], [['conformal']])['exact_binding_rate'] == 0

def test_real_evaluation_records_repetitions_without_human_labels(tmp_path):
    report = evaluate(ROOT, repeats=2, work_dir=tmp_path)
    assert report['human_review']['status'] == 'pending'
    assert report['human_review']['semantic_support_rate'] is None
    assert len(report['trials']) == 10
    assert len(report['provenance']['papers']) == 3
    for trial in report['trials']:
        for method in ('baseline', 'executor'):
            result = trial[method]
            assert result['latency_seconds'] >= 0
            assert result['cost_usd'] == 0
            assert result['metrics']['exact_binding_rate'] in (None, 1)
    assert all(t['executor']['status'] == 'incomplete' for t in report['trials'] if t['case_id'] == 'absent_topic')

def test_pending_packet_keeps_quote_binding_and_never_invents_reviewer():
    from evaluation.evaluate_research_tasks import human_review_packet
    evidence = corpus().papers[0].evidence[0].model_dump()
    report = {'provenance': {'corpus_sha256': 'pinned-corpus'},
              'cases': [{'id': 'case', 'question': 'A question?', 'subquestions': ['A facet?']}],
              'trials': [{'case_id': 'case', 'repeat': repeat,
                          'baseline': {'selected': [evidence]},
                          'executor': {'selected': [evidence]}} for repeat in (1, 2)]}
    packet = human_review_packet(report)
    assert len(packet['items']) == 2  # Separate methods; repeated identical quotes deduplicated.
    for item in packet['items']:
        assert item['evidence'] == evidence
        assert item['question'] == 'A question?'
        assert item['reviewer'] is None
        assert item['status'] == 'pending'
        assert all(value is None for value in item['judgments'].values())
def test_text_provenance_hash_is_stable_across_checkout_line_endings(tmp_path):
    from evaluation.evaluate_research_tasks import text_sha256
    first, second = tmp_path / 'lf.txt', tmp_path / 'crlf.txt'
    first.write_bytes(b'first\nsecond\n')
    second.write_bytes(b'first\r\nsecond\r\n')
    assert text_sha256(first) == text_sha256(second)

