import re
from urllib.parse import urlparse, urlunparse
from typing import Tuple
from utils.security import validate_url_security


def normalize_url(url: str) -> str:
    """Normalize a given URL string."""
    cleaned = url.strip()
    if not cleaned:
        return ""

    # Prepend https:// if protocol is missing
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned):
        cleaned = "https://" + cleaned

    parsed = urlparse(cleaned)

    # Lowercase scheme and netloc, strip default ports
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]

    # Reconstruct normalized URL
    normalized = urlunparse((
        scheme,
        netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        ""  # Remove fragment (#...) as it is client-only
    ))
    return normalized


def validate_url(url: str) -> Tuple[bool, str, str]:
    """Validate and normalize a URL.
    
    Returns:
        (is_valid, normalized_url, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "", "URL is required."

    normalized = normalize_url(url)
    if not normalized:
        return False, "", "URL cannot be empty."

    # Validate security constraints (SSRF, protocols)
    is_safe, error_msg = validate_url_security(normalized)
    if not is_safe:
        return False, "", error_msg

    return True, normalized, ""
