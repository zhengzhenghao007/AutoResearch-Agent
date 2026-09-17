"""Both uploaded and downloaded papers enter the same bounded PDF parser."""
import hashlib
import re
import subprocess
import sys
import json
from pathlib import Path
import requests
from schemas.research import Document, Page, Source


class PaperProcessor:
    def __init__(self, max_pages=50, max_bytes=20 * 1024 * 1024):
        if not 1 <= max_pages <= 500 or not 1 <= max_bytes <= 20 * 1024 * 1024:
            raise ValueError('Invalid PDF limits')
        self.max_pages, self.max_bytes = max_pages, max_bytes

    def parse_bytes(self, data: bytes, title: str, uri: str) -> Document:
        if len(data) > self.max_bytes or not data.startswith(b'%PDF-'):
            raise ValueError('Expected a PDF within the size limit')
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'services.pdf_worker', str(self.max_pages)],
                input=data, capture_output=True, timeout=45,
                cwd=Path(__file__).resolve().parents[1],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            )
            if result.returncode:
                raise ValueError('PDF worker rejected document')
            parsed = json.loads(result.stdout)
            total = parsed['total_pages']
            pages = [Page.model_validate(p) for p in parsed['pages']]
        except (ValueError, subprocess.TimeoutExpired, OSError) as exc:
            raise ValueError('Unable to read PDF; supply an unencrypted text PDF') from exc
        if not any(p.text.strip() for p in pages):
            raise ValueError('No readable text in selected pages; OCR is not implemented')
        digest = hashlib.sha256(data).hexdigest()
        return Document(source=Source(id=digest, title=title, uri=uri, sha256=digest),
                        pages=pages, total_pages=total, truncated=total > len(pages))

    def parse_local(self, path: str) -> Document:
        file = Path(path)
        with file.open('rb') as stream:
            data = stream.read(self.max_bytes + 1)
        return self.parse_bytes(data, file.stem, f'upload:{file.name}')

    def download(self, url: str, title: str) -> Document:
        # Canonical allowlist; reject credentials, ports, query strings and redirects.
        if not re.fullmatch(r'https://arxiv\.org/pdf/(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?(?:\.pdf)?', url):
            raise ValueError('Only canonical HTTPS arXiv PDF URLs are supported')
        with requests.get(url, timeout=(10, 60), stream=True, allow_redirects=False) as response:
            if response.status_code != 200:
                raise ValueError(f'PDF download returned HTTP {response.status_code}')
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > self.max_bytes:
                    raise ValueError('PDF exceeds size limit')
                chunks.append(chunk)
        return self.parse_bytes(b''.join(chunks), title, url)
