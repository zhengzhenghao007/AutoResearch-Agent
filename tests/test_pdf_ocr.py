from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
import pytest

from services.paper_processing import PaperProcessor
from tests.test_evidence_pdf import pdf_bytes


def scan():
    image = Image.new('RGB', (1400, 400), 'white')
    draw = ImageDraw.Draw(image)
    from pathlib import Path
    import matplotlib
    font = ImageFont.truetype(str(Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf'), 38)
    draw.text((60, 80), 'Our method improves prediction accuracy.', font=font, fill='black')
    draw.text((60, 160), 'The experiment uses a public dataset.', font=font, fill='black')
    data = BytesIO()
    image.save(data, format='PDF', resolution=150)
    return data.getvalue()


def test_scanned_text_imports_with_explicit_ocr_provenance():
    data = scan()
    assert not PdfReader(BytesIO(data)).pages[0].extract_text().strip()
    document = PaperProcessor().parse_bytes(data, 'Synthetic scan', 'upload:scan.pdf')
    assert document.ocr_pages == [1]
    assert 'prediction accuracy' in document.pages[0].text.lower()
    assert document.total_pages == 1 and not document.truncated


def test_mixed_document_preserves_native_text_and_page_numbers():
    writer = PdfWriter()
    for data in (pdf_bytes(['Native method evidence.']), scan()):
        writer.add_page(PdfReader(BytesIO(data)).pages[0])
    result = BytesIO(); writer.write(result)
    document = PaperProcessor().parse_bytes(result.getvalue(), 'Mixed', 'upload:mixed.pdf')
    assert document.ocr_pages == [2]
    assert document.pages[0].text.strip() == 'Native method evidence.'
    assert 'prediction accuracy' in document.pages[1].text.lower()


def test_ocr_page_limit_is_explicit_before_worker():
    from services.pdf_ocr import recognize_pages
    with pytest.raises(ValueError, match='20'):
        recognize_pages(b'%PDF-placeholder', list(range(1, 22)))


def test_missing_local_engine_has_actionable_message(monkeypatch):
    from services import pdf_ocr
    monkeypatch.setattr(pdf_ocr.importlib.util, 'find_spec', lambda name: None)
    with pytest.raises(ValueError, match='requirements-ocr.txt'):
        pdf_ocr.recognize_pages(b'%PDF-placeholder', [1])


def test_native_serialization_remains_compatible_with_saved_hashes():
    document = PaperProcessor().parse_bytes(pdf_bytes(['Native method evidence.']), 'Native', 'upload:native.pdf')
    assert document.ocr_pages == []
    assert 'ocr_pages' not in document.model_dump()


def test_native_document_with_many_blank_pages_does_not_need_ocr(monkeypatch):
    from services import pdf_ocr
    monkeypatch.setattr(pdf_ocr.importlib.util, 'find_spec', lambda name: None)
    document = PaperProcessor().parse_bytes(pdf_bytes(['Native method evidence.'] + [''] * 21), 'Native', 'upload:native.pdf')
    assert len(document.pages) == 22
    assert document.ocr_pages == []


def test_combined_native_and_ocr_character_limit(monkeypatch):
    from services import paper_processing, pdf_ocr
    from types import SimpleNamespace
    import json
    monkeypatch.setattr(paper_processing.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps({'total_pages':2,'pages':[{'number':1,'text':'x'*600_000},{'number':2,'text':''}],'ocr_candidates':[2]}).encode()))
    monkeypatch.setattr(pdf_ocr, 'recognize_pages', lambda *a: {2:'y'*500_000})
    with pytest.raises(ValueError, match='character limit'):
        PaperProcessor().parse_bytes(b'%PDF-placeholder', 'Mixed', 'upload:mixed.pdf')


def test_real_ocr_timeout_terminates_worker_promptly(monkeypatch):
    from services import pdf_ocr
    import time
    monkeypatch.setattr(pdf_ocr, 'OCR_TIMEOUT', 0.01)
    started = time.monotonic()
    with pytest.raises(ValueError, match='exceeded'):
        pdf_ocr.recognize_pages(scan(), [1])
    assert time.monotonic() - started < 8


def test_outlined_text_without_image_objects_also_uses_ocr():
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from matplotlib.textpath import TextPath
    from matplotlib.patches import PathPatch
    figure, axes = plt.subplots(figsize=(10, 2))
    axes.add_patch(PathPatch(TextPath((10, 25), 'Our method improves prediction accuracy.', size=14), color='black'))
    axes.set_xlim(0, 320); axes.set_ylim(0, 60); axes.axis('off')
    data = BytesIO()
    figure.savefig(data, format='pdf'); plt.close(figure)
    page = PdfReader(BytesIO(data.getvalue())).pages[0]
    assert not page.extract_text().strip()
    assert len(page.images) == 0
    document = PaperProcessor().parse_bytes(data.getvalue(), 'Outlined text', 'upload:outlines.pdf')
    assert document.ocr_pages == [1]
    assert 'prediction accuracy' in document.pages[0].text.lower()
