import pytest
from utils.filenames import sanitize_filename, generate_unique_filename


def test_sanitize_path_traversal():
    """Ensure path traversal attacks are neutralized."""
    evil_cases = [
        ("../../../evil.exe", "evil.exe"),
        ("..\\..\\windows\\system32\\calc.exe", "calc.exe"),
        ("/etc/passwd", "passwd"),
        ("C:\\secret\\data.zip", "data.zip"),
    ]
    for raw, expected in evil_cases:
        cleaned = sanitize_filename(raw)
        assert cleaned == expected
        assert "/" not in cleaned
        assert "\\" not in cleaned
        assert not cleaned.startswith("..")


def test_sanitize_illegal_characters():
    """Ensure characters invalid in file systems are sanitized."""
    bad_name = 'cool:video*name?"test|<>.mp4'
    cleaned = sanitize_filename(bad_name)
    assert ":" not in cleaned
    assert "*" not in cleaned
    assert "?" not in cleaned
    assert '"' not in cleaned
    assert "|" not in cleaned
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert cleaned.endswith(".mp4")


def test_sanitize_empty_or_whitespace():
    """Ensure fallback filename is provided if name is empty."""
    assert sanitize_filename("") == "download_file"
    assert sanitize_filename("   ") == "download_file"
    assert sanitize_filename(None) == "download_file"


def test_generate_unique_filename():
    """Ensure duplicate filenames are safely incremented."""
    existing = {"photo.jpg", "photo_1.jpg"}
    unique = generate_unique_filename("photo.jpg", existing)
    assert unique == "photo_2.jpg"
