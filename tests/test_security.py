import pytest
from utils.security import validate_url_security, is_ip_private_or_reserved


def test_ssrf_blocked_hostnames():
    """Ensure localhost and loopback hostnames are rejected."""
    bad_urls = [
        "http://localhost/secret",
        "https://127.0.0.1:8080/admin",
        "http://0.0.0.0/keys",
        "http://[::1]/internal",
        "http://metadata.google.internal/computeMetadata/v1/",
    ]
    for url in bad_urls:
        is_safe, msg = validate_url_security(url)
        assert is_safe is False
        assert len(msg) > 0


def test_ssrf_blocked_private_ips():
    """Ensure private network IPs are recognized and rejected."""
    private_ips = [
        "10.0.0.1",
        "172.16.0.5",
        "192.168.1.1",
        "169.254.169.254",  # AWS/GCP metadata
        "127.0.0.5",
    ]
    for ip in private_ips:
        assert is_ip_private_or_reserved(ip) is True
        is_safe, _ = validate_url_security(f"http://{ip}/info")
        assert is_safe is False


def test_unsafe_schemes_rejected():
    """Ensure non-http/https schemes are rejected."""
    unsafe_schemes = [
        "file:///etc/passwd",
        "file://c:/windows/system32/cmd.exe",
        "ftp://example.com/file.txt",
        "javascript:alert(1)",
        "data:text/html,<b>hi</b>",
    ]
    for url in unsafe_schemes:
        is_safe, msg = validate_url_security(url)
        assert is_safe is False


def test_safe_public_url():
    """Ensure standard public URLs are marked safe."""
    safe_urls = [
        "https://example.com/image.jpg",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://instagram.com/p/ABC123",
        "https://httpbin.org/get",
    ]
    for url in safe_urls:
        is_safe, _ = validate_url_security(url)
        assert is_safe is True
