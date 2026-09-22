"""Offline browser QA server, never a production or live-search entry point.

Run from the repository root:
  python -m uvicorn --app-dir tests ui_fixture_server:app --port 8000
Snapshots are isolated in a temporary directory and discarded on process exit.
Only the external literature source is replaced; parsing, extraction, validation,
synthesis, persistence and HTTP handlers are the real implementation.
"""
import tempfile

from backend.app.main import app
from backend.app.api.research import get_workflow
from services.paper_processing import PaperProcessor
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow
from test_evidence_pdf import pdf_bytes


_directory = tempfile.TemporaryDirectory(prefix='evidence-ui-')
PAPERS = [
    {'title': 'Offline fixture: route planning',
     'pdf_url': 'https://arxiv.org/pdf/2401.12345',
     'summary': 'Synthetic regression material; not a real published paper.',
     'authors': ['Synthetic fixture']},
    {'title': 'Offline fixture: map comparison',
     'pdf_url': 'https://arxiv.org/pdf/2401.12346',
     'summary': 'Synthetic regression material; not a real published paper.',
     'authors': ['Synthetic fixture']},
]
TEXTS = [
    ['We propose a route planning method.',
     'A limitation is the small evaluation area.'],
    ['Our approach compares two map representations.',
     'We plan a future experiment on additional maps.'],
]


class FixtureSourceProcessor(PaperProcessor):
    def download(self, url, title):
        index = next(i for i, paper in enumerate(PAPERS) if paper['pdf_url'] == url)
        return self.parse_bytes(pdf_bytes(TEXTS[index]), title, url)


flow = EvidenceWorkflow(
    store=ResearchStore(_directory.name), processor=FixtureSourceProcessor(),
    search=lambda topic, max_results=5: [] if topic == 'empty' else PAPERS[:max_results],
)
app.dependency_overrides[get_workflow] = lambda: flow
