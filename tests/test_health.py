import pytest
from app import create_app
from config import TestingConfig


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test that GET /health returns 200 and {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok"}


def test_api_404_not_found(client):
    """Test that a non-existent API route returns formatted JSON error."""
    response = client.get("/api/non-existent-endpoint")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


def test_web_404_not_found(client):
    """Test that a non-existent browser page renders styled HTML error."""
    response = client.get("/non-existent-page")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data
    assert b"Return to Home" in response.data
