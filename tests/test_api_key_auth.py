import os
from fastapi.testclient import TestClient
def fresh_client():
    # Re-import api to ensure dependency sees updated config
    import importlib
    import travel_agent.config as cfg
    import travel_agent.api as api_mod
    importlib.reload(cfg)
    importlib.reload(api_mod)
    return TestClient(api_mod.app)


def test_auth_disabled_when_no_key():
    # API_KEY not set by default, request should succeed (clarify) without header
    os.environ.pop('API_KEY', None)
    client = fresh_client()
    r = client.post('/api/mvp/plan', json={'session_id':'ak1','text':'预算1000 2天 去上海 2025-12-10'})
    assert r.status_code == 200


def test_auth_enabled_requires_header(monkeypatch):
    monkeypatch.setenv('API_KEY','secret123')
    # Need to re-import config values? Simulate by updating module variable
    client = fresh_client()
    # Missing header -> 401
    r1 = client.post('/api/mvp/plan', json={'session_id':'ak2','text':'预算1000 2天 去上海 2025-12-10'})
    assert r1.status_code == 401
    # Correct header -> 200
    r2 = client.post('/api/mvp/plan', json={'session_id':'ak3','text':'预算1000 2天 去上海 2025-12-10'}, headers={'X-API-Key':'secret123'})
    assert r2.status_code == 200
