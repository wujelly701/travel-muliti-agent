from fastapi.testclient import TestClient
import importlib, os
import travel_agent.config as cfg
import travel_agent.api as api_mod
os.environ.pop('API_KEY', None)
cfg.API_KEY = None
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)

def test_error_destination_missing_recorded():
    # Start session missing destination & date, answer without destination for two rounds to trigger error
    sid = "err1"
    r1 = client.post("/api/mvp/plan", json={"session_id": sid, "text": "预算1000 3天"})
    assert r1.status_code == 200
    assert r1.json()["mode"] == "clarify"
    # First clarify: provide days (already) and budget only, omit destination & date
    questions1 = r1.json()["questions"]
    answers1 = []
    for q in questions1:
        if q["field"] == "budget_total":
            answers1.append({"question_id": q["id"], "field": q["field"], "value": "1000"})
        elif q["field"] == "days":
            answers1.append({"question_id": q["id"], "field": q["field"], "value": "3"})
    r2 = client.post("/api/mvp/plan/clarify", json={"session_id": sid, "answers": answers1})
    assert r2.status_code == 200
    # Second clarify still omit destination triggers error
    questions2 = r2.json()["questions"]
    answers2 = []
    for q in questions2:
        if q["field"] == "depart_date":
            answers2.append({"question_id": q["id"], "field": q["field"], "value": "2025-12-18"})
        # intentionally skip destination
    r3 = client.post("/api/mvp/plan/clarify", json={"session_id": sid, "answers": answers2})
    j3 = r3.json()
    assert j3["success"] is False
    assert j3["error"]["code"] == "INTENT_DESTINATION_MISSING"
    # Fetch errors endpoint
    errs = client.get("/api/mvp/errors?limit=10").json()["errors"]
    codes = [e["code"] for e in errs]
    assert "INTENT_DESTINATION_MISSING" in codes