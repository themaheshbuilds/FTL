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

    @staticmethod
    def _select_best_video_format(formats: List[Dict[str, Any]]) -> Optional[str]:
        """Select best progressive video format with audio, avoiding audio-only DASH streams."""
        if not formats:
            return None

        # Filter candidates that have a direct URL and are not audio-only
        video_candidates = [f for f in formats if f.get("url") and f.get("vcodec") != "none"]
        if not video_candidates:
            video_candidates = [f for f in formats if f.get("url")]
            if not video_candidates:
                return None

        # 1. Progressive video with audio muxed (acodec != 'none')
        progressive = [f for f in video_candidates if f.get("acodec") != "none"]
        if progressive:
            return max(
                progressive,
                key=lambda f: (f.get("height") or 0, f.get("width") or 0, f.get("tbr") or 0)
            ).get("url")

        # 2. Highest resolution video candidate
        return max(
            video_candidates,
            key=lambda f: (f.get("height") or 0, f.get("width") or 0, f.get("tbr") or 0)
        ).get("url")

    def _extract_via_instagram_ie(self, url: str) -> Optional[AnalysisResult]:
        """Extract media using yt-dlp's InstagramIE directly.
        
        This handles both single posts (photos and videos) and multi-item carousels,
        retaining full-resolution image URLs that standard yt-dlp video extractors
        discard when format checks fail on static photos.
        """
        proxies = YtDlpService.get_active_proxies()
        candidate_proxies = list(proxies) if proxies else [None]
        if candidate_proxies and candidate_proxies[0] is not None:
            candidate_proxies.append(None)

        info = None
        for current_proxy in candidate_proxies[:3]:
            extra_opts = {
                "skip_download": True,
                "quiet": True,
                "referer": "https://www.instagram.com/",
                "http_headers": {
                    "Referer": "https://www.instagram.com/",
                    "Origin": "https://www.instagram.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                }
            }
            if current_proxy:
                extra_opts["proxy"] = current_proxy

            opts = YtDlpService.get_default_opts(extra_opts)
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

                if info and isinstance(info, dict):
                    break
            except Exception as e:
                logger.warning(f"Direct InstagramIE extraction trial failed for {url} (proxy={bool(current_proxy)}): {e}")

        if not info or not isinstance(info, dict):
            return None

        title = info.get("title") or "Instagram Media"
        description = info.get("description")
        entries = info.get("entries")
        if entries is not None and not isinstance(entries, list):
            try:
                entries = list(entries)
            except Exception:
                entries = []

        if not entries:
            # Check direct carousel_media or edge_sidecar_to_children
            raw_carousel = info.get("carousel_media") or info.get("edge_sidecar_to_children")
            if raw_carousel:
                if isinstance(raw_carousel, dict) and "edges" in raw_carousel:
                    entries = [edge.get("node") for edge in raw_carousel.get("edges", []) if edge.get("node")]
                elif isinstance(raw_carousel, list):
                    entries = raw_carousel

        if entries and isinstance(entries, list) and len(entries) > 0:
            items: List[MediaItem] = []
            previews: List[str] = []
            has_videos = False
            has_images = False

            for idx, entry in enumerate(entries):
                if not entry or not isinstance(entry, dict):
                    continue
                entry_id = entry.get("id") or entry.get("pk") or f"media_{idx + 1}"
                formats = entry.get("formats") or []
                thumbnails = entry.get("thumbnails") or []

                # Fallback for raw Instagram product media dictionaries
                if not formats and entry.get("video_versions"):
                    formats = entry.get("video_versions")
                if not thumbnails and entry.get("image_versions2"):
                    cands = entry.get("image_versions2", {}).get("candidates", [])
                    thumbnails = [{"url": c.get("url")} for c in cands if c.get("url")]

                is_video = bool(formats)

                if is_video:
                    has_videos = True
                    direct_url = self._select_best_video_format(formats)
                    ext = "mp4"
                    mime = "video/mp4"
                    media_type = "video"
                    thumb = thumbnails[-1].get("url") if thumbnails else None
                else:
                    has_images = True
                    # The last thumbnail in yt-dlp candidates is the highest resolution original image
                    direct_url = thumbnails[-1].get("url") if thumbnails else (entry.get("display_url") or entry.get("url"))
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

            # Detect background music / audio track in carousel
            music_info = info.get("music_info") or info.get("clips_metadata") or {}
            audio_url = None
            audio_title = None
            if isinstance(music_info, dict):
                asset = music_info.get("music_asset_info") or music_info.get("audio_type_model") or music_info
                audio_url = asset.get("progressive_download_url") or asset.get("audio_url") or music_info.get("audio_url")
                raw_title = asset.get("title") or asset.get("song_name") or "Instagram Audio Track"
                artist = asset.get("display_artist") or asset.get("artist_name") or ""
                audio_title = f"{artist} - {raw_title}" if artist else raw_title

            if audio_url:
                items.append(MediaItem(
                    url=audio_url,
                    media_type="audio",
                    filename=sanitize_filename(f"{audio_title or 'audio_track'}.mp3"),
                    mime_type="audio/mpeg",
                    title=audio_title or "Background Audio Track",
                    thumbnail_url=previews[0] if previews else None
                ))
            elif has_videos:
                # Add audio track derived from the first video
                primary_video = next((it for it in items if it.media_type == "video"), None)
                if primary_video:
                    items.append(MediaItem(
                        url=primary_video.url,
                        media_type="audio",
                        filename=sanitize_filename(f"{title}_audio.mp3"),
                        mime_type="audio/mpeg",
                        title=f"{title} (Audio Track)",
                        thumbnail_url=primary_video.thumbnail_url,
                        duration=primary_video.duration
                    ))

            if has_videos and has_images:
                content_type = "mixed"
                available_formats = ["zip", "mp4", "mkv", "images_pdf", "images_zip", "audio", "mp3"]
            elif has_videos:
                content_type = "video_collection"
                available_formats = ["zip", "mp4", "mkv", "audio", "mp3"]
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
                direct_url = self._select_best_video_format(formats)
                ext = "mp4"
                mime = "video/mp4"
                thumb = thumbnails[-1].get("url") if thumbnails else None
                available_formats = ["mp4", "mkv", "webm", "audio", "mp3", "m4a"]

                if not direct_url:
                    return None

                video_item = MediaItem(
                    url=direct_url,
                    media_type="video",
                    filename=sanitize_filename(f"{entry_id}.{ext}"),
                    mime_type=mime,
                    title=title,
                    thumbnail_url=thumb,
                    duration=info.get("duration")
                )

                # Check for music info in single video/reel
                music_info = info.get("music_info") or info.get("clips_metadata") or {}
                audio_url = None
                audio_title = None
                if isinstance(music_info, dict):
                    asset = music_info.get("music_asset_info") or music_info.get("audio_type_model") or music_info
                    audio_url = asset.get("progressive_download_url") or asset.get("audio_url") or music_info.get("audio_url")
                    raw_title = asset.get("title") or asset.get("song_name") or "Instagram Audio Track"
                    artist = asset.get("display_artist") or asset.get("artist_name") or ""
                    audio_title = f"{artist} - {raw_title}" if artist else raw_title

                audio_item = MediaItem(
                    url=audio_url or direct_url,
                    media_type="audio",
                    filename=sanitize_filename(f"{audio_title or entry_id}_audio.mp3"),
                    mime_type="audio/mpeg",
                    title=audio_title or f"{title} (Audio Track)",
                    thumbnail_url=thumb,
                    duration=info.get("duration")
                )

                items = [video_item, audio_item]
                previews = [thumb] if thumb else []
            else:
                content_type = "image"
                direct_url = thumbnails[-1].get("url") if thumbnails else (info.get("display_url") or info.get("url"))
                ext = "jpg"
                mime = "image/jpeg"
                thumb = thumbnails[0].get("url") if thumbnails else direct_url
                available_formats = ["original", "pdf", "docx", "zip"]

                if not direct_url:
                    return None

                item = MediaItem(
                    url=direct_url,
                    media_type="image",
                    filename=sanitize_filename(f"{entry_id}.{ext}"),
                    mime_type=mime,
                    title=title,
                    thumbnail_url=thumb,
                    duration=info.get("duration")
                )
                items = [item]
                previews = [thumb] if thumb else []

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
