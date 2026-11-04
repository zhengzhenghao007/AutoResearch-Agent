"""Bounded local OCR fallback; never sends a document to a remote service."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

MAX_OCR_PAGES = 20
OCR_TIMEOUT = 600


def recognize_pages(data: bytes, page_numbers: list[int]) -> dict[int, str]:
    if len(page_numbers) > MAX_OCR_PAGES:
        raise ValueError('This PDF needs OCR on more than 20 pages. Split it into smaller PDFs and retry.')
    if any(importlib.util.find_spec(name) is None for name in ('rapidocr_onnxruntime', 'pypdfium2')):
        raise ValueError('Scanned PDF detected. Install local OCR with: python -m pip install -r requirements-ocr.txt, then restart the API.')
    env = {**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    command = [sys.executable, '-m', 'services.pdf_ocr_worker', ','.join(map(str, page_numbers))]
    if sys.platform == 'win32':
        # Invoke the actual interpreter, not the venv redirector: killing it on
        # timeout then also closes the pipes (there is no surviving child).
        bootstrap = "import sys,json,runpy;sys.path=json.loads(sys.argv[1]);sys.argv=['services.pdf_ocr_worker',sys.argv[2]];runpy.run_module('services.pdf_ocr_worker',run_name='__main__')"
        command = [sys._base_executable, '-c', bootstrap, json.dumps(sys.path), ','.join(map(str, page_numbers))]
    try:
        result = subprocess.run(command, input=data, capture_output=True, timeout=OCR_TIMEOUT, env=env,
                                cwd=Path(__file__).resolve().parents[1],
                                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        if result.returncode:
            raise ValueError('Local OCR could not process this PDF. Try a smaller or higher-resolution PDF.')
        value = json.loads(result.stdout)
        if set(value) != {str(n) for n in page_numbers} or any(not isinstance(t, str) for t in value.values()) or sum(map(len, value.values())) > 1_000_000:
            raise ValueError('Invalid OCR output')
        return {int(n): text for n, text in value.items()}
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Local OCR exceeded 10 minutes. Split this PDF into smaller files and retry.') from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError('Local OCR failed to start. Reinstall requirements-ocr.txt and restart the API.') from exc
