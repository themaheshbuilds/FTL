from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class MediaItem:
    """Represents a single extracted media item."""
    url: str
    media_type: str  # 'image' | 'video' | 'audio' | 'document' | 'unknown'
    filename: str = "media_item"
    mime_type: str = "application/octet-stream"
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    filesize: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    local_path: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "media_type": self.media_type,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "title": self.title,
            "thumbnail_url": self.thumbnail_url,
            "filesize": self.filesize,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
        }
