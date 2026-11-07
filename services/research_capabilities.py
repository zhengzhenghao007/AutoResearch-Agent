"""Bounded extractive research stages. Proposals never become reported findings."""
import re
from collections import Counter
from schemas.research import CATEGORIES
from schemas.research_tasks import TaskResult, TaskArtifact


def terms(text):
    words = set(re.findall(r'[a-z0-9]{3,}', text.lower()))
    for phrase in re.findall(r'[\u4e00-\u9fff]+', text):
        words.update(phrase[i:i+2] for i in range(max(1, len(phrase)-1)))
    return words - {'the','and','for','with','what','how','are','this','that','paper'}


def outlier_samples(references):
    """Tukey fences with median-of-halves quartiles, excluding the odd middle sample."""
    from fractions import Fraction
    from statistics import median
    if len(references) < 4:
        return []
    values = sorted(Fraction(row.value) for row in references)
    half = len(values) // 2
    lower = median(values[:half])
    upper = median(values[-half:])
    margin = 3 * (upper - lower) / 2
    return [row for row in references if not lower - margin <= Fraction(row.value) <= upper + margin]


def execute_capability(executor, run, task, step, deadline):
    def check():
        if executor.clock() >= deadline:
            raise TimeoutError()
    check()
    if step.tool == 'research_retrieve':
        # Round-robin across papers/categories prevents a verbose first paper consuming the budget.
        query = terms(' '.join([task.question] + [r for q in task.subquestions for r in q.requirements]))
        buckets, known, gaps = [], set(), []
        for paper in run.papers:
            check()
            by_id = {e.id:e for e in paper.evidence}
            for category in CATEGORIES:
                ids = list(dict.fromkeys(e for c in paper.claims if c.category == category and c.claim_type == 'paper_report' for e in c.evidence_ids if e in by_id))
                ids.sort(key=lambda eid: (-len(query & terms(by_id[eid].quote)), eid))
                if ids: buckets.append(ids)
        selected=[]
        limit=min(100, task.budget.max_evidence-task.usage.evidence)
        while buckets and len(selected)<limit:
            next_buckets=[]
            for bucket in buckets:
                check()
                eid=bucket.pop(0)
                if eid not in known and len(selected)<limit:
                    selected.append(eid);known.add(eid)
                if bucket: next_buckets.append(bucket)
            buckets=next_buckets
        total={e for p in run.papers for c in p.claims if c.claim_type=='paper_report' for e in c.evidence_ids}
        if total-known:
            gaps.append(f'Evidence budget/context limit selected {len(selected)} of {len(total)} candidate quotations; omitted evidence was not analyzed.')
        if not selected: gaps.append('No saved evidence. Search for literature or upload readable papers before synthesis.')
        return TaskResult(evidence_ids=selected,gaps=gaps,summary='Category-balanced paper coverage, ranked by English terms and Chinese character pairs within each category. This selection is not semantic relevance verification.')

    inspection=next((s.result for s in task.steps if s.tool=='inspect_sources' and s.result),None)
    checked=set(inspection.evidence_ids if inspection else [])
    # Reject any ambiguous globally duplicated ID even when a caller bypasses the normal inspector.
    counts=Counter(e.id for p in run.papers for e in p.evidence)
    checked={eid for eid in checked if counts[eid]==1}
    evidence={e.id:e for p in run.papers for e in p.evidence if e.id in checked}
    artifacts=[];gaps=[]
    def add(kind,title,text,ids=(),sources=(),status='needs_review'):
        check()
        artifacts.append(TaskArtifact(kind=kind,title=title,text=text,evidence_ids=list(dict.fromkeys(ids)),source_ids=list(dict.fromkeys(sources)),status=status))
    if step.tool == 'evidence_matrix':
        for paper in run.papers:
            check()
            for category in CATEGORIES:
                ids=list(dict.fromkeys(eid for c in paper.claims if c.category==category and c.claim_type=='paper_report' for eid in c.evidence_ids if eid in checked))
                if ids:
                    add('matrix',f'{paper.document.source.title} / {category}', '\n'.join(evidence[eid].quote for eid in ids),ids,[paper.document.source.id],'quoted')
                else:
                    gaps.append(f'{paper.document.source.title}: no selected checked evidence for {category}.')
    elif step.tool == 'brainstorm':
        for paper in run.papers:
            for claim in paper.claims:
                check()
                ids=[eid for eid in claim.evidence_ids if eid in checked]
                if claim.category not in ('limitation','future_work') or claim.claim_type!='paper_report' or not ids: continue
                if len(artifacts)>=12:
                    gaps.append('Investigation proposals capped at 12; additional limitations omitted.')
                    break
                quote=evidence[ids[0]].quote
                add('hypothesis',f'Investigate: {paper.document.source.title}',
                    f'Author-reported basis: {quote}\nResearch question: Under which conditions does this limitation hold, and which intervention changes it?\n'
                    'Validation plan: reproduce the reported baseline, vary one stated assumption at a time, define the metric and data split before testing, and include negative results. '
                    'Falsification: reject the candidate explanation if the intervention does not improve the prespecified metric under the same protocol. '
                    'Novelty and feasibility are unverified; search related work and compare experimental settings before adopting this direction.',ids,[paper.document.source.id],'proposal')
        if not artifacts: gaps.append('No checked author-reported limitations or future directions; no grounded hypothesis proposed.')
    elif step.tool == 'literature_review':
        for category in CATEGORIES:
            ids=list(dict.fromkeys(eid for p in run.papers for c in p.claims if c.category==category and c.claim_type=='paper_report' for eid in c.evidence_ids if eid in checked))
            if ids:
                sources=[evidence[eid].source_id for eid in ids]
                add('review',category.replace('_',' ').title(), '\n'.join(f'[{evidence[eid].source_id}, p.{evidence[eid].page}] {evidence[eid].quote}' for eid in ids),ids,sources,'quoted')
        add('quality','Review scope','This is extractive, selected-paper review material. It does not establish consensus, resolve contradictions or certify a systematic review. Use the saved review protocol and screening history; model synthesis is a separate optional operation.')
    elif step.tool == 'supervise':
        prior_gaps=list(dict.fromkeys(g for s in task.steps if s.result for g in s.result.gaps))
        gaps.extend(prior_gaps)
        if not checked:
            gaps.append('No validated quotations available; search additional literature or repair PDF extraction.')
        for paper in run.papers:
            check()
            doc=paper.document
            if doc.truncated: gaps.append(f'Incomplete page extraction: {doc.source.title} ({len(doc.pages)}/{doc.total_pages}).')
            if doc.ocr_pages: gaps.append(f'Visually verify OCR quotations: {doc.source.title}.')
        add('quality','Research quality checkpoint', f'{len(checked)} literal quotation bindings checked across {len(run.papers)} saved papers. '
            'Semantic support, scientific correctness, novelty and experimental reproducibility remain unassessed. '
            'No hypothesis has been promoted to an experimental finding.',checked,[p.document.source.id for p in run.papers])
        for gap in list(dict.fromkeys(gaps))[:30]:
            add('quality','Next action',gap+' Review the relevant source, expand the search or revise the research plan.')
        if run.experiments:
            from services.experiment_statistics import build_experiment_statistics
            report=build_experiment_statistics(run)
            check()
            for dataset in report.datasets:
                for col in dataset.columns:
                    add('experiment',f'{dataset.title} / {col.name}',
                        f'Dataset {dataset.dataset_id}; SHA256 {dataset.sha256}; algorithm {report.algorithm}. '
                        f'n={col.observed_count}; missing={col.missing_count}; mean={col.mean}; min={col.minimum}; max={col.maximum}; sample SD={col.sample_standard_deviation}. '
                        'Descriptive observations only; no causal or significance claim. '+' '.join(col.warnings),sources=[dataset.dataset_id],status='computed')
                    flagged = outlier_samples(col.references)
                    if flagged:
                        examples = ', '.join(f'{row.sample_id}={row.value}' for row in flagged[:10])
                        add('experiment', f'Inspect atypical observations: {col.name}',
                            f'{len(flagged)} of {col.observed_count} observations outside 1.5 × IQR fences '
                            f'(median-of-halves quartiles). Up to 10 sample IDs: {examples}. '
                            'Check calibration, units and protocol before interpreting or excluding any observation.',
                            sources=[dataset.dataset_id], status='needs_review')
        else:
            add('quality','Experimental validation pending','No user experimental dataset supplied. Upload observations and specify controls, metrics and a protocol to evaluate candidate hypotheses.')
    else:
        raise ValueError('Unsupported research capability')
    return TaskResult(evidence_ids=sorted(checked),gaps=list(dict.fromkeys(gaps)),artifacts=artifacts,
                      summary=f'{step.tool.replace("_"," ")}: {len(artifacts)} traceable research artifacts. Scientific validation remains unassessed.')
