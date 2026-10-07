from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.generic_downloader import GenericDownloader


class GenericExtractor(BaseExtractor):
    """Fallback extractor for direct files and standard web links."""

    def can_handle(self, url: str) -> bool:
        return True  # Fallback extractor handles any URL

    def analyze(self, url: str) -> AnalysisResult:
        return GenericDownloader.analyze(url)

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
