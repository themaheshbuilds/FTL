from typing import List, Optional
from extractors.base import BaseExtractor
from extractors.youtube import YouTubeExtractor
from extractors.instagram import InstagramExtractor
from extractors.twitter import TwitterExtractor
from extractors.reddit import RedditExtractor
from extractors.facebook import FacebookExtractor
from extractors.linkedin import LinkedInExtractor
from extractors.generic import GenericExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from utils.logging import get_logger

logger = get_logger("linkforge.extraction_service")


class ExtractionService:
    """Orchestrates extractor selection and execution."""

    def __init__(self):
        # Specific extractors in priority order, with GenericExtractor as final fallback
        self.extractors: List[BaseExtractor] = [
            YouTubeExtractor(),
            InstagramExtractor(),
            TwitterExtractor(),
            RedditExtractor(),
            FacebookExtractor(),
            LinkedInExtractor(),
            GenericExtractor(),
        ]

    def get_extractor_for_url(self, url: str) -> BaseExtractor:
        """Find the first matching extractor that can handle the URL."""
        for extractor in self.extractors:
            if extractor.can_handle(url):
                return extractor
        return self.extractors[-1]  # Generic fallback

    def analyze(self, url: str) -> AnalysisResult:
        """Analyze URL through the selected extractor."""
        extractor = self.get_extractor_for_url(url)
        logger.info(f"Using {extractor.__class__.__name__} to analyze {url}")
        return extractor.analyze(url)

    def extract(self, url: str) -> List[MediaItem]:
        """Extract media through the selected extractor."""
        extractor = self.get_extractor_for_url(url)
        return extractor.extract(url)


# Global singleton instance
extraction_service = ExtractionService()
