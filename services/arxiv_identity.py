"""Conservative arXiv link normalization; explicit revisions are never merged."""
import re

# Keep the downloader's accepted identifier grammar. Do not decode paths or
# discard query/fragment/authority components to turn untrusted URLs into trusted ones.
_LINK = re.compile(
    r'https?://arxiv\.org/(?:abs|pdf)/'
    r'(?P<identifier>(?:[0-9]{4}\.[0-9]{4,5}|[a-z-]+(?:\.[A-Z]{2})?/[0-9]{7})(?:v[0-9]+)?)'
    r'(?:\.pdf)?'
)


def canonical_arxiv_pdf_url(url: str) -> str:
    """Normalize recognized links only; unknown URLs remain subject to download validation."""
    match = _LINK.fullmatch(url)
    return f'https://arxiv.org/pdf/{match.group("identifier")}' if match else url


def explicit_arxiv_revision_id(uri: str) -> str | None:
    """Only a revision explicitly present in a recognized URI is known."""
    match = _LINK.fullmatch(uri)
    if match and re.search(r'v[0-9]+$', match.group('identifier')):
        return match.group('identifier')
    return None
