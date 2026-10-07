from dataclasses import dataclass, field
import time
from typing import Optional, Dict, Any


@dataclass
class Job:
    """Represents a packaging or download job."""
    job_id: str
    url: str
    requested_format: str
    status: str = "queued"  # queued | analyzing | extracting | downloading | processing | completed | failed | expired
    output_filename: Optional[str] = None
    output_file_path: Optional[str] = None
    filesize: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "url": self.url,
            "requested_format": self.requested_format,
            "status": self.status,
            "filename": self.output_filename,
            "filesize": self.filesize,
            "mime_type": self.mime_type,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }
