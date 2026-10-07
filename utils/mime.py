import mimetypes
from typing import Tuple

MIME_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-matroska": ".mkv",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/aac": ".aac",
    "application/pdf": ".pdf",
    "application/zip": ".zip",
    "application/x-zip-compressed": ".zip",
    "application/x-rar-compressed": ".rar",
    "application/x-tar": ".tar",
    "application/gzip": ".tar.gz",
}


def normalize_content_type(content_type: str) -> str:
    """Strip charset and parameters from Content-Type header."""
    if not content_type:
        return "application/octet-stream"
    return content_type.split(";")[0].strip().lower()


def categorize_mime_type(content_type: str) -> str:
    """Categorize a MIME type into standard LinkForge media types:
    image | video | audio | document | archive | unknown
    """
    clean_type = normalize_content_type(content_type)

    if clean_type.startswith("image/"):
        return "image"
    if clean_type.startswith("video/"):
        return "video"
    if clean_type.startswith("audio/"):
        return "audio"
    if clean_type in ("application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        return "document"
    if "zip" in clean_type or "tar" in clean_type or "compressed" in clean_type:
        return "archive"

    return "unknown"


def extension_for_mime_type(content_type: str, fallback_ext: str = "") -> str:
    """Get the preferred file extension for a MIME type."""
    clean_type = normalize_content_type(content_type)
    if clean_type in MIME_TO_EXTENSION:
        return MIME_TO_EXTENSION[clean_type]
    ext = mimetypes.guess_extension(clean_type)
    return ext or fallback_ext
