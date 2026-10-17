import pytest
from api.index import VercelWSGIMiddleware
from app import create_app
from config import TestingConfig


@pytest.fixture
def wsgi_client():
    app = create_app(TestingConfig)
    app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
    with app.test_client() as client:
        yield client


def test_vercel_rewrite_root(wsgi_client):
    # Simulates Vercel rewrite for / -> /api/index
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/"})
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data


def test_vercel_rewrite_downloader(wsgi_client):
    # Simulates Vercel rewrite for /downloader -> /api/index
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/downloader"})
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data


def test_vercel_rewrite_converter(wsgi_client):
    # Simulates Vercel rewrite for /converter -> /api/index
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/converter"})
    assert res.status_code == 200
    assert b"converter-dropzone" in res.data


def test_vercel_rewrite_tool_converter(wsgi_client):
    # Simulates Vercel rewrite for /converter/pdf-to-images
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/converter/pdf-to-images"})
    assert res.status_code == 200
    assert b"PDF to Images" in res.data


def test_vercel_rewrite_api_analyze(wsgi_client):
    # Simulates Vercel rewrite for POST /api/analyze
    res = wsgi_client.post("/api/index", headers={"X-Matched-Path": "/api/analyze"}, json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_URL"


def test_vercel_rewrite_direct_api_index_fallback(wsgi_client):
    # Simulates Vercel invoking /api/index directly without X-Matched-Path
    res = wsgi_client.get("/api/index")
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data
