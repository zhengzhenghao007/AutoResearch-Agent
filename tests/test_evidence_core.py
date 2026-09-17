import pytest

from schemas.research import Source, Document, Page, Evidence, Claim, PaperEvidence
from services.evidence_review import review_paper


def paper():
    quote = 'We evaluate our method on two public datasets.'
    return PaperEvidence(
        document=Document(source=Source(id='s1', title='Paper', uri='upload:test.pdf', sha256='a'*64),
                          pages=[Page(number=1, text=quote)], total_pages=1),
        evidence=[Evidence(id='e1', source_id='s1', page=1, quote=quote)],
        claims=[Claim(id='c1', text=quote, category='experiment', evidence_ids=['e1'])],
        missing_fields=['problem', 'method', 'dataset', 'result', 'limitation', 'future_work'],
    )


def test_valid_literal_report():
    assert review_paper(paper()).approved


@pytest.mark.parametrize('change', ['page', 'quote', 'source', 'claim', 'reference'])
def test_rejects_unsupported_reports(change):
    p = paper()
    if change == 'page': p.evidence[0].page = 2
    if change == 'quote': p.evidence[0].quote = 'Invented experimental accuracy is 99 percent.'
    if change == 'source': p.evidence[0].source_id = 'other'
    if change == 'claim': p.claims[0].text = 'Our method beats every baseline.'
    if change == 'reference': p.claims[0].evidence_ids = ['missing']
    assert not review_paper(p).approved


def test_empty_evidence_is_not_approved():
    p = paper()
    p.claims = []
    p.evidence = []
    assert not review_paper(p).approved


def test_paper_cannot_become_user_experiment():
    p = paper()
    p.claims[0].claim_type = 'user_observation'
    assert not review_paper(p).approved


@pytest.mark.parametrize('missing', [[], ['problem'] * 6, ['problem', 'method', 'dataset', 'result', 'limitation', 'future_work', 'experiment']])
def test_rejects_inconsistent_missing_fields(missing):
    p = paper()
    p.missing_fields = missing
    assert not review_paper(p).approved


@pytest.mark.parametrize('origin', ['hypothesis', 'suggestion'])
def test_generated_ideas_cannot_be_experimental_observations(origin):
    p = paper()
    p.claims[0].claim_type = origin
    review = review_paper(p)
    assert not review.approved
    assert any('cannot be experimental observations' in issue for issue in review.issues)
