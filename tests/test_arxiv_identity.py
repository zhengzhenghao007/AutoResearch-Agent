"""Equivalent links collapse; revision identity and download boundaries remain explicit."""
import hashlib
import pytest
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


def search(tmp_path, urls):
    return EvidenceWorkflow(store=ResearchStore(tmp_path), search=lambda *a, **k: [
        {'title': f'Paper {i}', 'pdf_url': url} for i, url in enumerate(urls)]).search('navigation')


def test_search_collapses_equivalent_arxiv_links(tmp_path):
    run = search(tmp_path, ['http://arxiv.org/pdf/2401.12345v2.pdf',
        'https://arxiv.org/abs/2401.12345v2', 'https://arxiv.org/pdf/2401.12345v2'])
    assert len(run.candidates) == 1
    item = run.candidates[0]
    assert item.title == 'Paper 0'
    assert item.pdf_url == 'https://arxiv.org/pdf/2401.12345v2'
    assert item.id == hashlib.sha256(item.pdf_url.encode()).hexdigest()[:16]


def test_search_preserves_distinct_revisions_and_unversioned_link(tmp_path):
    run = search(tmp_path, [f'https://arxiv.org/pdf/2401.12345{s}' for s in ('', 'v1', 'v2')])
    assert len(run.candidates) == 3


def test_legacy_identifiers_remain_distinct(tmp_path):
    run = search(tmp_path, ['http://arxiv.org/abs/hep-th/9901001v1',
        'https://arxiv.org/pdf/hep-th/9901001v1.pdf',
        'https://arxiv.org/pdf/math.GT/0309136'])
    assert len(run.candidates) == 2
    assert run.candidates[0].pdf_url == 'https://arxiv.org/pdf/hep-th/9901001v1'


@pytest.mark.parametrize('url', [
    'https://arxiv.org.evil.test/pdf/2401.12345',
    'https://user@arxiv.org/pdf/2401.12345',
    'https://arxiv.org:443/pdf/2401.12345',
    'https://arxiv.org/pdf/2401.12345?download=1',
    'https://arxiv.org/pdf/2401.12345#x',
    'https://arxiv.org/pdf/../2401.12345',
    'https://arxiv.org/pdf/%32%3401.12345',
])
def test_search_does_not_rewrite_unsafe_links_into_allowed_urls(tmp_path, url):
    run = search(tmp_path, [url, 'https://arxiv.org/pdf/2401.12345'])
    assert len(run.candidates) == 2
    assert run.candidates[0].pdf_url == url
