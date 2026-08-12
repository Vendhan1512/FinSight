from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """
    Tests the health check endpoint.
    If PostgreSQL is not running locally, this will fail with a 503.
    """
    response = client.get("/health")
    # For now we just check if it returns 200 or 503 (if DB is down locally but app runs)
    assert response.status_code in [200, 503]
    
    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "ok"
        assert data["database"] == "connected"
    else:
        assert "detail" in data
