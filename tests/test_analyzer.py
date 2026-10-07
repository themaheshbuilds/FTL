import pytest
from services.platform_detector import PlatformDetector
from services.url_analyzer import UrlAnalyzer
from utils.validation import validate_url, normalize_url


def test_platform_detection():
    """Verify platform detection for various URLs."""
    test_cases = [
        ("https://www.youtube.com/watch?v=12345", "YouTube"),
        ("https://youtu.be/abcdef", "YouTube"),
        ("https://www.instagram.com/p/C-12345/", "Instagram"),
        ("https://tiktok.com/@user/video/123", "TikTok"),
        ("https://www.reddit.com/r/python/comments/123", "Reddit"),
        ("https://twitter.com/user/status/123", "Twitter"),
        ("https://x.com/user/status/123", "Twitter"),
        ("https://facebook.com/watch/?v=123", "Facebook"),
        ("https://www.linkedin.com/posts/activity-123", "LinkedIn"),
        ("https://example.com/assets/banner.png", "Direct File"),
        ("https://example.com/article", "Generic Web"),
    ]
    for url, expected_platform in test_cases:
        assert PlatformDetector.detect_platform(url) == expected_platform


def test_url_normalization():
    """Verify URL normalization behavior."""
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("HTTP://Example.COM:80/path#hash") == "http://example.com/path"
    assert normalize_url("https://example.com:443/docs") == "https://example.com/docs"


def test_analyzer_rejects_ssrf():
    """Verify UrlAnalyzer immediately rejects SSRF attempts without network call."""
    res = UrlAnalyzer.analyze_url("http://127.0.0.1/admin")
    assert res.success is False
    assert res.error_code == "INVALID_URL"
    assert "loopback" in res.error_message.lower() or "internal" in res.error_message.lower()
