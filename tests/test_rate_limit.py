from fastapi.testclient import TestClient
import importlib, os
import travel_agent.config as cfg
import travel_agent.api as api_mod
from travel_agent.config import RATE_LIMIT_REQUESTS_PER_MIN
os.environ.pop('API_KEY', None)
cfg.API_KEY = None
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)

def test_rate_limit_exceeded():
    sid = "rl1"
    # fire limit times all succeed (may trigger clarify or success)
    for i in range(RATE_LIMIT_REQUESTS_PER_MIN):
        r = client.post("/api/mvp/plan", json={"session_id": sid, "text": f"预算1000 去北京 2025-12-10 2天"})
        assert r.status_code == 200
    # next one should be blocked
    r_block = client.post("/api/mvp/plan", json={"session_id": sid, "text": "预算1000 去北京 2025-12-10 2天"})
    j = r_block.json()
    assert j["success"] is False and j["error"]["code"] == "RATE_LIMIT_EXCEEDED"