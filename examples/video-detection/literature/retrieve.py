"""Replay provider searches and verify a curated arXiv reading set. Run with the repo venv."""
import hashlib
import json
import re
import subprocess
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from schemas.multi_source_search import SearchRequest
from services.multi_source_search import multi_search

# Author-selected seeds from topical web searches. First six receive full-text review.
SEEDS = {
    '2404.15955': 'Image-to-video transfer, recompression and few-shot adaptation.',
    '2405.19707': 'GenVideo cross-generator and degraded-video evaluations.',
    '2403.16638': 'Joint appearance and optical-flow evidence on GVD.',
    '2501.11340': 'Caption-paired benchmark for evaluating cross-generator transfer.',
    '2503.06624': 'Scene diversity and domain variation as sources of evaluation shift.',
    '2607.00948': 'Benchmark confounds and shortcut learning in motion-based detectors.',
    '2508.00701': 'Training-free second-order temporal-difference baseline, D3.',
    '2512.10248': 'Evaluation after removing visible watermark cues.',
    '2604.04634': 'Impact of input resolution and native-scale evidence.',
    '2405.15343': 'Large-scale motion-feature learning for fake video detection.',
    '2506.16802': 'Augmentation choices for generalization across generators.',
    '2601.11035': 'Multi-detector benchmark and harmonized evaluation.',
    '2405.04133': 'Local and global temporal inconsistencies as forensic features.',
    '2505.12620': 'Multimodal detector with explanations.',
    '2605.05895': 'Temporal residuals and semantic trajectories across generators.',
    '2506.14827': 'Explainable reasoning for generated video detection.',
    '2607.04607': 'Causal approach to suppressing nuisance factors.',
    '2610.35148': 'Efficiency of temporally sliced detection.',
    '2607.10787': 'Survey of visual and language-based approaches.',
    '2508.21052': 'Partially generated video manipulations and localization.',
    '2307.07494': 'Adjacent face-manipulation study of cross-dataset transfer.',
    '2002.12749': 'Adjacent face-deepfake study of adversarial detector vulnerabilities.',
    '2004.14491': 'Adjacent face-deepfake study of behavioral and appearance cues.',
}
CACHE = ROOT / '.verification/video-pdfs'
def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name', '').startswith('citation_'):
            self.fields.setdefault(attrs['name'], []).append(attrs['content'])

def retrieve(item):
    url = 'https://arxiv.org/abs/' + item
    response = requests.get(url, timeout=25)
    response.raise_for_status()
    meta = Meta()
    meta.feed(response.text)
    f = meta.fields
    date = f['citation_date'][0]
    authors = [' '.join(reversed(a.split(', ', 1))) for a in f['citation_author']]
    assert f['citation_arxiv_id'][0] == item
    return dict(id='arxiv-'+item, arxiv_id=item, url=url, title=' '.join(f['citation_title'][0].split()),
                authors=authors, year=int(date[:4]), date=date, relevance=SEEDS[item])

def pdf(item):
    path = CACHE / (item+'.pdf')
    url = 'https://arxiv.org/pdf/'+item
    if not path.exists():
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            buf = bytearray()
            for chunk in response.iter_content(65536):
                buf.extend(chunk)
                if len(buf) > 20*1024*1024:
                    raise ValueError('PDF exceeds parser limit')
        if not buf.startswith(b'%PDF-'):
            raise ValueError('Unexpected response format')
        path.write_bytes(buf)
    data = path.read_bytes()
    parsed = subprocess.run([sys.executable, '-m', 'services.pdf_worker', '60'], input=data,
                            cwd=ROOT, capture_output=True, check=True, timeout=45)
    doc = json.loads(parsed.stdout)
    write(path.with_suffix('.pages.json'), doc)
    return dict(arxiv_id=item, url=url, sha256=hashlib.sha256(data).hexdigest(),
                total_pages=doc['total_pages'], extracted_pages=len(doc['pages']))

def search():
    req = SearchRequest(query='AI-generated video detection', limit=20,
                        sources=['arxiv','openalex','semantic_scholar','crossref'])
    batch = multi_search('video-detection-literature', req)
    write(HERE/'queries.json', batch.model_dump(mode='json'))

def screen():
    """Audit each first-page hit against the curated set without guessing identities."""
    papers = json.loads((HERE/'papers.json').read_text(encoding='utf-8'))
    batch = json.loads((HERE/'queries.json').read_text(encoding='utf-8'))
    def title_key(title):
        return re.sub(r'[^a-z0-9]+', '', title.lower())
    indexed = {title_key(p['title']): p for p in papers}
    seen, decisions = set(), []
    for source in batch['sources']:
        for hit in source['hits']:
            key = title_key(hit['title'])
            selected = indexed.get(key)
            if selected:
                reason = ('Additional record for an included title' if key in seen else
                          'Matches an included primary record by normalized title')
                seen.add(key)
            else:
                reason = 'Outside the curated primary-record set; no full-text eligibility decision'
            decisions.append(dict(provider=source['source'], rank=hit['rank'], title=hit['title'],
                                  source_id=hit['source_id'], matched_id=selected['id'] if selected else None,
                                  reason=reason))
    write(HERE/'screening.json', decisions)

if __name__ == '__main__':
    CACHE.mkdir(parents=True, exist_ok=True)
    if 'screen' in sys.argv:
        screen()
    elif 'add' in sys.argv:
        papers = {p['arxiv_id']:p for p in json.loads((HERE/'papers.json').read_text(encoding='utf-8'))}
        write(HERE/'papers.json', [papers[i] if i in papers else retrieve(i) for i in SEEDS])
    elif 'search' in sys.argv:
        search()
    else:
        papers, coverage = [], []
        for i in SEEDS:
            try:
                papers.append(retrieve(i))
                write(HERE/'papers.json', papers)
                print(i, papers[-1]['title'], flush=True)
            except Exception as exc:
                print(i, str(exc), flush=True)
            time.sleep(1)
        # Also retain the audit of a candidate excluded after its authoritative title was verified.
        for i in [*list(SEEDS)[:6], '2406.19568']:
            try:
                coverage.append(pdf(i))
            except Exception as exc:
                coverage.append(dict(arxiv_id=i,error=str(exc)))
            write(HERE/'fulltext-coverage.json',coverage)
