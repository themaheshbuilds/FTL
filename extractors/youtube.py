from urllib.parse import urlparse
import re
from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService

YOUTUBE_PATTERN = re.compile(r"(?:www\.)?(?:youtube\.com|youtu\.be)", re.IGNORECASE)


class YouTubeExtractor(BaseExtractor):
    """Extractor for YouTube videos, shorts, and playlists."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(YOUTUBE_PATTERN.search(hostname))

    def analyze(self, url: str) -> AnalysisResult:
        result = YtDlpService.analyze_url(url, platform_hint="YouTube")
        # Ensure YouTube specific formatting
        if result.success and "mp4" not in result.formats:
            result.formats.append("mp4")
        if result.success and "audio" not in result.formats:
            result.formats.append("audio")
        return result

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
