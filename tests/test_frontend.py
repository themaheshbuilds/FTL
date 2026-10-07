import pytest
from app import create_app
from config import TestingConfig


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        yield client


def test_index_page_loads(client):
    """Test that GET / returns 200 and renders LinkForge homepage."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"LINKFORGE" in response.data
    assert b"One Link. Any File." in response.data
    assert b"url-input" in response.data
    assert b"analyze-btn" in response.data


def test_static_css_assets_accessible(client):
    """Test that static stylesheets are accessible."""
    res_style = client.get("/static/css/style.css")
    assert res_style.status_code == 200
    assert b"--brand-primary" in res_style.data

    res_comp = client.get("/static/css/components.css")
    assert res_comp.status_code == 200
    assert b".input-card" in res_comp.data


def test_static_js_assets_accessible(client):
    """Test that static JavaScript files are accessible."""
    res_app = client.get("/static/js/app.js")
    assert res_app.status_code == 200

    res_analyzer = client.get("/static/js/analyzer.js")
    assert res_analyzer.status_code == 200
    assert b"Analyzer" in res_analyzer.data

    res_downloader = client.get("/static/js/downloader.js")
    assert res_downloader.status_code == 200
    assert b"Downloader" in res_downloader.data
