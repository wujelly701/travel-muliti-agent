import importlib, os
from fastapi.testclient import TestClient
import travel_agent.config as cfg
import travel_agent.api as api_mod

os.environ.pop('API_KEY', None)
os.environ.pop('JWT_ENABLE', None)
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)


def test_plan_v3_graph_success():
    r = client.post('/api/mvp/plan_v3', json={'session_id':'gv3_1','text':'从上海 去杭州 2025-12-10 3天 预算3000'})
    assert r.status_code == 200
    body = r.json()
    assert body['success'] is True
    assert len(body['data']['flights']) >= 1
    assert len(body['data']['hotels']) >= 1


def test_plan_v3_clarify_when_missing_origin():
    r = client.post('/api/mvp/plan_v3', json={'session_id':'gv3_2','text':'去上海 2025-12-10 3天 预算3000'})
    assert r.status_code == 200
    body = r.json()
    assert body['success'] is False and body['mode'] == 'clarify'
    fields = [q['field'] for q in body['questions']]
    assert 'origin' in fields
