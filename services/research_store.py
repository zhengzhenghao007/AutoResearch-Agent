"""Local single-user snapshots. Atomic writes, versioned validated reads."""
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from schemas.research import ResearchRun, ResearchRunSummary, ResearchHistory
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

    def history(self, page=1, page_size=10) -> ResearchHistory:
        """Validated summaries ordered by snapshot mtime, then ID for stable ties.

        Single-user snapshots: concurrent writes can change pagination between reads.
        Corrupt records fail explicitly instead of disappearing from history.
        """
        if page < 1 or not 1 <= page_size <= 50:
            raise ValueError('Invalid history pagination')
        paths = [p for p in self.root.glob('*.json')
                 if re.fullmatch(r'[a-f0-9]{32}', p.stem)]
        rows = []
        for path in paths:
            try:
                run = self.load(path.stem)
                modified = path.stat().st_mtime
            except (ValueError, OSError) as exc:
                raise ValueError(f'Invalid stored research run: {path.stem}') from exc
            rows.append((modified, ResearchRunSummary(
                id=run.id, topic=run.topic, candidate_count=len(run.candidates),
                selected_count=len(run.selected_ids), paper_count=len(run.papers),
                updated_at=datetime.fromtimestamp(modified, timezone.utc),
                source_support_passed=run.review.approved,
            )))
        rows.sort(key=lambda row: (row[0], row[1].id), reverse=True)
        start = (page - 1) * page_size
        return ResearchHistory(items=[row[1] for row in rows[start:start + page_size]],
                               total=len(rows), page=page, page_size=page_size)
