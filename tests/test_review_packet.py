"""Review provenance simulations are confined to temporary test copies."""
import hashlib
import importlib
import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

CORPUS = Path(__file__).parent / 'fixtures' / 'evidence'


def api():
    return importlib.import_module('evaluation.review_packet')


def setup_packet(tmp_path):
    source = tmp_path / 'source'
    shutil.copytree(CORPUS, source)
    manifest = source / 'manifest.json'
    packet = tmp_path / 'packet'
    api().export_packet(manifest, packet)
    reviews = packet / 'reviews.json'
    data = json.loads(reviews.read_text(encoding='utf-8'))
    return manifest, reviews, data


def complete(data, manifest, record_id='normal'):
    original = next(r for r in json.loads(manifest.read_text())['records'] if r['id'] == record_id)
    row = next(r for r in data['reviews'] if r['id'] == record_id)
    row.update(completed=True, reviewer='TEST ONLY simulated reviewer',
               reviewed_at=date.today().isoformat(), annotations=original['annotations'])
    return row


def save(path, data):
    path.write_text(json.dumps(data), encoding='utf-8')


def test_export_is_offline_blank_and_escaped(tmp_path):
    source = tmp_path / 'source'
    shutil.copytree(CORPUS, source)
    manifest = source / 'manifest.json'
    original = json.loads(manifest.read_text())
    original['records'][0]['source'] = '<script>alert(1)</script>'
    save(manifest, original)
    out = tmp_path / 'packet'
    api().export_packet(manifest, out)
    data = json.loads((out / 'reviews.json').read_text())
    assert data['manifest_sha256'] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert len(data['reviews']) == 7
    assert all(not r['completed'] and r['reviewer'] is None and r['reviewed_at'] is None
               and r['annotations'] == [] for r in data['reviews'])
    html = (out / 'index.html').read_text(encoding='utf-8')
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert 'We propose a compact algorithm.' in html
    assert {hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*.pdf')} == {
        r['sha256'] for r in original['records']}


def test_import_roundtrip_keeps_source_and_pending_records(tmp_path):
    manifest, reviews, data = setup_packet(tmp_path)
    before = manifest.read_bytes()
    complete(data, manifest)
    save(reviews, data)
    out = tmp_path / 'reviewed'
    api().import_reviews(manifest, reviews, out)
    result = importlib.import_module('evaluation.evaluate_evidence').evaluate(out / 'manifest.json')
    assert result['reviewed_count'] == 1
    assert result['regressions']['passed'] == 7
    records = json.loads((out / 'manifest.json').read_text())['records']
    assert sum(r['status'] == 'pending_human_review' for r in records) == 6
    assert manifest.read_bytes() == before
    audit = json.loads((out / 'import_audit.json').read_text())
    assert audit['manifest_sha256'] == hashlib.sha256(before).hexdigest()


@pytest.mark.parametrize('mutation', [
    'manifest_hash', 'sample_hash', 'scope', 'duplicate', 'unknown', 'missing',
    'quote', 'page', 'reviewer', 'future', 'extra', 'incomplete', 'bool_string',
])
def test_import_rejects_invalid_reviews_without_output(tmp_path, mutation):
    manifest, reviews, data = setup_packet(tmp_path)
    row = complete(data, manifest)
    if mutation == 'manifest_hash': data['manifest_sha256'] = '0' * 64
    if mutation == 'sample_hash': row['sha256'] = '0' * 64
    if mutation == 'scope': row['max_pages'] += 1
    if mutation == 'duplicate': data['reviews'].append(row.copy())
    if mutation == 'unknown': row['id'] = 'unknown'
    if mutation == 'missing': data['reviews'].pop()
    if mutation == 'quote': row['annotations'][0]['quote'] = 'A fabricated sentence absent from the paper.'
    if mutation == 'page': row['annotations'][0]['page'] = 99
    if mutation == 'reviewer': row['reviewer'] = '   '
    if mutation == 'future': row['reviewed_at'] = (date.today() + timedelta(days=1)).isoformat()
    if mutation == 'extra': row['unrecognized'] = True
    if mutation == 'incomplete': row['completed'] = False
    if mutation == 'bool_string': row['completed'] = 'true'
    save(reviews, data)
    out = tmp_path / 'reviewed'
    with pytest.raises(ValueError): api().import_reviews(manifest, reviews, out)
    assert not out.exists()


def test_rejects_empty_review_and_existing_destination(tmp_path):
    manifest, reviews, data = setup_packet(tmp_path)
    with pytest.raises(ValueError): api().import_reviews(manifest, reviews, tmp_path / 'empty')
    with pytest.raises((ValueError, FileExistsError)):
        api().export_packet(manifest, reviews.parent)
    complete(data, manifest)
    save(reviews, data)
    out = tmp_path / 'existing'
    out.mkdir()
    marker = out / 'keep.txt'
    marker.write_text('keep')
    with pytest.raises((ValueError, FileExistsError)): api().import_reviews(manifest, reviews, out)
    assert marker.read_text() == 'keep'


def test_raster_review_allows_no_annotations(tmp_path):
    manifest, reviews, data = setup_packet(tmp_path)
    row = complete(data, manifest, 'image_only')
    assert row['annotations'] == []
    save(reviews, data)
    out = tmp_path / 'reviewed'
    api().import_reviews(manifest, reviews, out)
    records = json.loads((out / 'manifest.json').read_text())['records']
    assert next(r for r in records if r['id'] == 'image_only')['status'] == 'human_reviewed'


def test_incomplete_row_preserves_existing_review(tmp_path):
    source = tmp_path / 'source'
    shutil.copytree(CORPUS, source)
    manifest = source / 'manifest.json'
    original = json.loads(manifest.read_text())
    original['records'][0].update(status='human_reviewed',
        reviewer='TEST ONLY earlier simulated reviewer', reviewed_at=date.today().isoformat())
    save(manifest, original)
    packet = tmp_path / 'packet'
    api().export_packet(manifest, packet)
    reviews = packet / 'reviews.json'
    data = json.loads(reviews.read_text())
    assert not data['reviews'][0]['completed']
    complete(data, manifest, 'image_only')
    save(reviews, data)
    out = tmp_path / 'reviewed'
    api().import_reviews(manifest, reviews, out)
    result = json.loads((out / 'manifest.json').read_text())['records'][0]
    assert result['reviewer'] == original['records'][0]['reviewer']
    assert result['annotations'] == original['records'][0]['annotations']


def test_failed_pdf_copy_leaves_no_published_output(tmp_path, monkeypatch):
    manifest, reviews, data = setup_packet(tmp_path)
    complete(data, manifest)
    save(reviews, data)
    original_write = Path.write_bytes

    def fail_pdf_write(path, value):
        if path.suffix == '.pdf': raise OSError('simulated disk failure')
        return original_write(path, value)

    monkeypatch.setattr(Path, 'write_bytes', fail_pdf_write)
    out = tmp_path / 'reviewed'
    with pytest.raises(OSError): api().import_reviews(manifest, reviews, out)
    assert not out.exists()
