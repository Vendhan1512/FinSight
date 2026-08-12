from fastapi.testclient import TestClient

def test_liveness(client: TestClient):
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_readiness(client: TestClient):
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        assert response.json()["status"] == "ok"

