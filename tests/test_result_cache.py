from fastapi.testclient import TestClient
import importlib, os, sys
from pathlib import Path

# Ensure src path present
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import travel_agent.config as cfg
import travel_agent.api as api_mod
from travel_agent.metrics import METRICS
from travel_agent.cache_util import cache_clear

# Disable API key for test isolation
os.environ.pop('API_KEY', None)
cfg.API_KEY = None
importlib.reload(cfg)
importlib.reload(api_mod)
app = api_mod.app
client = TestClient(app)

def test_result_cache_hit():
    METRICS.reset()
    cache_clear()
    # first request should be miss
    r1 = client.post("/api/mvp/plan", json={"session_id": "c1", "text": "从北京 预算2000 去上海 2025-12-10 3天"})
    assert r1.status_code == 200 and r1.json()["success"] is True
    # second identical is hit
    r2 = client.post("/api/mvp/plan", json={"session_id": "c2", "text": "从北京 预算2000 去上海 2025-12-10 3天"})
    assert r2.status_code == 200 and r2.json()["success"] is True
    m = client.get("/api/mvp/metrics").json()
    assert m["cache_misses"] == 1
    assert m["cache_hits"] == 1