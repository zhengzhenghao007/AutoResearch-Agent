"""Deterministic chapter material with direct quotation and computation bindings."""
from services.academic_humanizer import humanize
import hashlib
import json

from schemas.research import ResearchRun
from schemas.manuscript_draft import ManuscriptDraft, DraftSection, DraftBlock, PaperBinding, ComputationBinding
from services.research_validation import validate_run
from services.experiment_statistics import build_experiment_statistics
from schemas.workspace import AssetBinding
from services.workspace import preview_workspace, _request


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
    assets = [item for item in run.workspace_items if item.kind in ('figure', 'table')]
    if assets:
        material['workspace_items'] = [item.model_dump(mode='json') for item in assets]
    digest = hashlib.sha256(json.dumps(material, ensure_ascii=False, sort_keys=True,
                                       separators=(',', ':')).encode('utf-8')).hexdigest()
    sections = {id:DraftSection(id=id,title=title,purpose=humanize(purpose),blocks=[]) for id,title,purpose in SECTIONS}
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
                text = humanize('No nonmissing observations for {column} in dataset {dataset}; no result can be drafted.').format(
                    column=column.name, dataset=dataset.title)
                kind = 'placeholder'
            else:
                text = humanize('For {name} in user dataset {dataset}, {count} values were observed '
                        'and {missing} were missing. The descriptive mean was {mean}; '
                        'minimum {minimum}, maximum {maximum}; sample standard deviation (n-1) '
                        '{sd}. '
                        'Unit: {unit}. '
                        'No missing values were imputed; sample independence and scientific validity are unverified.').format(
                            name=column.name, dataset=dataset.title, count=column.observed_count,
                            missing=column.missing_count, mean=column.mean, minimum=column.minimum,
                            maximum=column.maximum, sd=column.sample_standard_deviation or 'unavailable',
                            unit=column.unit if column.unit is not None else 'unspecified')
                kind = 'user_statistics'
            sections['user_results'].blocks.append(DraftBlock(id=f'data:{dataset.dataset_id}:{column.name}',
                                                              kind=kind,text=text,computation=binding))
    for item in assets:
        rendering = preview_workspace(run, _request(item))
        sections['user_results'].blocks.append(DraftBlock(id=f'asset:{item.id}', kind='research_asset',
            text=item.text or item.title,
            asset=AssetBinding(item_id=item.id, title=item.title, **rendering.model_dump())))
    for section in sections.values():
        if not section.blocks:
            text = (humanize('No user experimental observations were supplied. Add real data before drafting user results.')
                    if section.id == 'user_results' else
                    humanize('No saved paper evidence for {section}. Add and review sources; do not infer missing findings.').format(section=section.title.lower()))
            section.blocks.append(DraftBlock(id=f'missing:{section.id}',kind='placeholder',text=text))
    return ManuscriptDraft(scope=humanize(ManuscriptDraft.model_fields['scope'].default), run_id=run.id,topic=run.topic,input_sha256=digest,
                           sections=list(sections.values()),omitted_legacy_observation_claims=omitted,
                           statistics_scope=statistics.scope)
