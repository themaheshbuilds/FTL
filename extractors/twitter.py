from urllib.parse import urlparse
import re
from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService
from services.generic_downloader import GenericDownloader

TWITTER_PATTERN = re.compile(r"(?:www\.)?(?:twitter\.com|x\.com)", re.IGNORECASE)


class TwitterExtractor(BaseExtractor):
    """Extractor for X / Twitter tweets, videos, and image sets."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(TWITTER_PATTERN.search(hostname))

    def analyze(self, url: str) -> AnalysisResult:
        res = YtDlpService.analyze_url(url, platform_hint="Twitter / X")
        if res.success:
            return res

        og_res = GenericDownloader.analyze(url)
        if og_res.success:
            og_res.platform = "Twitter / X"
            return og_res

        return AnalysisResult(
            success=False,
            platform="Twitter / X",
            content_type="unknown",
            error_code="CONTENT_UNAVAILABLE",
            error_message="Unable to access X / Twitter content. Post may be restricted, deleted, or requires login."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
