import os
import pytest
from app import create_app
from config import TestingConfig
from services.job_service import JobService


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        yield client


def test_api_analyze_missing_url(client):
    """Test POST /api/analyze with missing or invalid URL payload."""
    res = client.post("/api/analyze", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_URL"


def test_api_analyze_invalid_scheme(client):
    """Test POST /api/analyze with blocked scheme."""
    res = client.post("/api/analyze", json={"url": "file:///etc/passwd"})
    assert res.status_code == 422
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_URL"


def test_api_generate_missing_url(client):
    """Test POST /api/generate with missing URL."""
    res = client.post("/api/generate", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_URL"


def test_download_endpoint_invalid_id(client):
    """Test GET /download/<file_id> with path traversal or invalid id."""
    res = client.get("/download/../../evil")
    # Flask route will either return 404 or our handler blocks it
    assert res.status_code in (400, 404)


def test_download_endpoint_nonexistent_job(client):
    """Test GET /download/<file_id> with unknown job id."""
    res = client.get("/download/abcdef123456")
    assert res.status_code == 404
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "EXPIRED_OR_NOT_FOUND"


def test_download_endpoint_successful_delivery(client, tmp_path):
    """Test GET /download/<file_id> delivers actual file."""
    # Create a job and dummy output file
    job = JobService.create_job("https://example.com/test", "original")
    dummy_file = tmp_path / "hello.txt"
    dummy_file.write_text("Hello LinkForge!")

    JobService.update_job_success(
        job.job_id,
        output_path=str(dummy_file),
        filename="hello.txt",
        mime_type="text/plain",
        filesize=dummy_file.stat().st_size
    )

    res = client.get(f"/download/{job.job_id}")
    assert res.status_code == 200
    assert res.data == b"Hello LinkForge!"
    assert "attachment" in res.headers.get("Content-Disposition", "")
