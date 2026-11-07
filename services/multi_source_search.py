"""Bounded official metadata API adapters with explicit partial failures."""
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
import requests
from services.academic_humanizer import humanize
from schemas.multi_source_search import SearchHit, SearchGroup, SearchBatch, SourceSearch


def safe_url(value):
    if not isinstance(value, str):
        return ''
    parsed = urlsplit(value)
    return value if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password else ''


def doi_value(value):
    value = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', str(value or '').strip(), flags=re.I).lower()
    return value if re.fullmatch(r'10\.\d{4,9}/[^\s]+', value) else None


class ProviderResponseError(ValueError):
    def __init__(self, status, retry_after):
        super().__init__(f'Provider returned HTTP {status}; retry later.')
        self.retry_after = retry_after


def fetch_json(url, params, headers=None):
    started = time.monotonic()
    with requests.get(url, params=params, headers={'User-Agent':'AutoResearch-Agent/1.0', **(headers or {})},
                      timeout=(5, 15), stream=True, allow_redirects=False) as response:
        if response.status_code != 200:
            from email.utils import parsedate_to_datetime
            raw = response.headers.get('Retry-After', '30')
            try:
                delay = max(30, int(raw))
            except ValueError:
                try:
                    delay = max(30, int(parsedate_to_datetime(raw).timestamp()-time.time()))
                except (ValueError, TypeError, OverflowError):
                    delay = 60
            raise ProviderResponseError(response.status_code, min(delay, 86400))
        content = bytearray()
        for chunk in response.iter_content(65536):
            if time.monotonic()-started > 20 or len(content)+len(chunk) > 2_000_000:
                raise ValueError('Provider response exceeded size or time limit')
            content.extend(chunk)
    return json.loads(content)


def search_source(source, query, limit):
    if source == 'arxiv':
        from tools.arxiv_search import search_arxiv
        import arxiv
        try:
            rows = search_arxiv(query, max_results=limit, num_retries=0)
        except arxiv.ArxivError as error:
            raise ValueError('arXiv unavailable') from error
        return [SearchHit(source=source, source_id=row['entry_id'], title=row['title'],
                         authors=row['authors'], url=safe_url(row['entry_id'].replace('http:', 'https:')),
                         pdf_url=safe_url(row['pdf_url'].replace('http:', 'https:')), rank=index+1)
                for index, row in enumerate(rows)]
    if source == 'crossref':
        rows = fetch_json('https://api.crossref.org/works', {'query.bibliographic':query, 'rows':limit})['message']['items']
    elif source == 'openalex':
        headers = {'Authorization':'Bearer '+os.environ['OPENALEX_API_KEY']} if os.getenv('OPENALEX_API_KEY') else {}
        rows = fetch_json('https://api.openalex.org/works', {'search':query, 'per-page':limit}, headers)['results']
    else:
        headers = {'x-api-key':os.environ['SEMANTIC_SCHOLAR_API_KEY']} if os.getenv('SEMANTIC_SCHOLAR_API_KEY') else {}
        rows = fetch_json('https://api.semanticscholar.org/graph/v1/paper/search',
                          {'query':query, 'limit':limit, 'fields':'title,authors,year,url,externalIds,openAccessPdf'}, headers)['data']
    hits = []
    for index, row in enumerate(rows[:limit]):
        if source == 'crossref':
            title = (row.get('title') or [''])[0]
            doi = doi_value(row.get('DOI'))
            source_id = row.get('DOI') or row.get('URL')
            authors = [' '.join(filter(None, [a.get('given'), a.get('family')])) for a in row.get('author', [])]
            url, pdf, year = row.get('URL'), '', None
        elif source == 'openalex':
            title, doi, source_id = row.get('title'), doi_value(row.get('doi')), row.get('id')
            authors = [a['author']['display_name'] for a in row.get('authorships', [])]
            location = row.get('best_oa_location') or {}
            url, pdf, year = row.get('id'), location.get('pdf_url'), row.get('publication_year')
        else:
            title, doi, source_id = row.get('title'), doi_value((row.get('externalIds') or {}).get('DOI')), row.get('paperId')
            authors = [a['name'] for a in row.get('authors', [])]
            url, pdf, year = row.get('url'), (row.get('openAccessPdf') or {}).get('url'), row.get('year')
        if not title or not source_id:
            continue
        hits.append(SearchHit(source=source, source_id=str(source_id), title=title, authors=authors,
            doi=doi, doi_status=('crossref_registered' if source == 'crossref' else 'source_reported') if doi else 'missing',
            url=safe_url(url), pdf_url=safe_url(pdf), year=year, rank=index+1))
    return hits


def multi_search(run_id, request, adapter=search_source):
    outcomes, groups = [], {}
    for source in request.sources:
        start = datetime.now(timezone.utc)
        try:
            hits = adapter(source, request.query, request.limit)
            outcome = SourceSearch(source=source, status='success', started_at=start,
                                   finished_at=datetime.now(timezone.utc), hits=hits)
        except ProviderResponseError as error:
            outcome = SourceSearch(source=source, status='failed', started_at=start,
                finished_at=datetime.now(timezone.utc), error=str(error), retry_after_seconds=error.retry_after)
        except (requests.RequestException, ValueError, KeyError, TypeError):
            # Provider exception strings can contain credential-bearing request URLs.
            outcome = SourceSearch(source=source, status='failed', started_at=start,
                finished_at=datetime.now(timezone.utc), error='Source unavailable or returned invalid metadata. Retry later.')
        outcomes.append(outcome)
        for hit in outcome.hits:
            key = 'doi:'+hit.doi if hit.doi else source+':'+hit.source_id
            groups.setdefault(key, []).append(hit)
    ordered = sorted(groups.items(), key=lambda pair: (min(hit.rank for hit in pair[1]), pair[0]))
    return SearchBatch(scope=humanize(SearchBatch.model_fields['scope'].default), run_id=run_id, request=request, sources=outcomes,
                       groups=[SearchGroup(key=key, records=records) for key, records in ordered])
