from fastapi.testclient import TestClient
from travel_agent.api import app

client = TestClient(app)

def test_health_alias_and_mvp():
    r1 = client.get('/health')
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1['status'] == 'healthy'
    assert data1['service'] == 'Travel Agent MVP'

    r2 = client.get('/api/mvp/health')
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2['status'] == 'healthy'
    assert data2['service'] == 'Travel Agent MVP'
