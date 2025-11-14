from fastapi.testclient import TestClient
import importlib, os
import travel_agent.config as cfg
import travel_agent.api as api_mod
from travel_agent.metrics import METRICS_PARALLEL

# ensure open mode
os.environ.pop('API_KEY', None)
os.environ.pop('JWT_ENABLE', None)
importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)

def test_plan_v2_parallel_success():
    before = METRICS_PARALLEL.snapshot()['parallel_runs']
    r = client.post('/api/mvp/plan_v2', json={'session_id':'pv2_1','text':'从上海 去杭州 2025-12-10 3天 预算3000'})
    assert r.status_code == 200
    data = r.json()
    assert data['success'] is True
    assert len(data['data']['flights']) >= 1
    assert len(data['data']['hotels']) >= 1
    after = METRICS_PARALLEL.snapshot()['parallel_runs']
    assert after == before + 1


def test_plan_v2_clarify_missing_origin():
    r = client.post('/api/mvp/plan_v2', json={'session_id':'pv2_2','text':'去上海 2025-12-10 3天 预算3000'})
    assert r.status_code == 200
    body = r.json()
    assert body['success'] is False and body['mode'] == 'clarify'
    fields = [q['field'] for q in body['questions']]
    assert 'origin' in fields
