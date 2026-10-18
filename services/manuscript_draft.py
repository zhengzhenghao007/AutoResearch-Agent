"""Deterministic chapter material with direct quotation and computation bindings."""
import hashlib
import json

from schemas.research import ResearchRun
from schemas.manuscript_draft import ManuscriptDraft, DraftSection, DraftBlock, PaperBinding, ComputationBinding
from services.research_validation import validate_run
from services.experiment_statistics import build_experiment_statistics


SECTIONS = (
    ('background', 'Background', 'Introduce author-reported problems from the selected sources.'),
    ('reported_methods', 'Reported methods', 'Keep methods, datasets and experiments attributed to their papers.'),
    ('reported_findings', 'Reported findings', 'Present reported paper outcomes separately from user observations.'),
    ('user_results', 'User observations', 'Describe uploaded observations without inferring causality or significance.'),
    ('limitations', 'Limitations and future directions', 'Retain author-reported limitations and future plans, not new findings.'),
)
CATEGORY_SECTION = {'problem':'background', 'method':'reported_methods', 'dataset':'reported_methods',
                    'experiment':'reported_methods', 'result':'reported_findings',
                    'limitation':'limitations', 'future_work':'limitations'}


def build_manuscript_draft(run: ResearchRun) -> ManuscriptDraft:
    run = ResearchRun.model_validate(run.model_dump())
    validate_run(run)
    statistics = build_experiment_statistics(run)
    material = {'topic':run.topic, 'papers':[p.model_dump(mode='json') for p in run.papers],
                'experiments':[d.model_dump(mode='json') for d in run.experiments]}
    digest = hashlib.sha256(json.dumps(material, ensure_ascii=False, sort_keys=True,
                                       separators=(',', ':')).encode('utf-8')).hexdigest()
    sections = {id:DraftSection(id=id,title=title,purpose=purpose,blocks=[]) for id,title,purpose in SECTIONS}
    omitted = 0
    for paper in run.papers:
        evidence = {e.id:e for e in paper.evidence}
        for claim in paper.claims:
            if claim.claim_type != 'paper_report':
                omitted += 1
                continue
            sections[CATEGORY_SECTION[claim.category]].blocks.append(DraftBlock(
                id=f'paper:{claim.id}',kind='paper_claim',text=claim.text,
                paper=PaperBinding(claim_id=claim.id,source=paper.document.source,
                                   evidence=[evidence[id] for id in claim.evidence_ids],
                                   parsed_pages=len(paper.document.pages),total_pages=paper.document.total_pages,
                                   truncated=paper.document.truncated)))
    for dataset in statistics.datasets:
        for column in dataset.columns:
            binding = ComputationBinding(dataset_id=dataset.dataset_id,sha256=dataset.sha256,
                                         title=dataset.title,column=column)
            if column.observed_count == 0:
                text = f'No nonmissing observations for {column.name} in dataset {dataset.title}; no result can be drafted.'
                kind = 'placeholder'
            else:
                text = (f'For {column.name} in user dataset {dataset.title}, {column.observed_count} values were observed '
                        f'and {column.missing_count} were missing. The descriptive mean was {column.mean}; '
                        f'minimum {column.minimum}, maximum {column.maximum}; sample standard deviation (n-1) '
                        f'{column.sample_standard_deviation if column.sample_standard_deviation is not None else "unavailable"}. '
                        f'Unit: {column.unit if column.unit is not None else "unspecified"}. '
                        'No missing values were imputed; sample independence and scientific validity are unverified.')
                kind = 'user_statistics'
            sections['user_results'].blocks.append(DraftBlock(id=f'data:{dataset.dataset_id}:{column.name}',
                                                              kind=kind,text=text,computation=binding))
    for section in sections.values():
        if not section.blocks:
            text = ('No user experimental observations were supplied. Add real data before drafting user results.'
                    if section.id == 'user_results' else
                    f'No saved paper evidence for {section.title.lower()}. Add and review sources; do not infer missing findings.')
            section.blocks.append(DraftBlock(id=f'missing:{section.id}',kind='placeholder',text=text))
    return ManuscriptDraft(run_id=run.id,topic=run.topic,input_sha256=digest,
                           sections=list(sections.values()),omitted_legacy_observation_claims=omitted,
                           statistics_scope=statistics.scope)
