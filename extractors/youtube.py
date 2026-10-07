from urllib.parse import urlparse
import re
from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService

YOUTUBE_PATTERN = re.compile(r"(?:www\.)?(?:youtube\.com|youtu\.be)", re.IGNORECASE)


class YouTubeExtractor(BaseExtractor):
    """Extractor for YouTube videos, shorts, and playlists (Coming Soon)."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(YOUTUBE_PATTERN.search(hostname))

    def analyze(self, url: str) -> AnalysisResult:
        return AnalysisResult(
            success=False,
            platform="YouTube",
            content_type="unknown",
            error_code="COMING_SOON",
            error_message="YouTube video downloader is coming soon! We are actively working on it."
        )

    def extract(self, url: str) -> List[MediaItem]:
        return []
