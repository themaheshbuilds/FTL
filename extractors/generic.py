from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.generic_downloader import GenericDownloader
from services.ytdlp_service import YtDlpService
from utils.logging import get_logger

logger = get_logger("linkforge.generic_extractor")


class GenericExtractor(BaseExtractor):
    """Fallback extractor for direct files and standard web links."""

    def can_handle(self, url: str) -> bool:
        return True  # Fallback extractor handles any URL

    def analyze(self, url: str) -> AnalysisResult:
        res = GenericDownloader.analyze(url)
        if res.success:
            return res

        # Fallback to yt-dlp if direct file/opengraph extraction didn't yield media
        try:
            yt_res = YtDlpService.analyze_url(url, platform_hint="Web Media")
            if yt_res.success:
                return yt_res
        except Exception as e:
            logger.debug(f"yt-dlp generic fallback failed for {url}: {e}")

        return res

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
