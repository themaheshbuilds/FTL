from urllib.parse import urlparse
import re
from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService
from services.generic_downloader import GenericDownloader

REDDIT_PATTERN = re.compile(r"(?:www\.)?(?:reddit\.com|redd\.it)", re.IGNORECASE)


class RedditExtractor(BaseExtractor):
    """Extractor for Reddit video posts, image galleries, and links."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(REDDIT_PATTERN.search(hostname))

    def analyze(self, url: str) -> AnalysisResult:
        res = YtDlpService.analyze_url(url, platform_hint="Reddit")
        if res.success:
            return res

        og_res = GenericDownloader.analyze(url)
        if og_res.success:
            og_res.platform = "Reddit"
            return og_res

        return AnalysisResult(
            success=False,
            platform="Reddit",
            content_type="unknown",
            error_code="CONTENT_UNAVAILABLE",
            error_message="Unable to access Reddit post. Content may be restricted, private, or removed."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
