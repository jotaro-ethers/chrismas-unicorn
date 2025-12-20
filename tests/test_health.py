from fastapi.testclient import TestClient


def test_root_returns_hello_world(client: TestClient):
    """Test root endpoint returns Hello World."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_check(client: TestClient):
    """Test health check endpoint returns 200 with correct schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_health_ready(client: TestClient):
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "database" in data
    assert "timestamp" in data
