from fastapi.testclient import TestClient
import importlib, os
import travel_agent.config as cfg
import travel_agent.api as api_mod
os.environ.pop('API_KEY', None)
cfg.API_KEY = None
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)

def test_prometheus_metrics_endpoint():
    # trigger a plan needing clarify and complete
    r1 = client.post("/api/mvp/plan", json={"session_id": "p1", "text": "预算500 2天"})
    qdata = r1.json()["questions"]
    answers = []
    for q in qdata:
        if q["field"] == "destination":
            answers.append({"question_id": q["id"], "field": q["field"], "value": "广州"})
        elif q["field"] == "depart_date":
            answers.append({"question_id": q["id"], "field": q["field"], "value": "2025-12-20"})
    client.post("/api/mvp/plan/clarify", json={"session_id": "p1", "answers": answers})
    # direct complete second
    client.post("/api/mvp/plan", json={"session_id": "p2", "text": "预算800 去深圳 2025-12-22 3天"})
    prom = client.get("/api/mvp/prom_metrics")
    assert prom.status_code == 200
    body = prom.text
    assert "plan_requests_total" in body
    assert "workflows_completed_total" in body