"""Portable, offline human review packets; labels are supplied only by reviewers."""
import argparse
from contextlib import contextmanager
from datetime import date
import hashlib
from html import escape
import json
from pathlib import Path
import shutil
import tempfile
from typing import Literal

from pydantic import Field, model_validator
from evaluation.evaluate_evidence import Annotation, Manifest, Record, load_manifest
from schemas.research import CATEGORIES, Contract
from services.evidence_review import normalized
from services.paper_processing import PaperProcessor


class ReviewEntry(Contract):
    id: str = Field(min_length=1)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    max_pages: int = Field(ge=1, le=500, strict=True)
    completed: bool = Field(strict=True)
    reviewer: str | None
    reviewed_at: date | None
    annotations: list[Annotation]

    @model_validator(mode='after')
    def review_provenance(self):
        if self.completed:
            if not self.reviewer or not self.reviewed_at or self.reviewed_at > date.today():
                raise ValueError('Completed review requires reviewer and a valid review date')
        elif self.reviewer is not None or self.reviewed_at is not None or self.annotations:
            raise ValueError('Incomplete review must have null provenance and empty annotations')
        return self


class ReviewPacket(Contract):
    schema_version: Literal[1]
    manifest_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    reviews: list[ReviewEntry]


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _destination(output_dir):
    # Check before resolving: dangling symlinks are existing destinations too.
    output = Path(output_dir).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Output already exists: {output}')
    return output


@contextmanager
def _staging(output):
    stage = Path(tempfile.mkdtemp(prefix=f'.{output.name}-', dir=output.parent))
    try:
        yield stage
        _destination(output)
        stage.rename(output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _load(manifest_path):
    path = Path(manifest_path).resolve()
    raw = path.read_bytes()
    manifest = load_manifest(path)
    if Manifest.model_validate_json(raw) != manifest:
        raise ValueError('Manifest changed while loading')
    samples = []
    for record in manifest.records:
        data = (path.parent / record.file).read_bytes()
        if _digest(data) != record.sha256:
            raise ValueError('Fixture integrity mismatch')
        try:
            doc = PaperProcessor(max_pages=record.max_pages).parse_bytes(data, record.id, record.source)
        except ValueError as exc:
            if not record.expected_error or 'No readable text' not in str(exc):
                raise
            if record.annotations:
                raise ValueError('Unreadable fixture cannot carry annotation quotes') from exc
            doc = None
        samples.append((record, data, doc))
    return manifest, _digest(raw), samples


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def _pdf_name(index):
    return f'{index:04d}.pdf'


def export_packet(manifest_path, output_dir):
    """Export source text and blank review entries without making review claims."""
    output = _destination(output_dir)
    _, manifest_hash, samples = _load(manifest_path)
    reviews, sections = [], []
    for index, (record, _, doc) in enumerate(samples, 1):
        reviews.append(dict(id=record.id, sha256=record.sha256, max_pages=record.max_pages,
                            completed=False, reviewer=None, reviewed_at=None, annotations=[]))
        provenance = '\n'.join(f'{label}: {value}' for label, value in (
            ('Source', record.source), ('SHA-256', record.sha256), ('License', record.license),
            ('Provenance', record.provenance), ('max_pages', record.max_pages)))
        scope = (f'Selected pages 1–{len(doc.pages)} of {doc.total_pages}; truncated: {doc.truncated}.'
                 if doc else 'No readable text in selected pages; OCR is not implemented.')
        pages = ''.join(f'<h3>Page {p.number}</h3><pre>{escape(p.text)}</pre>' for p in doc.pages) if doc else ''
        drafts = json.dumps([a.model_dump(mode='json') for a in record.annotations], indent=2)
        sections.append(f'<section><h2>{escape(record.id)}</h2>'
                        f'<a href="{_pdf_name(index)}">Local source PDF</a>'
                        f'<pre>{escape(provenance)}</pre><p>Review scope: {escape(scope)}</p>{pages}'
                        '<details><summary>Original draft annotations — not human verified by this packet</summary>'
                        f'<pre>{escape(drafts)}</pre></details></section>')
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
            'base-uri &#39;none&#39;; form-action &#39;none&#39;">'
            '<title>Offline evidence review</title></head><body><h1>Offline evidence review</h1>'
            '<p>Edit reviews.json locally. Exhaustively annotate the selected pages, including missed evidence. '
            'Each annotation needs page, exact quote (at least 12 characters), category, and supported (boolean). '
            'Categories: ' + escape(', '.join(CATEGORIES)) + '.</p>'
            '<p>Assess category and literal source support yourself. Source support is not scientific truth. '
            'Draft annotations are suggestions, not verified labels. Only set completed to true after reviewing '
            'the entire selected scope; supply your nonblank reviewer identity and YYYY-MM-DD review date. '
            'Incomplete entries must keep null reviewer/date and empty annotations. '
            'No readable text may be recorded with an empty annotation list.</p>'
            f'<p>Source manifest SHA-256: {manifest_hash}</p>' + ''.join(sections) + '</body></html>')
    with _staging(output) as stage:
        for index, (_, data, _) in enumerate(samples, 1):
            (stage / _pdf_name(index)).write_bytes(data)
        _write_json(stage / 'reviews.json', dict(schema_version=1, manifest_sha256=manifest_hash, reviews=reviews))
        (stage / 'index.html').write_text(html, encoding='utf-8')
    return output / 'reviews.json'


def import_reviews(manifest_path, review_path, output_dir):
    """Validate review provenance and literal locations, then publish a new corpus."""
    output = _destination(output_dir)
    manifest, manifest_hash, samples = _load(manifest_path)
    raw_reviews = Path(review_path).read_bytes()
    packet = ReviewPacket.model_validate_json(raw_reviews)
    if packet.manifest_sha256 != manifest_hash:
        raise ValueError('Source manifest hash mismatch')
    rows = {row.id: row for row in packet.reviews}
    if len(rows) != len(packet.reviews) or set(rows) != {r.id for r in manifest.records}:
        raise ValueError('Reviews must contain each manifest identity exactly once')
    completed = [row.id for row in packet.reviews if row.completed]
    if not completed:
        raise ValueError('At least one completed human review is required')
    records = []
    for index, (record, _, doc) in enumerate(samples, 1):
        row = rows[record.id]
        if row.sha256 != record.sha256 or row.max_pages != record.max_pages:
            raise ValueError('Review sample hash or page scope mismatch')
        values = record.model_dump(mode='json')
        values['file'] = _pdf_name(index)
        if row.completed:
            pages = {p.number: normalized(p.text) for p in doc.pages} if doc else {}
            for annotation in row.annotations:
                if normalized(annotation.quote) not in pages.get(annotation.page, ''):
                    raise ValueError(f'{record.id}: annotation quote not found on cited page')
            values.update(status='human_reviewed', reviewer=row.reviewer,
                          reviewed_at=row.reviewed_at, annotations=row.annotations)
        records.append(Record.model_validate(values))
    result = Manifest(schema_version=1, records=records)
    with _staging(output) as stage:
        for index, (_, data, _) in enumerate(samples, 1):
            (stage / _pdf_name(index)).write_bytes(data)
        _write_json(stage / 'manifest.json', result.model_dump(mode='json'))
        _write_json(stage / 'import_audit.json', dict(schema_version=1, manifest_sha256=manifest_hash,
                    reviews_sha256=_digest(raw_reviews), completed_ids=completed))
    return output / 'manifest.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('export', 'import'):
        command = commands.add_parser(name)
        command.add_argument('manifest')
        if name == 'import':
            command.add_argument('reviews')
        command.add_argument('output_dir')
    args = parser.parse_args()
    try:
        result = (export_packet(args.manifest, args.output_dir) if args.command == 'export'
                  else import_reviews(args.manifest, args.reviews, args.output_dir))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(result)


if __name__ == '__main__':
    main()
