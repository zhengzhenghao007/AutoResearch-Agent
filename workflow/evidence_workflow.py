"""Additive research loop, independent of the legacy ReaderPipeline."""
import hashlib
from uuid import uuid4
from schemas.research import Candidate, ResearchRun, Review
from services.paper_processing import PaperProcessor
from services.evidence_extraction import EvidenceExtractor
from services.evidence_review import review_paper
from services.literature_synthesis import build_suggestions, synthesize
from services.research_store import ResearchStore


class EvidenceWorkflow:
    def __init__(self, store=None, processor=None, extractor=None, search=None):
        self.store = store or ResearchStore()
        self.processor = processor or PaperProcessor()
        self.extractor = extractor or EvidenceExtractor()
        if search is None:
            from tools.arxiv_search import search_arxiv
            search = search_arxiv
        self.search_source = search

    def _new(self, topic):
        return ResearchRun(id=uuid4().hex, topic=topic, plan=[
            f'Define scope and search literature for: {topic}',
            'Review candidates and explicitly choose relevant papers.',
            'Extract page-level quotations and mark missing evidence.',
            'Compare supported reports; label suggestions and coverage gaps.',
            'Review sources; researcher evaluates relevance and scientific validity.',
        ])

    def search(self, topic, max_results=5):
        run = self._new(topic)
        if not 1 <= max_results <= 20:
            raise ValueError('max_results must be 1..20')
        seen = set()
        for item in self.search_source(topic, max_results=max_results):
            url = item['pdf_url']
            # arXiv feeds sometimes supply HTTP even though HTTPS is supported.
            if url.startswith('http://arxiv.org/'):
                url = 'https://' + url[len('http://'):]
            identity = hashlib.sha256(url.encode()).hexdigest()[:16]
            if identity not in seen:
                run.candidates.append(Candidate(id=identity, title=item['title'], pdf_url=url, summary=item.get('summary', ''), authors=item.get('authors', [])))
                seen.add(identity)
        self.store.save(run)
        return run

    def _finish(self, run):
        issues = [f'{p.document.source.title}: {issue}' for p in run.papers for issue in review_paper(p).issues]
        run.review = Review(approved=bool(run.papers) and not issues, issues=issues or ([] if run.papers else ['No papers processed']))
        run.artifacts = synthesize(run.papers)
        run.generated_claims = build_suggestions(run.papers)
        self.store.save(run)
        return run

    def analyze(self, run_id, selected_ids):
        run = self.store.load(run_id)
        choices = {c.id: c for c in run.candidates}
        if not selected_ids or len(set(selected_ids)) != len(selected_ids) or any(i not in choices for i in selected_ids):
            raise ValueError('Select distinct candidate IDs from this research run')
        # Build a complete new snapshot; failures leave the previous snapshot intact.
        papers = [p for p in run.papers if p.document.source.uri.startswith('upload:')]
        seen = {p.document.source.id for p in papers}
        for identity in selected_ids:
            item = choices[identity]
            document = self.processor.download(item.pdf_url, item.title)
            if document.source.id not in seen:
                papers.append(self.extractor.extract(document))
                seen.add(document.source.id)
        run.papers, run.selected_ids = papers, list(selected_ids)
        return self._finish(run)

    def import_pdf(self, data, title, run_id=None):
        run = self.store.load(run_id) if run_id else self._new(title)
        document = self.processor.parse_bytes(data, title, f'upload:{title}')
        if any(p.document.source.id == document.source.id for p in run.papers):
            raise ValueError('This PDF is already in the research run')
        run.papers.append(self.extractor.extract(document))
        return self._finish(run)
