import os
import re
from urllib.parse import urlparse, unquote
from typing import Optional, Tuple, Dict, Any, List
import requests
from bs4 import BeautifulSoup
from config import Config
from models.result import AnalysisResult
from models.media import MediaItem
from utils.filenames import sanitize_filename
from utils.mime import normalize_content_type, categorize_mime_type, extension_for_mime_type
from utils.security import validate_url_security
from utils.logging import get_logger

logger = get_logger("linkforge.generic_downloader")


class GenericDownloader:
    """Handles direct file downloads, HTTP streaming, and OpenGraph metadata inspection."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        return {
            "User-Agent": cls.DEFAULT_USER_AGENT,
            "Accept": "*/*",
        }

    @classmethod
    def parse_content_disposition_filename(cls, content_disposition: Optional[str]) -> Optional[str]:
        """Extract filename from Content-Disposition header if present."""
        if not content_disposition:
            return None
        # Match filename*=utf-8''... or filename="..." or filename=...
        matches = re.findall(r'filename\*=UTF-8\'\'([^;]+)', content_disposition, re.IGNORECASE)
        if matches:
            return unquote(matches[0])
        matches = re.findall(r'filename=["\']?([^"\';]+)["\']?', content_disposition, re.IGNORECASE)
        if matches:
            return matches[0]
        return None

    @classmethod
    def extract_filename_from_url(cls, url: str) -> str:
        """Extract base filename from URL path."""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        base = os.path.basename(path)
        return base if base else "download_file"

    @classmethod
    def inspect_url(cls, url: str) -> Tuple[bool, Dict[str, Any]]:
        """Perform HTTP HEAD or range GET request to inspect headers safely."""
        is_safe, error_msg = validate_url_security(url)
        if not is_safe:
            return False, {"error": error_msg}

        headers = cls.get_headers()
        try:
            # First attempt HEAD request
            resp = requests.head(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=Config.DOWNLOAD_TIMEOUT_SECONDS
            )

            # If server forbids HEAD or doesn't provide Content-Type, fallback to GET with stream
            if resp.status_code >= 400 or "content-type" not in resp.headers:
                resp = requests.get(
                    url,
                    headers=headers,
                    stream=True,
                    allow_redirects=True,
                    timeout=Config.DOWNLOAD_TIMEOUT_SECONDS
                )
                resp.close()

            # Verify redirect destination hasn't redirected to internal IP (SSRF)
            is_redirect_safe, redirect_err = validate_url_security(resp.url)
            if not is_redirect_safe:
                return False, {"error": f"Redirect blocked: {redirect_err}"}

            content_type = normalize_content_type(resp.headers.get("Content-Type", ""))
            content_length = resp.headers.get("Content-Length")
            filesize = int(content_length) if content_length and content_length.isdigit() else None

            cd_filename = cls.parse_content_disposition_filename(resp.headers.get("Content-Disposition"))
            fallback_filename = cls.extract_filename_from_url(resp.url)
            raw_filename = cd_filename or fallback_filename

            # If filename lacks extension, supply from mime type
            stem, ext = os.path.splitext(raw_filename)
            if not ext:
                ext = extension_for_mime_type(content_type, "")
                raw_filename = f"{stem}{ext}"

            safe_name = sanitize_filename(raw_filename)

            return True, {
                "final_url": resp.url,
                "content_type": content_type,
                "category": categorize_mime_type(content_type),
                "filesize": filesize,
                "filename": safe_name,
                "status_code": resp.status_code,
            }
        except requests.RequestException as e:
            logger.warning(f"Error inspecting URL {url}: {e}")
            return False, {"error": f"Connection error: {e}"}

    @classmethod
    def analyze(cls, url: str) -> AnalysisResult:
        """Analyze direct file or HTML page via OpenGraph fallback."""
        ok, meta = cls.inspect_url(url)
        if not ok:
            return AnalysisResult(
                success=False,
                platform="Generic Web",
                content_type="unknown",
                error_code="CONNECTION_ERROR",
                error_message=meta.get("error", "Failed to connect to the target URL.")
            )

        category = meta.get("category", "unknown")
        content_type = meta.get("content_type", "")
        filename = meta.get("filename", "download_file")
        filesize = meta.get("filesize")

        # If it's a direct media/file download
        if category in ("image", "video", "audio", "document", "archive"):
            formats = ["original"]
            if category == "image":
                formats = ["original", "zip", "pdf"]
            elif category == "video":
                formats = ["mp4", "audio"]
            elif category == "archive":
                formats = ["original"]

            item = MediaItem(
                url=meta.get("final_url", url),
                media_type=category,
                filename=filename,
                mime_type=content_type,
                filesize=filesize,
                thumbnail_url=url if category == "image" else None,
            )

            return AnalysisResult(
                success=True,
                platform="Direct File",
                content_type="direct_file" if category in ("document", "archive") else category,
                media_count=1,
                formats=formats,
                items=[item],
                previews=[url] if category == "image" else [],
                title=filename
            )

        # If it's an HTML page, inspect for OpenGraph tags
        if "text/html" in content_type:
            return cls._inspect_opengraph(url)

        # Fallback unknown file
        item = MediaItem(
            url=meta.get("final_url", url),
            media_type="unknown",
            filename=filename,
            mime_type=content_type,
            filesize=filesize,
        )
        return AnalysisResult(
            success=True,
            platform="Generic Web",
            content_type="direct_file",
            media_count=1,
            formats=["original"],
            items=[item],
            title=filename
        )

    @classmethod
    def _inspect_opengraph(cls, url: str) -> AnalysisResult:
        """Scrape OpenGraph tags for public media links on HTML pages."""
        try:
            resp = requests.get(url, headers=cls.get_headers(), timeout=10)
            if not resp.ok:
                return AnalysisResult(
                    success=False,
                    platform="Generic Web",
                    content_type="unknown",
                    error_code="HTML_FETCH_FAILED",
                    error_message=f"Target web page returned status code {resp.status_code}."
                )

            soup = BeautifulSoup(resp.text, "html.parser")
            og_title = (soup.find("meta", property="og:title") or {}).get("content")
            og_image = (soup.find("meta", property="og:image") or {}).get("content")
            og_video = (soup.find("meta", property="og:video") or {}).get("content")

            items = []
            previews = []

            if og_video:
                previews.append(og_image if og_image else "")
                items.append(MediaItem(
                    url=og_video,
                    media_type="video",
                    filename="web_video.mp4",
                    mime_type="video/mp4",
                    title=og_title or "Web Video",
                    thumbnail_url=og_image
                ))
                return AnalysisResult(
                    success=True,
                    platform="Generic Web",
                    content_type="video",
                    media_count=1,
                    formats=["mp4", "audio"],
                    items=items,
                    previews=[p for p in previews if p],
                    title=og_title or "Web Video"
                )

            if og_image:
                previews.append(og_image)
                items.append(MediaItem(
                    url=og_image,
                    media_type="image",
                    filename="web_image.jpg",
                    mime_type="image/jpeg",
                    title=og_title or "Web Image",
                    thumbnail_url=og_image
                ))
                return AnalysisResult(
                    success=True,
                    platform="Generic Web",
                    content_type="image",
                    media_count=1,
                    formats=["original", "zip", "pdf"],
                    items=items,
                    previews=previews,
                    title=og_title or "Web Image"
                )

            return AnalysisResult(
                success=False,
                platform="Generic Web",
                content_type="unknown",
                error_code="NO_MEDIA_FOUND",
                error_message="No downloadable public media was found on this webpage."
            )

        except Exception as e:
            logger.warning(f"Failed to inspect OpenGraph for {url}: {e}")
            return AnalysisResult(
                success=False,
                platform="Generic Web",
                content_type="unknown",
                error_code="SCRAPE_ERROR",
                error_message="Could not analyze webpage content."
            )

    @classmethod
    def download_file(cls, url: str, target_dir: str, preferred_filename: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Stream download file directly to target directory with size limits.
        
        Returns:
            (success, downloaded_path, error_message)
        """
        is_safe, error_msg = validate_url_security(url)
        if not is_safe:
            return False, None, error_msg

        headers = cls.get_headers()
        try:
            with requests.get(url, headers=headers, stream=True, timeout=Config.DOWNLOAD_TIMEOUT_SECONDS) as r:
                r.raise_for_status()

                # Recheck redirect safety
                is_safe_redirect, redirect_err = validate_url_security(r.url)
                if not is_safe_redirect:
                    return False, None, redirect_err

                # Determine filename
                if preferred_filename:
                    final_filename = sanitize_filename(preferred_filename)
                else:
                    cd_name = cls.parse_content_disposition_filename(r.headers.get("Content-Disposition"))
                    url_name = cls.extract_filename_from_url(r.url)
                    content_type = normalize_content_type(r.headers.get("Content-Type", ""))
                    name_candidate = cd_name or url_name
                    stem, ext = os.path.splitext(name_candidate)
                    if not ext:
                        ext = extension_for_mime_type(content_type, "")
                        name_candidate = f"{stem}{ext}"
                    final_filename = sanitize_filename(name_candidate)

                dest_path = os.path.join(target_dir, final_filename)
                downloaded_bytes = 0

                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            downloaded_bytes += len(chunk)
                            if downloaded_bytes > Config.MAX_FILE_SIZE_BYTES:
                                f.close()
                                if os.path.exists(dest_path):
                                    os.remove(dest_path)
                                return False, None, "File exceeds maximum permitted size (500 MB limit)."
                            f.write(chunk)

                return True, dest_path, None

        except requests.RequestException as e:
            logger.error(f"Failed to stream download from {url}: {e}")
            return False, None, f"Download failed: {e}"
