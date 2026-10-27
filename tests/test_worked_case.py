"""The public worked example must remain replayable through the real services."""
import json
from pathlib import Path
from schemas.research import ResearchRun
from services.research_validation import validate_run
from services.citation_registry import build_citation_registry
from services.manuscript_draft import build_manuscript_draft
from services.manuscript import get_manuscript
from services.research_store import ResearchStore

CASE = Path(__file__).resolve().parents[1] / 'examples/conformal-prediction'


def read(name):
    return json.loads((CASE / name).read_text(encoding='utf-8'))


def test_case_has_licensed_sources_and_reproducible_evidence_and_draft(tmp_path):
    manifest = read('sources.json')
    run = ResearchRun.model_validate(read('outputs/run.json'))
    validate_run(run)
    assert {p.document.source.sha256 for p in run.papers} == {p['sha256'] for p in manifest['papers']}
    assert manifest['license'] == 'CC-BY-4.0'
    for paper in run.papers:
        pages = {p.number: p.text for p in paper.document.pages}
        assert all(e.quote in pages[e.page] for e in paper.evidence)
    assert build_citation_registry(run).model_dump(mode='json') == read('outputs/citations.json')
    assert build_manuscript_draft(run).model_dump(mode='json') == read('outputs/draft.json')
    store = ResearchStore(tmp_path)
    store.save(run)
    (tmp_path / 'manuscripts').mkdir()
    (tmp_path / 'manuscripts' / f'{run.id}.json').write_bytes((CASE / 'outputs/manuscript-state.json').read_bytes())
    manuscript = get_manuscript(store, run.id)
    assert len(manuscript.revisions) == 1
    assert not manuscript.approvals and not manuscript.reviews
    assert not run.experiments
    execution = read('outputs/execution.json')
    assert execution['model_calls'] == 0 and execution['human_approval'] is False
    assert sum(s.get('quotes', 0) for s in execution['steps']) == sum(len(p.evidence) for p in run.papers)
