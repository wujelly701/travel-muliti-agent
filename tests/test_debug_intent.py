from fastapi.testclient import TestClient
import importlib
import travel_agent.config as cfg
import travel_agent.api as api_mod

importlib.reload(cfg)
importlib.reload(api_mod)
client = TestClient(api_mod.app)

def test_debug_intent_missing_origin():
    r = client.post('/api/mvp/debug/intent', json={'session_id':'dbg1','text':'预算1500 去上海 2025-12-10 3天'})
    assert r.status_code == 200
    data = r.json()
    assert 'origin' in data['gaps']
    assert data['intent']['destination'] == '上海'


def test_debug_intent_full():
    r = client.post('/api/mvp/debug/intent', json={'session_id':'dbg2','text':'从北京 预算1500 去上海 2025-12-10 3天'})
    assert r.status_code == 200
    data = r.json()
    assert data['gaps'] == []
    assert data['intent']['origin'] == '北京'
