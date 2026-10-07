import pytest
from unittest.mock import patch, MagicMock
from extractors.linkedin import LinkedInExtractor
from services.platform_detector import PlatformDetector
from models.result import AnalysisResult


def test_linkedin_can_handle_domains():
    extractor = LinkedInExtractor()
    assert extractor.can_handle("https://www.linkedin.com/posts/test-post-123/")
    assert extractor.can_handle("https://in.linkedin.com/posts/test-post-123/")
    assert extractor.can_handle("https://lnkd.in/p/d44WFrce")
    assert extractor.can_handle("http://lnkd.in/abc")
    assert not extractor.can_handle("https://www.instagram.com/p/123/")
    assert not extractor.can_handle("https://youtube.com/watch?v=123")


def test_platform_detector_linkedin_shortlink():
    assert PlatformDetector.detect_platform("https://lnkd.in/p/d44WFrce") == "LinkedIn"
    assert PlatformDetector.detect_platform("https://www.linkedin.com/posts/test") == "LinkedIn"


def test_linkedin_multipage_document_extraction():
    extractor = LinkedInExtractor()
    fake_images = [{"@type": "ImageObject", "url": f"https://media.licdn.com/image_{i}.jpg"} for i in range(1, 21)]
    fake_json_ld = {
        "@type": "SocialMediaPosting",
        "headline": "DSA Full Notes Document",
        "image": fake_images
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = f'''<html><head>
    <script type="application/ld+json">{str(fake_json_ld).replace("'", '"')}</script>
    </head><body></body></html>'''

    with patch("extractors.linkedin.requests.get", return_value=mock_resp):
        res = extractor.analyze("https://lnkd.in/p/d44WFrce")
        assert res.success is True
        assert res.platform == "LinkedIn"
        assert res.content_type == "image_collection"
        assert res.media_count == 20
        assert "pdf" in res.formats
        assert "zip" in res.formats
        assert len(res.items) == 20
        assert res.items[0].filename == "page_01.jpg"
        assert res.items[19].filename == "page_20.jpg"
        assert res.items[0].url == "https://media.licdn.com/image_1.jpg"
        assert res.items[19].url == "https://media.licdn.com/image_20.jpg"


def test_linkedin_single_image_extraction():
    extractor = LinkedInExtractor()
    fake_json_ld = {
        "@type": "SocialMediaPosting",
        "headline": "Single Image Announcement",
        "image": [{"@type": "ImageObject", "url": "https://media.licdn.com/single.jpg"}]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = f'''<html><head>
    <script type="application/ld+json">{str(fake_json_ld).replace("'", '"')}</script>
    </head><body></body></html>'''

    with patch("extractors.linkedin.requests.get", return_value=mock_resp):
        res = extractor.analyze("https://www.linkedin.com/posts/single-image")
        assert res.success is True
        assert res.content_type == "image"
        assert res.media_count == 1
        assert res.items[0].filename == "page_01.jpg"


def test_linkedin_unavailable():
    extractor = LinkedInExtractor()
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("extractors.linkedin.requests.get", return_value=mock_resp):
        with patch("services.ytdlp_service.YtDlpService.analyze_url", return_value=AnalysisResult(success=False, platform="LinkedIn", content_type="unknown")):
            with patch("services.generic_downloader.GenericDownloader.analyze", return_value=AnalysisResult(success=False, platform="LinkedIn", content_type="unknown")):
                res = extractor.analyze("https://lnkd.in/p/nonexistent")
                assert res.success is False
                assert res.error_code == "CONTENT_UNAVAILABLE"


def test_linkedin_video_with_data_sources_and_poster_image():
    """Verify that LinkedIn video posts with poster thumbnails are extracted as video, not image."""
    extractor = LinkedInExtractor()
    html = '''<html><head>
        <meta property="og:title" content="Exciting Machine Learning Announcement | LinkedIn">
        <meta property="og:image" content="https://media.licdn.com/dms/image/poster.jpg">
    </head><body>
        <video data-poster-url="https://media.licdn.com/dms/image/poster.jpg"
               data-sources='[
                   {"src": "https://dms.licdn.com/playlist/vid/v2/low.mp4", "type": "video/mp4", "data-bitrate": 300000},
                   {"src": "https://dms.licdn.com/playlist/vid/v2/high.mp4", "type": "video/mp4", "data-bitrate": 1500000}
               ]'>
        </video>
    </body></html>'''

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_resp.url = "https://www.linkedin.com/posts/ml-announcement"

    with patch("extractors.linkedin.requests.get", return_value=mock_resp):
        res = extractor.analyze("https://www.linkedin.com/posts/ml-announcement")
        assert res.success is True
        assert res.platform == "LinkedIn"
        assert res.content_type == "video"
        assert res.media_count == 1
        assert "mp4" in res.formats
        assert "audio" in res.formats
        assert len(res.items) == 1
        assert res.items[0].media_type == "video"
        assert res.items[0].url == "https://dms.licdn.com/playlist/vid/v2/high.mp4"
        assert res.items[0].thumbnail_url == "https://media.licdn.com/dms/image/poster.jpg"
        assert res.items[0].filename.endswith(".mp4")


def test_linkedin_video_og_video_tag():
    """Verify that og:video meta tags are recognized as video."""
    extractor = LinkedInExtractor()
    html = '''<html><head>
        <meta property="og:title" content="Tech Demo">
        <meta property="og:video" content="https://dms.licdn.com/playlist/vid/demo.mp4">
        <meta property="og:image" content="https://media.licdn.com/demo_thumb.jpg">
    </head><body></body></html>'''

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_resp.url = "https://www.linkedin.com/posts/demo"

    with patch("extractors.linkedin.requests.get", return_value=mock_resp):
        res = extractor.analyze("https://www.linkedin.com/posts/demo")
        assert res.success is True
        assert res.content_type == "video"
        assert res.items[0].media_type == "video"
        assert res.items[0].url == "https://dms.licdn.com/playlist/vid/demo.mp4"

