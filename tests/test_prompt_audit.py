from fastapi.testclient import TestClient
import importlib, os
import travel_agent.config as cfg
import travel_agent.api as api_mod
from travel_agent.prompt_audit import PROMPT_AUDIT
os.environ.pop('API_KEY', None)
cfg.API_KEY = None
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)

def test_itinerary_audit_recorded():
    PROMPT_AUDIT._records = []  # reset
    r = client.post("/api/mvp/plan", json={"session_id": "a1", "text": "从上海 预算2000 去杭州 2025-12-10 3天"})
    assert r.status_code == 200
    audit = client.get("/api/mvp/llm_audit").json()["audit"]
    assert any(rec["prompt_tag"] == "itinerary" for rec in audit)

def test_fail_json_audit_repair():
    PROMPT_AUDIT._records = []  # reset
    from travel_agent.llm_manager import llm_safe_json
    try:
        llm_safe_json("FAIL_JSON")
    except Exception:
        pass
    audit = client.get("/api/mvp/llm_audit").json()["audit"]
    # Should contain at least one invalid json record with error_code
    assert any((not rec["json_valid"] and rec["error_code"] == "LLM_JSON_INVALID") for rec in audit)