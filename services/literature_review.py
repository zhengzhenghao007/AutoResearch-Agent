"""Read-only literature review material assembled from saved provenance."""
from services.academic_humanizer import humanize
from datetime import datetime, timezone
import hashlib
import json
from schemas.manuscript_draft import DraftSection
from schemas.research import Contract
from schemas.screening_report import ScreeningReport
from schemas.multi_source_search import SearchBatch
from services.manuscript_draft import build_manuscript_draft
from services.screening_report import build_screening_report
from services.search_history import search_history
from services.workspace import _escape
from services.review_protocol import get_protocol
from schemas.review_protocol import ReviewProtocol


class LiteraturePacket(Contract):
    run_id: str
    project_name: str
    goal: str
    input_sha256: str
    generated_at: datetime
    source_ids: list[str]
    sections: list[DraftSection]
    screening: ScreeningReport
    searches: list[SearchBatch]
    protocol: ReviewProtocol | None
    missing_requirements: list[str]
    scope: str = 'Quoted literature review material for researcher editing. Systematic-review completeness and scientific quality remain unassessed.'


def build_literature_packet(store, run_id, source_ids):
    run = store.load(run_id)
    known = {paper.document.source.id for paper in run.papers}
    if len(set(source_ids)) != len(source_ids) or not set(source_ids) <= known:
        raise ValueError('Select distinct existing paper sources')
    selected = set(source_ids) if source_ids else known
    draft = build_manuscript_draft(run)
    sections = []
    for section in draft.sections:
        if section.id == 'user_results':
            continue
        blocks = [block for block in section.blocks if block.paper and block.paper.source.id in selected]
        sections.append(section.model_copy(update={'blocks':blocks}))
    screening = build_screening_report(run)
    searches = search_history(store, run_id)
    protocols = get_protocol(store, run_id).revisions
    protocol = protocols[-1] if protocols else None
    missing = [
               'Screening decisions for multi-source metadata records and uploaded PDFs require reconciliation.',
               'A complete search strategy and reviewer assessment are required before systematic-review claims.']
    labels = {'question':'research question', 'inclusion_criteria':'inclusion criteria',
              'exclusion_criteria':'exclusion criteria', 'publication_range':'publication-date range',
              'search_strategy':'search strategy'}
    for field, label in labels.items():
        if protocol is None or not getattr(protocol, field):
            missing.append(f'Review protocol requires {label}.')
    if not searches:
        missing.append('No saved multi-database search batches are available.')
    if screening.counts.undecided:
        missing.append(f'{screening.counts.undecided} legacy candidates have no screening decision.')
    if any(not search.sources or any(source.status != 'success' for source in search.sources) for search in searches):
        missing.append('Some saved searches are incomplete or contain source failures.')
    if any(paper.document.truncated for paper in run.papers if paper.document.source.id in selected):
        missing.append('Selected papers include partial text extraction.')
    if not selected:
        missing.append('No parsed paper evidence is available.')
    source_list = [paper.document.source.id for paper in run.papers if paper.document.source.id in selected]
    material = {'protocol':protocol.model_dump(mode='json') if protocol else None,'goal':run.research_goal,'sources':source_list,'sections':[section.model_dump(mode='json') for section in sections],
                'screening':screening.model_dump(mode='json'),'searches':[search.model_dump(mode='json') for search in searches]}
    digest = hashlib.sha256(json.dumps(material,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return LiteraturePacket(scope=humanize(LiteraturePacket.model_fields['scope'].default), run_id=run.id,project_name=run.project_name or 'Research',goal=run.research_goal or '',
        input_sha256=digest,generated_at=datetime.now(timezone.utc),source_ids=source_list,sections=sections,
        screening=screening,searches=searches,protocol=protocol,missing_requirements=[humanize(item) for item in missing])


def render_literature_packet(packet):
    lines = ['# '+_escape(packet.project_name), '', packet.scope, '', 'Research goal', _escape(packet.goal or 'Unspecified'),
             '', 'Input SHA256', packet.input_sha256, '', '## Requirements to resolve']
    lines.extend('- '+_escape(item) for item in packet.missing_requirements)
    if packet.protocol:
        lines.extend(['', '## Review protocol', f'Revision {packet.protocol.revision} / {packet.protocol.saved_at.isoformat()}'])
        for field in ('question', 'inclusion_criteria', 'exclusion_criteria', 'publication_range', 'search_strategy'):
            lines.extend(['', field.replace('_', ' ').title(), _escape(getattr(packet.protocol, field) or 'Unspecified')])
    for section in packet.sections:
        lines.extend(['', '## '+_escape(section.title)])
        if not section.blocks:
            lines.append(humanize('No extracted quotations for this category in the selected sources.'))
        for block in section.blocks:
            lines.extend(['', _escape(block.text)])
            for evidence in block.paper.evidence:
                lines.append(f'- {_escape(block.paper.source.title)} / page {evidence.page} / evidence {_escape(evidence.id)}')
    lines.extend(['', '## Search history'])
    for batch in packet.searches:
        lines.append(f'- {_escape(batch.request.query)} / {batch.created_at.isoformat()} / {_escape(batch.id)}')
        lines.append('  '+_escape(batch.scope))
        for source in batch.sources:
            lines.append(f'  - {source.source} / {source.status} / {len(source.hits)} records')
    lines.extend(['', '## Screening history'])
    for item in packet.screening.items:
        reason = item.latest.reason if item.latest else 'No decision recorded'
        lines.append(f'- {_escape(item.candidate.title)} / {item.status} / {_escape(reason)}')
    return '\n'.join(lines)+'\n'
