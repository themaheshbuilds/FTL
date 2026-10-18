import pytest
from app import create_app, VercelWSGIMiddleware
from config import TestingConfig


@pytest.fixture
def wsgi_client():
    app = create_app(TestingConfig)
    app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
    with app.test_client() as client:
        yield client


# Tests for ?__route= parameter routing (Vercel rewrite capture group)
def test_vercel_route_param_root(wsgi_client):
    res = wsgi_client.get("/api/index?__route=/")
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data
    assert b"Universal Downloader" in res.data


def test_vercel_route_param_downloader(wsgi_client):
    res = wsgi_client.get("/api/index?__route=/downloader")
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data
    assert b"Download anything" in res.data


def test_vercel_route_param_converter(wsgi_client):
    res = wsgi_client.get("/api/index?__route=/converter")
    assert res.status_code == 200
    assert b"converter-dropzone" in res.data


def test_vercel_route_param_files_alias(wsgi_client):
    res = wsgi_client.get("/api/index?__route=/files")
    assert res.status_code == 200
    assert b"converter-dropzone" in res.data


def test_vercel_route_param_tool_converter(wsgi_client):
    res = wsgi_client.get("/api/index?__route=/converter/pdf-to-images")
    assert res.status_code == 200
    assert b"PDF to Images" in res.data


def test_vercel_route_param_api_analyze(wsgi_client):
    res = wsgi_client.post("/api/index?__route=/api/analyze", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_URL"


# Tests for X-Matched-Path header fallback
def test_vercel_rewrite_root(wsgi_client):
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/"})
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data


def test_vercel_rewrite_downloader(wsgi_client):
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/downloader"})
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data


def test_vercel_rewrite_converter(wsgi_client):
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/converter"})
    assert res.status_code == 200
    assert b"converter-dropzone" in res.data


def test_vercel_rewrite_tool_converter(wsgi_client):
    res = wsgi_client.get("/api/index", headers={"X-Matched-Path": "/converter/pdf-to-images"})
    assert res.status_code == 200
    assert b"PDF to Images" in res.data


def test_vercel_rewrite_api_analyze(wsgi_client):
    res = wsgi_client.post("/api/index", headers={"X-Matched-Path": "/api/analyze"}, json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_URL"


def test_vercel_rewrite_direct_api_index_fallback(wsgi_client):
    res = wsgi_client.get("/api/index")
    assert res.status_code == 200
    assert b"LINKFORGE" in res.data
