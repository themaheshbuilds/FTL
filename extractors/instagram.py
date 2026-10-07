from urllib.parse import urlparse
import re
from typing import List, Optional, Dict, Any
import yt_dlp
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService
from services.generic_downloader import GenericDownloader
from utils.filenames import sanitize_filename
from utils.logging import get_logger

logger = get_logger("linkforge.extractors.instagram")
INSTAGRAM_PATTERN = re.compile(r"(?:www\.)?instagram\.com", re.IGNORECASE)


class InstagramExtractor(BaseExtractor):
    """Extractor for Instagram posts, reels, and carousel collections."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(INSTAGRAM_PATTERN.search(hostname))

    def _extract_via_instagram_ie(self, url: str) -> Optional[AnalysisResult]:
        """Extract media using yt-dlp's InstagramIE directly.
        
        This handles both single posts (photos and videos) and multi-item carousels,
        retaining full-resolution image URLs that standard yt-dlp video extractors
        discard when format checks fail on static photos.
        """
        opts = YtDlpService.get_default_opts({"skip_download": True, "quiet": True})
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ie = ydl.get_info_extractor("Instagram")
                ie.initialize()

                # Override raise_no_formats so single photo posts return metadata instead of raising ExtractorError
                orig_raise_no_formats = ie.raise_no_formats
                ie.raise_no_formats = lambda msg, expected=True: None
                try:
                    info = ie._real_extract(url)
                finally:
                    ie.raise_no_formats = orig_raise_no_formats

            if not info or not isinstance(info, dict):
                return None

            title = info.get("title") or "Instagram Media"
            description = info.get("description")
            entries = info.get("entries")

            if entries and isinstance(entries, list):
                items: List[MediaItem] = []
                previews: List[str] = []
                has_videos = False
                has_images = False

                for idx, entry in enumerate(entries):
                    if not entry:
                        continue
                    entry_id = entry.get("id") or f"media_{idx + 1}"
                    formats = entry.get("formats") or []
                    thumbnails = entry.get("thumbnails") or []
                    is_video = bool(formats)

                    if is_video:
                        has_videos = True
                        direct_url = formats[-1].get("url")
                        ext = "mp4"
                        mime = "video/mp4"
                        media_type = "video"
                        thumb = thumbnails[-1].get("url") if thumbnails else None
                    else:
                        has_images = True
                        # The last thumbnail in yt-dlp candidates is the highest resolution original image
                        direct_url = thumbnails[-1].get("url") if thumbnails else None
                        ext = "jpg"
                        mime = "image/jpeg"
                        media_type = "image"
                        thumb = thumbnails[0].get("url") if thumbnails else direct_url

                    if not direct_url:
                        continue

                    if thumb and thumb not in previews:
                        previews.append(thumb)

                    item_title = f"{title}_{idx + 1}"
                    item = MediaItem(
                        url=direct_url,
                        media_type=media_type,
                        filename=sanitize_filename(f"{entry_id}.{ext}"),
                        mime_type=mime,
                        title=item_title,
                        thumbnail_url=thumb,
                        duration=entry.get("duration")
                    )
                    items.append(item)

                if not items:
                    return None

                if has_videos and has_images:
                    content_type = "mixed"
                    available_formats = ["zip", "images_pdf", "images_zip", "mp4"]
                elif has_videos:
                    content_type = "video_collection"
                    available_formats = ["zip", "mp4"]
                else:
                    content_type = "image_collection"
                    available_formats = ["pdf", "docx", "zip", "images"]

                return AnalysisResult(
                    success=True,
                    platform="Instagram",
                    content_type=content_type,
                    media_count=len(items),
                    formats=available_formats,
                    items=items,
                    previews=previews,
                    title=title,
                    description=description
                )
            else:
                # Single item (photo or video/reel)
                formats = info.get("formats") or []
                thumbnails = info.get("thumbnails") or []
                is_video = bool(formats)
                entry_id = info.get("id") or "media"

                if is_video:
                    content_type = "video"
                    direct_url = formats[-1].get("url")
                    ext = "mp4"
                    mime = "video/mp4"
                    thumb = thumbnails[-1].get("url") if thumbnails else None
                    available_formats = ["mp4", "mkv", "webm", "audio", "m4a"]
                else:
                    content_type = "image"
                    direct_url = thumbnails[-1].get("url") if thumbnails else None
                    ext = "jpg"
                    mime = "image/jpeg"
                    thumb = thumbnails[0].get("url") if thumbnails else direct_url
                    available_formats = ["original", "pdf", "docx", "zip"]

                if not direct_url:
                    return None

                item = MediaItem(
                    url=direct_url,
                    media_type=content_type,
                    filename=sanitize_filename(f"{entry_id}.{ext}"),
                    mime_type=mime,
                    title=title,
                    thumbnail_url=thumb,
                    duration=info.get("duration")
                )
                return AnalysisResult(
                    success=True,
                    platform="Instagram",
                    content_type=content_type,
                    media_count=1,
                    formats=available_formats,
                    items=[item],
                    previews=[thumb] if thumb else [],
                    title=title,
                    description=description
                )

        except Exception as e:
            logger.warning(f"Direct InstagramIE extraction failed for {url}: {e}")
            return None

    def analyze(self, url: str) -> AnalysisResult:
        # 1. Try specialized InstagramIE extraction (handles carousels & photo posts)
        direct_res = self._extract_via_instagram_ie(url)
        if direct_res and direct_res.success and direct_res.media_count > 0:
            return direct_res

        # 2. Try standard YtDlpService extraction
        res = YtDlpService.analyze_url(url, platform_hint="Instagram")
        if res.success and res.media_count > 0:
            return res

        # 3. Fallback to OpenGraph inspection if public web preview is available
        og_res = GenericDownloader.analyze(url)
        if og_res.success and og_res.media_count > 0:
            og_res.platform = "Instagram"
            return og_res

        return AnalysisResult(
            success=False,
            platform="Instagram",
            content_type="unknown",
            error_code="CONTENT_UNAVAILABLE",
            error_message="Unable to access Instagram post. The account may be private or requires login."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
