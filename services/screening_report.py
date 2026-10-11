"""Derive screening history without rewriting snapshots or selecting papers."""
from schemas.research import ResearchRun
from schemas.screening_report import ScreeningCounts, ScreeningItem, ScreeningReport
from services.research_validation import validate_run


def build_screening_report(run: ResearchRun) -> ScreeningReport:
    run = ResearchRun.model_validate(run.model_dump())
    validate_run(run)
    histories = {candidate.id: [] for candidate in run.candidates}
    for event in run.candidate_decisions:
        histories[event.candidate_id].append(event)
    selected = set(run.selected_ids)
    counts = dict(total=len(run.candidates), include=0, exclude=0, undecided=0, selected=len(selected))
    items = []
    for candidate in run.candidates:
        history = histories[candidate.id]
        latest = history[-1] if history else None
        status = latest.decision if latest else 'undecided'
        counts[status] += 1
        chosen = candidate.id in selected
        notice = None
        if status == 'exclude' and chosen:
            notice = 'excluded_but_selected'
        elif status == 'include' and not chosen:
            notice = 'included_but_not_selected'
        elif status == 'undecided' and chosen:
            notice = 'selected_without_decision'
        items.append(ScreeningItem(candidate=candidate, status=status, selected_for_analysis=chosen,
                                   latest=latest, history=history, selection_notice=notice))
    return ScreeningReport(run_id=run.id, topic=run.topic, counts=ScreeningCounts(**counts), items=items)
