"""Protect review work and exercise a real raster-only PDF (no hidden text)."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader
from services.paper_processing import PaperProcessor

CORPUS = Path(__file__).parent / 'fixtures' / 'evidence'


def generator():
    spec = importlib.util.spec_from_file_location('fixture_generator', CORPUS / 'generate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_raster_fixture_has_image_pixels_but_no_extractable_text():
    path = CORPUS / 'image_only.pdf'
    assert path.exists(), 'Missing image-only scan regression fixture'
    reader = PdfReader(path)
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert not page.extract_text().strip()
    images = page['/Resources']['/XObject']
    raster = next(value.get_object() for value in images.values())
    assert raster['/Subtype'] == '/Image'
    assert len(set(raster.get_data())) > 1  # actual nonblank raster content
    with pytest.raises(ValueError, match='No readable text'):
        PaperProcessor().parse_bytes(path.read_bytes(), 'Raster fixture', 'upload:image_only.pdf')


@pytest.mark.parametrize('existing', ['manifest.json', 'normal.pdf'])
def test_generator_refuses_overwrite_before_any_mutation(tmp_path, existing):
    root = tmp_path / 'corpus'
    root.mkdir()
    # A preexisting manifest could contain real human work; never parse-and-rewrite it.
    (root / existing).write_bytes(b'Human work must remain byte-for-byte unchanged')
    before = {p.name:p.read_bytes() for p in root.iterdir()}
    with pytest.raises(FileExistsError):
        generator().generate(root)
    assert {p.name:p.read_bytes() for p in root.iterdir()} == before


def test_generator_new_directory_is_reproducible_and_pending(tmp_path):
    module = generator()
    first, second = tmp_path / 'first', tmp_path / 'second'
    module.generate(first)
    module.generate(second)
    assert {p.name:p.read_bytes() for p in first.iterdir()} == {p.name:p.read_bytes() for p in second.iterdir()}
    assert all(p.read_bytes() == (CORPUS / p.name).read_bytes() for p in first.glob('*.pdf'))
    assert json.loads((first / 'manifest.json').read_text()) == json.loads((CORPUS / 'manifest.json').read_text())
    from evaluation.evaluate_evidence import evaluate
    result = evaluate(first / 'manifest.json')
    assert result == {'reviewed_count':0,'pending_count':7,'metrics':None,'regressions':{'passed':7,'failed':[]}}
    records = json.loads((first / 'manifest.json').read_text())['records']
    assert all(r['status']=='pending_human_review' and r['reviewer'] is None for r in records)


def test_generator_cli_existing_target_exits_cleanly(tmp_path):
    root = tmp_path / 'existing'
    root.mkdir()
    (root / 'manifest.json').write_text('{}')
    script = tmp_path / 'generate.py'
    shutil.copyfile(CORPUS / 'generate.py', script)
    result = subprocess.run([sys.executable,str(script),'--output-dir',str(root)],capture_output=True,text=True)
    assert result.returncode != 0
    assert 'overwrite' in result.stderr.lower()
    assert list(p.name for p in root.iterdir()) == ['manifest.json']
