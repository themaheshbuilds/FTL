from abc import ABC, abstractmethod
from typing import List, Optional
from models.result import AnalysisResult
from models.media import MediaItem


class BaseExtractor(ABC):
    """Abstract base class for all platform and generic extractors."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this extractor can process the given URL."""
        pass

    @abstractmethod
    def analyze(self, url: str) -> AnalysisResult:
        """Inspect the URL and return structured metadata without heavy downloads."""
        pass

    @abstractmethod
    def extract(self, url: str) -> List[MediaItem]:
        """Extract media items ready for packaging or saving."""
        pass
