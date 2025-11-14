import os, importlib
from fastapi.testclient import TestClient
import travel_agent.config as cfg
import travel_agent.api as api_mod


def fresh_client():
    importlib.reload(cfg)
    importlib.reload(api_mod)
    return TestClient(api_mod.app)


def test_jwt_disabled_token_endpoint_reject():
    os.environ.pop('JWT_ENABLE', None)
    c = fresh_client()
    r = c.post('/api/mvp/auth/token', data={'username':'demo','password':'demo123'})
    assert r.status_code == 400  # disabled


def test_jwt_enabled_flow():
    os.environ['JWT_ENABLE'] = 'true'
    os.environ['AUTH_DEMO_USER'] = 'demo'
    os.environ['AUTH_DEMO_PASSWORD'] = 'demo123'
    os.environ['AUTH_JWT_SECRET'] = 'test-secret'
    c = fresh_client()
    # issue token
    r = c.post('/api/mvp/auth/token', data={'username':'demo','password':'demo123'})
    assert r.status_code == 200
    token = r.json()['access_token']
    # use token for plan (missing origin triggers clarify) - authorized
    r2 = c.post('/api/mvp/plan', json={'session_id':'jwt1','text':'预算1000 去上海 3天 2025-12-10'}, headers={'Authorization': f'Bearer {token}'})
    assert r2.status_code == 200
    # invalid token
    r3 = c.post('/api/mvp/plan', json={'session_id':'jwt2','text':'预算1000 去上海 3天 2025-12-10'}, headers={'Authorization': 'Bearer badtoken'})
    assert r3.status_code == 401
