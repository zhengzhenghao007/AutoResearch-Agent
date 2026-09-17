from io import BytesIO
import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from services.paper_processing import PaperProcessor


def pdf_bytes(texts):
    writer = PdfWriter()
    for text in texts:
        page = writer.add_blank_page(width=600, height=800)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(('BT /F1 12 Tf 40 700 Td (' + text + ') Tj ET').encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def test_real_pdf_pages_and_truncation():
    document = PaperProcessor(max_pages=1).parse_bytes(pdf_bytes(['First page evidence.', 'Second page.']), 'Paper', 'upload:p.pdf')
    assert document.pages[0].number == 1
    assert 'First page evidence.' in document.pages[0].text
    assert document.total_pages == 2 and document.truncated


@pytest.mark.parametrize('data', [b'not pdf', pdf_bytes([''])])
def test_bad_or_scanned_pdf_is_explicit(data):
    with pytest.raises(ValueError):
        PaperProcessor().parse_bytes(data, 'Paper', 'upload:p.pdf')


@pytest.mark.parametrize('url', ['http://arxiv.org/pdf/2401.12345', 'https://evil.test/a.pdf', 'https://arxiv.org@localhost/pdf/2401.12345', 'https://arxiv.org/pdf/../../admin', 'https://arxiv.org:443/pdf/2401.12345'])
def test_rejects_unsafe_urls_before_network(url):
    with pytest.raises(ValueError):
        PaperProcessor().download(url, 'Paper')


def test_parser_timeout_is_explicit(monkeypatch):
    import subprocess
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('pdf_worker', 45)
    monkeypatch.setattr(subprocess, 'run', timeout)
    with pytest.raises(ValueError, match='Unable to read PDF'):
        PaperProcessor().parse_bytes(b'%PDF-fake', 'Paper', 'upload:p.pdf')


def test_redirects_and_oversize_download_rejected(monkeypatch):
    import requests
    class Response:
        status_code = 302
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def iter_content(self, size): yield b'a' * 11
    response = Response()
    def get(url, **kwargs):
        assert kwargs['allow_redirects'] is False
        return response
    monkeypatch.setattr(requests, 'get', get)
    with pytest.raises(ValueError, match='HTTP 302'):
        PaperProcessor().download('https://arxiv.org/pdf/2401.12345', 'Paper')
    response.status_code = 200
    with pytest.raises(ValueError, match='size limit'):
        PaperProcessor(max_bytes=10).download('https://arxiv.org/pdf/2401.12345', 'Paper')


def test_worker_and_parent_agree_on_maximum_size():
    with pytest.raises(ValueError, match='limits'):
        PaperProcessor(max_bytes=20 * 1024 * 1024 + 1)
