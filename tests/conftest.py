# Ensure src/ is on path so 'travel_agent' package resolves when not installed.
import sys, os, importlib
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import travel_agent.config as cfg
import travel_agent.api as api_mod

@pytest.fixture(autouse=True)
def clear_api_key():
    os.environ.pop('API_KEY', None)
    cfg.API_KEY = None
    importlib.reload(cfg)
    importlib.reload(api_mod)
    yield
