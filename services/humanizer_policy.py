"""One local publication policy shared by the API, CLI and background workers."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

Profile = Literal['minimal', 'standard']


def policy_path():
    return Path(os.environ.get('AUTORESEARCH_HUMANIZER_POLICY_FILE',
                               Path(__file__).resolve().parents[1] / 'data' / 'academic-humanizer.json'))


def profile() -> Profile:
    try:
        value = json.loads(policy_path().read_text(encoding='utf-8'))['profile']
    except FileNotFoundError:
        return 'standard'
    if value not in ('standard', 'minimal'):
        raise ValueError('Invalid Academic Humanizer profile')
    return value


def set_profile(value: Profile):
    if value not in ('standard', 'minimal'):
        raise ValueError('Invalid Academic Humanizer profile')
    path = policy_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as target:
            temporary = target.name
            json.dump({'profile':value}, target)
        os.replace(temporary, path)
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)
