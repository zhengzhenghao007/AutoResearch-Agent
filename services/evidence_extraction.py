"""Conservative extractive reader: generated prose cannot become a reported fact."""
import json
import re
from pathlib import Path
from pydantic import Field
from schemas.research import (Contract, Category, CATEGORIES, Document, Evidence, Claim, PaperEvidence)
from services.evidence_review import review_paper


class Selection(Contract):
    page: int = Field(ge=1)
    quote: str = Field(min_length=12, max_length=3000)
    category: Category


class Selections(Contract):
    items: list[Selection] = Field(default_factory=list, max_length=200)


PATTERNS = {
    'future_work': r'future work|future research|further investigation|we expect|we hypothesi[sz]e|we plan|expected to|hypothetical',
    'limitation': r'limitation|limited by|limited to|drawback',
    'problem': r'challenge|research question|problem|aim to|aims to',
    'method': r'we propose|our method|our approach|framework|algorithm',
    'dataset': r'dataset|data set|benchmark corpus',
    'experiment': r'we evaluate|experiment|experimental setup|ablation',
    'result': r'we find|results show|results indicate|achieved|outperforms',
}


class EvidenceExtractor:
    def __init__(self, mode='rule', llm_client=None):
        if mode not in ('rule', 'llm'):
            raise ValueError('Mode must be rule or llm')
        self.mode, self.llm_client = mode, llm_client

    def extract(self, document: Document) -> PaperEvidence:
        if self.mode == 'llm':
            if self.llm_client is None:
                from services.llm_client import LLMClient
                self.llm_client = LLMClient()
            # Fail explicitly rather than silently hiding pages from the reader.
            payload = json.dumps([p.model_dump() for p in document.pages], ensure_ascii=False)
            if len(payload) > 100000:
                raise ValueError('LLM input exceeds 100000 characters; lower max_pages or use rule mode')
            prompt = (Path(__file__).resolve().parents[1] / 'prompts/evidence_extraction.txt').read_text(encoding='utf-8')
            response = self.llm_client.structured_chat(system_prompt=prompt, user_prompt=payload, output_schema=Selections)
            selections = Selections.model_validate(response.parsed.model_dump()).items
        else:
            selections = []
            for page in document.pages:
                for sentence in re.split(r'(?<=[.!?])\s+', page.text):
                    sentence = sentence.strip()
                    if not 12 <= len(sentence) <= 3000:
                        continue
                    for category, pattern in PATTERNS.items():
                        if re.search(pattern, sentence, re.I):
                            selections.append(Selection(page=page.number, quote=sentence, category=category))
                            break
        paper = PaperEvidence(document=document, extractor=f'literal-{self.mode}-v1')
        seen = set()
        for selection in selections:
            key = (selection.page, selection.quote, selection.category)
            if key in seen:
                continue
            seen.add(key)
            identity = f'{document.source.id}:{len(paper.claims) + 1}'
            evidence_id = f'e:{identity}'
            paper.evidence.append(Evidence(id=evidence_id, source_id=document.source.id, page=selection.page, quote=selection.quote))
            paper.claims.append(Claim(id=f'c:{identity}', text=selection.quote, category=selection.category, evidence_ids=[evidence_id], created_by=paper.extractor))
        paper.missing_fields = [c for c in CATEGORIES if c not in {v.category for v in paper.claims}]
        review = review_paper(paper)
        if paper.claims and not review.approved:
            raise ValueError('Rejected extraction: ' + '; '.join(review.issues))
        return paper
