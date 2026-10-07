from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from models.media import MediaItem


@dataclass
class AnalysisResult:
    """Standardized result returned by extractors and URL analyzer."""
    success: bool
    platform: str
    content_type: str  # 'image' | 'image_collection' | 'video' | 'video_collection' | 'mixed' | 'direct_file' | 'audio'
    media_count: int = 0
    formats: List[str] = field(default_factory=list)
    items: List[MediaItem] = field(default_factory=list)
    previews: List[str] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        if not self.success:
            return {
                "success": False,
                "error": {
                    "code": self.error_code or "ANALYSIS_FAILED",
                    "message": self.error_message or "Unable to analyze URL."
                }
            }

        return {
            "success": True,
            "platform": self.platform,
            "content_type": self.content_type,
            "media_count": self.media_count,
            "formats": self.formats,
            "previews": self.previews,
            "title": self.title,
            "description": self.description,
            "items": [item.to_dict() for item in self.items],
        }
