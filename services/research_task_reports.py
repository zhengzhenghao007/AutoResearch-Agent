"""Portable working notes from committed checkpoints, never scientific approval."""
from services.academic_humanizer import humanize
import html
import re

from schemas.research import ResearchRun
from schemas.research_tasks import ResearchTask
from services.research_tasks import task_source_hash


def build_task_report(task: ResearchTask, run: ResearchRun) -> dict:
    if task.run_id != run.id:
        raise ValueError('Task belongs to another research record')
    current = task.status != 'stale' and task.source_sha256 == task_source_hash(run, task.mode)
    warnings = [humanize('Working notes only. Lexical relevance and literal source checks do not establish scientific validity.')]
    if not current:
        warnings.append(humanize('Saved sources changed. Quotations are withheld; checkpoint IDs remain for audit. Create a new task.'))
    questions = []
    for question in task.subquestions:
        steps = [step for step in task.steps if step.question_id == question.id]
        retrieval = next((s for s in steps if s.tool in ('lexical_retrieve', 'research_retrieve')), None)
        inspection = next((s for s in steps if s.tool == 'inspect_sources'), None)
        checked = inspection is not None and inspection.status == 'completed' and inspection.result is not None
        selected = inspection if checked else retrieval
        result = selected.result if selected and selected.status == 'completed' else None
        ids = list(dict.fromkeys(result.evidence_ids)) if result else []
        gaps = list(dict.fromkeys(g for s in steps if s.result for g in s.result.gaps))
        evidence = []
        if current:
            for eid in ids:
                matches = [(p, e) for p in run.papers for e in p.evidence if e.id == eid]
                if len(matches) != 1:
                    gaps.append(humanize('Missing or ambiguous evidence binding: {eid}').format(eid=eid))
                    continue
                paper, item = matches[0]
                source = paper.document.source
                pages = [p for p in paper.document.pages if p.number == item.page]
                quote = ' '.join(item.quote.split())
                if item.source_id != source.id or len(pages) != 1 or not quote or quote not in ' '.join(pages[0].text.split()):
                    gaps.append(humanize('Invalid source/page/quote binding: {eid}').format(eid=eid))
                    continue
                evidence.append(dict(evidence_id=eid, source_id=source.id, title=source.title,
                                     uri=source.uri, source_sha256=source.sha256, page=item.page,
                                     quote=item.quote, binding_status='checked' if checked else 'not_checked'))
        questions.append(dict(id=question.id, question=question.question, requirements=question.requirements,
                              inspection_status=inspection.status if inspection else 'not_planned',
                              evidence_ids=ids, evidence=evidence, gaps=gaps))
    snapshot = task.model_dump(mode='json')
    if not current:
        for step in snapshot['steps']:
            if step['result']:
                step['result']['artifacts'] = []
    return dict(schema_version=1, report_kind='research_task_working_notes', scientific_validation='not_assessed',
                source_status='current' if current else 'stale', warnings=warnings,
                task=snapshot, questions=questions,
                artifacts=[a.model_dump(mode='json') for s in task.steps if s.result for a in s.result.artifacts] if current else [])


def _literal(value) -> str:
    # Render user/paper data as text, never Markdown structure, HTML or links.
    text = html.escape(' '.join(str(value).split()), quote=True)
    return re.sub(r'([\\`*_{}\[\]()#+.!|>~:\-])', r'\\\1', text)


def render_task_report(report: dict) -> str:
    task = report['task']
    lines = ['# Research task working notes', '', _literal(task['question']), '',
             f"Task: {_literal(task['id'])}", f"Record: {_literal(task['run_id'])}",
             f"Status: {_literal(task['status'])}", f"Source status: {report['source_status']}",
             'Scientific validation: not_assessed',
             f"Source snapshot: {_literal(task['source_sha256'])}",
             f"Checkpoint updated: {_literal(task['updated_at'])}", '']
    lines.extend('> ' + _literal(warning) for warning in report['warnings'])
    if task['stop_reason']:
        lines.extend(['', 'Stop reason: ' + _literal(task['stop_reason'])])
    usage, budget = task['usage'], task['budget']
    lines.extend(['', '## Budget and usage', '',
                  f"Step attempts: {usage['steps']} / {budget['max_steps']}",
                  f"Active seconds: {usage['seconds']} / {budget['max_seconds']}",
                  f"Evidence items: {usage['evidence']} / {budget['max_evidence']}",
                  f"Model tokens: {usage['input_tokens']} input, {usage['output_tokens']} output; provider cost USD {usage['cost_usd']}"])
    for question in report['questions']:
        lines.extend(['', '## ' + _literal(question['question']), '',
                      'Source inspection: ' + _literal(question['inspection_status']), ''])
        lines.extend('- Requirement: ' + _literal(r) for r in question['requirements'])
        if not question['evidence']:
            lines.extend(['', humanize('No exportable quotations at this checkpoint.')])
        for item in question['evidence']:
            lines.extend(['', f"### {_literal(item['title'])} — PDF page {item['page']}", '',
                          '> ' + _literal(item['quote']), '',
                          'Binding: ' + item['binding_status'],
                          'Evidence ID: ' + _literal(item['evidence_id']),
                          'Source ID: ' + _literal(item['source_id']),
                          'Source URI: ' + _literal(item['uri']),
                          'Source SHA256: ' + _literal(item['source_sha256'])])
        lines.extend(['', 'Checkpoint evidence IDs: ' + (', '.join(_literal(i) for i in question['evidence_ids']) or 'none')])
        lines.extend('- Gap: ' + _literal(gap) for gap in question['gaps'])
    if report.get('artifacts'):
        lines.extend(['', '## Research artifacts', ''])
        for artifact in report['artifacts']:
            lines.extend(['### '+_literal(artifact['title']), _literal(artifact['status']), _literal(artifact['text']),
                          'Evidence: '+', '.join(_literal(e) for e in artifact['evidence_ids']), ''])
    lines.extend(['', '## Execution checkpoints', ''])
    for step in task['steps']:
        lines.append(f"- {_literal(step['title'])}: {_literal(step['status'])}; attempts {step['attempts']}")
    lines.extend(['', '## Execution history', ''])
    for event in task['events']:
        lines.append(f"- {_literal(event['at'])}: {_literal(event['message'])}")
    return '\n'.join(lines) + '\n'
