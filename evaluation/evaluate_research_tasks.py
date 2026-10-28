"""Offline real-corpus retrieval comparison; no semantic or human quality labels."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import platform
import tempfile
from time import perf_counter
from schemas.research import ResearchRun

def text_sha256(path):
    """Hash UTF-8 text with LF newlines, matching Git across checkout platforms."""
    return hashlib.sha256(Path(path).read_text(encoding='utf-8').encode('utf-8')).hexdigest()

CASES = [
    {'id': 'missing_inputs', 'question': 'How do conformal methods handle missing values and imputation?', 'subquestions': ['missing values', 'imputation'], 'facets': [['missing'], ['imputation', 'impute']]},
    {'id': 'perturbed_inputs', 'question': 'How does robust conformal prediction handle perturbations and coverage?', 'subquestions': ['perturbations robustness', 'coverage guarantees'], 'facets': [['perturbation', 'perturbations'], ['coverage']]},
    {'id': 'sparse_regions', 'question': 'How does epistemic uncertainty relate to training data and conditional coverage?', 'subquestions': ['epistemic uncertainty', 'conditional coverage'], 'facets': [['epistemic'], ['conditional']]},
    {'id': 'lexical_decoy', 'question': 'zygomorphic quasicrystals superconductivity', 'subquestions': ['zygomorphic quasicrystals superconductivity'], 'facets': [['zygomorphic'], ['quasicrystals'], ['superconductivity']]},
    {'id': 'absent_topic', 'question': 'zygomorphic quasicrystals', 'subquestions': ['zygomorphic quasicrystals'], 'facets': [['zygomorphic'], ['quasicrystals']]},
]


def measure_selection(run, selected, facets):
    """Require exact saved ID/source/page/quote equality plus literal page support.

    Lexical facet hits count only valid bindings. Tokens are case-insensitive whole
    words. Neither term presence nor literal support establishes semantic support.
    """
    registry = {e.id: (e, p.document) for p in run.papers for e in p.evidence}
    valid = []
    errors = []
    for record in selected:
        saved = registry.get(record.get('id'))
        ok = bool(saved and saved[0].model_dump() == record)
        if ok:
            evidence, document = saved
            ok = evidence.source_id == document.source.id and any(
                p.number == evidence.page and evidence.quote in p.text for p in document.pages)
        if ok:
            valid.append(record)
        else:
            errors.append(record.get('id'))
    tokens = set(re.findall(r'[a-z]+', ' '.join(e['quote'] for e in valid).lower()))
    hits = [any(term.lower() in tokens for term in alternatives) for alternatives in facets]
    return {
        'selected_count': len(selected), 'valid_binding_count': len(valid),
        'exact_binding_rate': len(valid) / len(selected) if selected else None,
        'lexical_facet_coverage': sum(hits) / len(hits) if hits else None,
        'omitted_facets': [i for i, hit in enumerate(hits) if not hit],
        'invalid_binding_ids': errors,
        'unique_sources': len({e['source_id'] for e in valid}),
    }


def baseline_selection(run, limit=6):
    """Fixed method-category extraction baseline, round robin by saved paper.

    Mirrors the existing method-comparison category input; cap is shared with
    executor. Round robin avoids silently giving the first paper all six slots.
    """
    groups = []
    for paper in run.papers:
        method_ids = {eid for c in paper.claims if c.category == 'method' for eid in c.evidence_ids}
        groups.append([e.model_dump() for e in paper.evidence if e.id in method_ids])
    result = []
    for index in range(max(map(len, groups), default=0)):
        for group in groups:
            if index < len(group):
                result.append(group[index])
                if len(result) == limit:
                    return result
    return result


def evaluate(root: Path, repeats=3, work_dir=None):
    from schemas.research_tasks import ResearchTaskCreate, TaskBudget
    from services.research_tasks import ResearchTaskExecutor
    from services.research_store import ResearchStore
    if repeats < 1:
        raise ValueError('repeats must be positive')
    corpus_path = root / 'examples/conformal-prediction/outputs/run.json'
    sources_path = root / 'examples/conformal-prediction/sources.json'
    run = ResearchRun.model_validate_json(corpus_path.read_text(encoding='utf-8'))
    sources = json.loads(sources_path.read_text(encoding='utf-8'))
    registry = {e.id: e.model_dump() for p in run.papers for e in p.evidence}
    trials = []
    with tempfile.TemporaryDirectory(dir=work_dir) as scratch:
        for repeat in range(repeats):
            for case in CASES:
                start = perf_counter()
                selected = baseline_selection(run)
                baseline = {'latency_seconds': perf_counter() - start, 'cost_usd': 0,
                            'input_tokens': 0, 'output_tokens': 0, 'selected': selected,
                            'metrics': measure_selection(run, selected, case['facets'])}
                store = ResearchStore(Path(scratch) / f'{repeat}-{case["id"]}')
                store.save(run)
                start = perf_counter()
                executor = ResearchTaskExecutor(store)
                task = executor.create(run.id, ResearchTaskCreate(question=case['question'], subquestions=case['subquestions'], budget=TaskBudget(max_steps=20, max_seconds=60, max_evidence=6)))
                for _ in range(30):
                    if task.status in {'completed', 'incomplete', 'cancelled', 'failed', 'stale', 'budget_exhausted'}:
                        break
                    # Recreate service after every durable step to exercise resume.
                    task = ResearchTaskExecutor(store).next(run.id, task.id)
                else:
                    raise RuntimeError('Executor failed to stop within evaluation step bound')
                latency = perf_counter() - start
                ids = list(dict.fromkeys(eid for step in task.steps if step.result for eid in step.result.evidence_ids))
                selected = [registry.get(eid, {'id': eid}) for eid in ids]
                trials.append({'case_id': case['id'], 'repeat': repeat + 1, 'baseline': baseline,
                               'executor': {'latency_seconds': latency, 'cost_usd': task.usage.cost_usd,
                                            'status': task.status, 'stop_reason': task.stop_reason,
                                            'selected': selected, 'metrics': measure_selection(run, selected, case['facets']),
                                            'task': task.model_dump(mode='json')}})
    signatures = {}
    for case in CASES:
        for method in ('baseline', 'executor'):
            values = [[e['id'] for e in t[method]['selected']] for t in trials if t['case_id'] == case['id']]
            signatures[f'{case["id"]}/{method}'] = all(v == values[0] for v in values)
    return {'schema_version': 1, 'command': 'python -m evaluation.evaluate_research_tasks --output examples/research-execution/results.json --repeats 3',
            'provenance': {'corpus': str(corpus_path.relative_to(root)).replace('\\', '/'),
                           'corpus_sha256': text_sha256(corpus_path),
                           'sources_sha256': text_sha256(sources_path),
                           'text_hash_encoding': 'UTF-8 with LF newlines; original PDF hashes remain byte hashes', 'license': sources['license'], 'license_url': sources['license_url'],
                           'python': platform.python_version(),
                           'implementation_sha256': {name: text_sha256(root / name) for name in ('evaluation/evaluate_research_tasks.py', 'services/research_tasks.py', 'schemas/research_tasks.py')},
                           'papers': sources['papers']},
            'human_review': {'status': 'pending', 'semantic_support_rate': None, 'scientific_accuracy': None,
                             'rubric': ['Does each quote answer the question?', 'Are assumptions and limitations preserved?', 'Are cross-paper comparisons justified?', 'Which relevant evidence was omitted?']},
            'cases': CASES, 'repeats': repeats, 'selection_identical_across_repeats': signatures, 'trials': trials,
            'limitations': ['Purposive three-paper corpus; not a search-recall or scientific-validity benchmark.',
                            'Whole-word facet coverage is a retrieval proxy; no expert relevance gold labels.',
                            'Baseline is bounded fixed method-category selection, not a model or complete workflow timing.',
                            'Executor latency includes planning, SQLite persistence and reload; baseline latency is selection only.',
                            'Zero model/network calls; costs and tokens zero. Local CPU/storage costs not estimated.',
                            'Raw PDF hashes are inherited provenance; this offline run verifies saved text, not original PDF bytes.']}


def human_review_packet(report):
    """Unscored, source-bound work queue for an actual independent reviewer."""
    cases = {case['id']: case for case in report['cases']}
    items, seen = [], set()
    for trial in report['trials']:
        case = cases[trial['case_id']]
        for method in ('baseline', 'executor'):
            for evidence in trial[method]['selected']:
                key = (case['id'], method, json.dumps(evidence, sort_keys=True))
                if key in seen:
                    continue
                seen.add(key)
                items.append({'case_id': case['id'], 'method': method,
                              'question': case['question'], 'subquestions': case['subquestions'],
                              'evidence': evidence, 'status': 'pending', 'reviewer': None,
                              'reviewed_at': None,
                              'judgments': {'answers_question': None, 'semantic_support': None,
                                            'assumptions_preserved': None, 'bibliography_only': None},
                              'notes': None})
    return {'schema_version': 1, 'status': 'pending', 'provenance': report['provenance'],
            'instructions': 'An independent human must inspect the saved page in the pinned corpus and question before recording judgments. True/false/null judgments are not inferred from lexical metrics. Do not treat this packet as manuscript approval.',
            'case_reviews': [{'case_id': case['id'], 'question': case['question'],
                              'reviewer': None, 'status': 'pending',
                              'missing_evidence': None, 'comparison_validity': None,
                              'scientific_accuracy': None} for case in report['cases']],
            'items': items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    report = evaluate(Path(__file__).resolve().parents[1], args.repeats)
    report['command'] = f'python -m evaluation.evaluate_research_tasks --output {args.output.as_posix()} --repeats {args.repeats}'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    packet_path = args.output.with_name(args.output.stem + '-human-review.json')
    packet_path.write_text(json.dumps(human_review_packet(report), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'trials': len(report['trials']), 'human_review': 'pending'}))

if __name__ == '__main__':
    main()
