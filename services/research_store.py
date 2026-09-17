"""Local single-user snapshots. Atomic writes, versioned validated reads."""
import os
import re
import tempfile
from pathlib import Path
from schemas.research import ResearchRun
from services.research_validation import validate_run


class ResearchStore:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else Path(__file__).resolve().parents[1] / 'data/research_runs'

    def _path(self, run_id):
        if not re.fullmatch(r'[a-f0-9]{32}', run_id):
            raise ValueError('Invalid research run ID')
        return self.root / f'{run_id}.json'

    def save(self, run: ResearchRun):
        run = ResearchRun.model_validate(run.model_dump())
        validate_run(run)
        path = self._path(run.id)
        self.root.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.root, delete=False) as file:
                name = file.name
                file.write(run.model_dump_json(indent=2))
                file.flush()
                os.fsync(file.fileno())
            os.replace(name, path)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)

    def load(self, run_id) -> ResearchRun:
        run = ResearchRun.model_validate_json(self._path(run_id).read_text(encoding='utf-8'))
        if run.id != run_id:
            raise ValueError('Stored run ID does not match filename')
        validate_run(run)
        return run
