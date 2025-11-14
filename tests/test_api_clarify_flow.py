from fastapi.testclient import TestClient
import importlib, os
import travel_agent.config as cfg
import travel_agent.api as api_mod

# Disable API key for this test by clearing env then reloading modules
os.environ.pop('API_KEY', None)
cfg.API_KEY = None
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)


def test_clarify_flow():
    # Missing origin & destination & date explicit: only budget + days present
    resp = client.post("/api/mvp/plan", json={"session_id": "sessA", "text": "预算2000 3天"})
    data = resp.json()
    assert data["success"] is False
    assert data["mode"] == "clarify"
    qs = data["questions"]
    # origin & destination should be among gaps
    fields = {q['field'] for q in qs}
    assert 'origin' in fields
    assert 'destination' in fields

    # Provide answers
    answers = []
    for q in qs:
        if q['field'] == 'origin':
            val = '北京'
        elif q['field'] == 'destination':
            val = '东京'
        elif q['field'] == 'depart_date':
            val = '2025-12-10'
        elif q['field'] == 'days':
            val = '3'
        elif q['field'] == 'budget_total':
            val = '2000'
        else:
            val = 'X'
        answers.append({"question_id": q["id"], "field": q["field"], "value": val})
    resp2 = client.post("/api/mvp/plan/clarify", json={"session_id": "sessA", "answers": answers})
    data2 = resp2.json()
    if data2.get("mode") == "clarify":
        # second round, answer remaining
        answers2 = []
        for q in data2['questions']:
            if q['field'] == 'origin':
                val = '北京'
            elif q['field'] == 'destination':
                val = '东京'
            elif q['field'] == 'depart_date':
                val = '2025-12-10'
            elif q['field'] == 'days':
                val = '3'
            elif q['field'] == 'budget_total':
                val = '2000'
            else:
                val = 'X'
            answers2.append({"question_id": q["id"], "field": q["field"], "value": val})
        data2 = client.post("/api/mvp/plan/clarify", json={"session_id": "sessA", "answers": answers2}).json()
    assert data2["success"] is True
    assert data2["data"]["schema_version"] == "1.0"
