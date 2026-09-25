"""Offline evaluation; pending annotations are never accuracy ground truth."""
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from schemas.research import Contract, Category, CATEGORIES
from services.evidence_extraction import EvidenceExtractor
from services.evidence_review import normalized, review_paper
from services.paper_processing import PaperProcessor


class Annotation(Contract):
    page: int = Field(ge=1)
    quote: str = Field(min_length=12)
    category: Category
    supported: bool = Field(strict=True)


class Record(Contract):
    id: str = Field(min_length=1)
    file: str = Field(min_length=1)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source: str = Field(min_length=1)
    license: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    status: Literal['pending_human_review', 'human_reviewed']
    reviewer: str | None = None
    reviewed_at: date | None = None
    max_pages: int = Field(ge=1, le=500)
    annotations: list[Annotation]
    expected_categories: list[Category]
    expected_truncated: bool
    expected_error: bool
    reject_quote: str | None = None

    @model_validator(mode='after')
    def provenance_complete(self):
        if self.status == 'human_reviewed':
            if not self.reviewer or not self.reviewed_at or self.reviewed_at > date.today():
                raise ValueError('Human review requires reviewer and valid review date')
        elif self.reviewer is not None or self.reviewed_at is not None:
            raise ValueError('Pending records cannot claim review provenance')
        keys = [(a.page, normalized(a.quote), a.category) for a in self.annotations]
        if len(set(keys)) != len(keys):
            raise ValueError('Duplicate annotations')
        return self


class Manifest(Contract):
    schema_version: Literal[1]
    records: list[Record] = Field(min_length=1)


def load_manifest(path):
    path = Path(path).resolve()
    manifest = Manifest.model_validate_json(path.read_text(encoding='utf-8'))
    ids = set()
    files = set()
    for record in manifest.records:
        file = (path.parent / record.file).resolve()
        if not file.is_relative_to(path.parent) or file == path.parent:
            raise ValueError('Fixture path escapes corpus')
        if record.id in ids or file in files:
            raise ValueError('Duplicate fixture identity')
        ids.add(record.id)
        files.add(file)
        if hashlib.sha256(file.read_bytes()).hexdigest() != record.sha256:
            raise ValueError('Fixture integrity mismatch')
    return manifest


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def evaluate(path):
    path = Path(path).resolve()
    manifest = load_manifest(path)
    tp, predicted, gold_count = Counter(), Counter(), Counter()
    reviewed_count = located = supported = claim_count = 0
    failed = []
    for record in manifest.records:
        data = (path.parent / record.file).read_bytes()
        try:
            doc = PaperProcessor(max_pages=record.max_pages).parse_bytes(data, record.id, record.source)
        except ValueError as exc:
            if not record.expected_error or 'No readable text' not in str(exc):
                raise
            if record.annotations:
                raise ValueError('Unreadable fixture cannot carry annotation quotes')
            if record.status == 'human_reviewed':
                reviewed_count += 1
            continue
        pages = {p.number: normalized(p.text) for p in doc.pages}
        for annotation in record.annotations:
            if normalized(annotation.quote) not in pages.get(annotation.page, ''):
                raise ValueError(f'{record.id}: annotation quote not found on cited page')
        paper = EvidenceExtractor().extract(doc)
        regression_ok = (not record.expected_error and doc.truncated == record.expected_truncated
                         and sorted(c.category for c in paper.claims) == sorted(record.expected_categories))
        if record.reject_quote:
            corrupted = paper.model_copy(deep=True)
            if not corrupted.evidence:
                regression_ok = False
            else:
                corrupted.evidence[0].quote = record.reject_quote
                corrupted.claims[0].text = record.reject_quote
                regression_ok &= not review_paper(corrupted).approved
        if not regression_ok:
            failed.append(record.id)
        if record.status != 'human_reviewed':
            continue
        reviewed_count += 1
        gold = {(a.page, normalized(a.quote), a.category) for a in record.annotations}
        support = {(a.page, normalized(a.quote)) for a in record.annotations if a.supported}
        gold_count.update(a.category for a in record.annotations)
        evidence = {e.id: e for e in paper.evidence}
        matched = set()
        for claim in paper.claims:
            predicted[claim.category] += 1
            claim_count += 1
            refs = [evidence[e] for e in claim.evidence_ids if e in evidence]
            located += bool(refs) and all(e.source_id == doc.source.id and normalized(e.quote) in pages.get(e.page, '') for e in refs)
            supported += any((e.page, normalized(e.quote)) in support for e in refs)
            for e in refs:
                key = (e.page, normalized(e.quote), claim.category)
                if key in gold and key not in matched:
                    tp[claim.category] += 1
                    matched.add(key)
                    break
    metrics = None
    if reviewed_count:
        metrics = {'categories': {c: {'true_positive': tp[c], 'predicted': predicted[c], 'gold': gold_count[c],
                    'precision': ratio(tp[c], predicted[c]), 'recall': ratio(tp[c], gold_count[c]),
                    'missingness': ratio(gold_count[c] - tp[c], gold_count[c])} for c in CATEGORIES},
                   'quote_location_rate': ratio(located, claim_count), 'support_rate': ratio(supported, claim_count),
                   'predicted_claims': claim_count}
    return {'reviewed_count': reviewed_count, 'pending_count': len(manifest.records) - reviewed_count,
            'metrics': metrics, 'regressions': {'passed': len(manifest.records) - len(failed), 'failed': failed}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', nargs='?', default='tests/fixtures/evidence/manifest.json')
    args = parser.parse_args()
    result = evaluate(args.manifest)
    print(json.dumps(result, indent=2))
    return bool(result['regressions']['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
