from fastapi.testclient import TestClient
import importlib, os
import travel_agent.config as cfg
import travel_agent.api as api_mod
from travel_agent.metrics import METRICS
os.environ.pop('API_KEY', None)
cfg.API_KEY = None
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)

def test_metrics_flow():
    METRICS.reset()
    # Trigger clarify session (missing destination)
    r1 = client.post("/api/mvp/plan", json={"session_id": "ms1", "text": "预算1000 2天"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["mode"] == "clarify"
    answers = []
    for q in data1["questions"]:
        if q["field"] == "destination":
            answers.append({"question_id": q["id"], "field": q["field"], "value": "北京"})
        elif q["field"] == "depart_date":
            answers.append({"question_id": q["id"], "field": q["field"], "value": "2025-12-15"})
        elif q["field"] == "origin":
            answers.append({"question_id": q["id"], "field": q["field"], "value": "广州"})
    r2 = client.post("/api/mvp/plan/clarify", json={"session_id": "ms1", "answers": answers})
    assert r2.status_code == 200
    # Direct plan complete (destination present)
    r3 = client.post("/api/mvp/plan", json={"session_id": "ms2", "text": "从广州 预算3000 去上海 2025-12-10 3天"})
    assert r3.status_code == 200
    m = client.get("/api/mvp/metrics").json()
    assert m["plan_requests"] == 2
    assert m["clarify_sessions"] >= 1
    assert m["clarify_rounds"] == 0  # answered all gaps in first round
    assert m["clarify_questions"] >= 2
    assert m["workflows_completed"] == 2
    assert m["workflow_avg_latency_ms"] >= 0