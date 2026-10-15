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

    res_tool = client.get("/static/js/tool_converter.js")
    assert res_tool.status_code == 200
    assert b"DedicatedToolConverter" in res_tool.data


def test_downloader_page_loads(client):
    """Test that GET /downloader loads the dedicated downloader page."""
    response = client.get("/downloader")
    assert response.status_code == 200
    assert b"LINKFORGE" in response.data
    assert b"url-input" in response.data
    assert b"analyze-btn" in response.data


def test_converter_hub_page_loads(client):
    """Test that GET /converter loads the converter hub page."""
    response = client.get("/converter")
    assert response.status_code == 200
    assert b"LINKFORGE" in response.data
    assert b"converter-dropzone" in response.data


@pytest.mark.parametrize("slug,expected_title", [
    ("pdf-to-images", b"PDF to Images"),
    ("images-to-pdf", b"Images to PDF"),
    ("video-to-audio", b"Video to Audio"),
    ("docx-to-pdf", b"Word (DOCX) to PDF"),
    ("pdf-to-docx", b"PDF to Word (DOCX)"),
    ("video-converter", b"Video Transcoder"),
    ("image-converter", b"Image Converter"),
])
def test_dedicated_tool_pages_load(client, slug, expected_title):
    """Test that each separate converter tool page loads with correct title."""
    response = client.get(f"/converter/{slug}")
    assert response.status_code == 200
    assert expected_title in response.data
    assert b"tool-dropzone" in response.data
    assert b"tool_converter.js" in response.data


def test_unknown_converter_tool_returns_404(client):
    """Test that an invalid tool slug returns 404."""
    response = client.get("/converter/non-existent-tool")
    assert response.status_code == 404

