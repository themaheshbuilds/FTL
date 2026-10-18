from urllib.parse import urlparse
import re
from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService
from utils.logging import get_logger

logger = get_logger("linkforge.extractor.youtube")

YOUTUBE_PATTERN = re.compile(r"(?:www\.)?(?:youtube\.com|youtu\.be)", re.IGNORECASE)


class YouTubeExtractor(BaseExtractor):
    """Extractor for YouTube videos, shorts, and audio extraction."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(YOUTUBE_PATTERN.search(hostname))

    def analyze(self, url: str) -> AnalysisResult:
        logger.info(f"Analyzing YouTube URL: {url}")
        res = YtDlpService.analyze_url(url, platform_hint="YouTube")
        if res.success:
            return res

        return AnalysisResult(
            success=False,
            platform="YouTube",
            content_type="video",
            error_code=res.error_code or "YOUTUBE_FETCH_FAILED",
            error_message=res.error_message or "Unable to extract video streams from this YouTube URL. It may be private or restricted."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
