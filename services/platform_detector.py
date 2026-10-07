from urllib.parse import urlparse
import re
from typing import Optional

PLATFORM_PATTERNS = [
    ("YouTube", re.compile(r"(?:www\.)?(?:youtube\.com|youtu\.be)")),
    ("Instagram", re.compile(r"(?:www\.)?instagram\.com")),
    ("TikTok", re.compile(r"(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)")),
    ("Reddit", re.compile(r"(?:www\.)?(?:reddit\.com|redd\.it)")),
    ("Twitter", re.compile(r"(?:www\.)?(?:twitter\.com|x\.com)")),
    ("Facebook", re.compile(r"(?:www\.)?(?:facebook\.com|fb\.watch)")),
    ("LinkedIn", re.compile(r"(?:[a-zA-Z0-9-]+\.)?(?:linkedin\.com|lnkd\.in)")),
    ("Pinterest", re.compile(r"(?:www\.)?(?:pinterest\.[a-z.]+|pin\.it)")),
    ("Threads", re.compile(r"(?:www\.)?threads\.net")),
    ("Vimeo", re.compile(r"(?:www\.)?vimeo\.com")),
    ("Twitch", re.compile(r"(?:www\.)?twitch\.tv")),
    ("Dailymotion", re.compile(r"(?:www\.)?dailymotion\.com")),
    ("SoundCloud", re.compile(r"(?:www\.)?soundcloud\.com")),
    ("Tumblr", re.compile(r"(?:[a-zA-Z0-9-]+\.)?tumblr\.com")),
    ("GitHub", re.compile(r"(?:www\.)?(?:github\.com|raw\.githubusercontent\.com)")),
    ("Google Drive", re.compile(r"drive\.google\.com")),
    ("Dropbox", re.compile(r"(?:www\.)?dropbox\.com")),
]

DIRECT_FILE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg",
    ".mp4", ".webm", ".mov", ".mkv",
    ".mp3", ".wav", ".ogg", ".aac",
    ".pdf", ".zip", ".tar", ".gz", ".docx", ".xlsx", ".csv", ".json", ".txt"
}


class PlatformDetector:
    """Detects platform and strategy from a normalized URL."""

    @staticmethod
    def detect_platform(url: str) -> str:
        """Identify platform name from URL."""
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        for name, pattern in PLATFORM_PATTERNS:
            if pattern.search(hostname):
                return name

        # Check if direct file extension
        path = parsed.path.lower()
        for ext in DIRECT_FILE_EXTENSIONS:
            if path.endswith(ext):
                return "Direct File"

        return "Generic Web"

    @staticmethod
    def is_direct_file(url: str) -> bool:
        """Check if URL directly points to a file extension."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in DIRECT_FILE_EXTENSIONS)
