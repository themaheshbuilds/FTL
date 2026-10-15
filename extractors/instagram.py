import json
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import requests
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
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'


class InstagramExtractor(BaseExtractor):
    """Extractor for Instagram posts, reels, and carousel collections."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(INSTAGRAM_PATTERN.search(hostname))

    @staticmethod
    def _extract_shortcode(url: str) -> Optional[str]:
        """Extract Instagram shortcode from post/reel URL."""
        match = re.search(r"/(?:p|reel|tv|reels)/([A-Za-z0-9_-]+)", url)
        return match.group(1) if match else None

    @staticmethod
    def _shortcode_to_mediaid(shortcode: str) -> str:
        """Convert Instagram base64-style shortcode to numerical media_id."""
        media_id = 0
        for char in shortcode:
            if char in ALPHABET:
                media_id = media_id * 64 + ALPHABET.index(char)
        return str(media_id)

    @staticmethod
    def _select_best_video_format(formats: List[Dict[str, Any]]) -> Optional[str]:
        """Select best progressive video format with audio, avoiding audio-only DASH streams."""
        if not formats:
            return None

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

    def _convert_info_to_analysis_result(self, info: Dict[str, Any]) -> Optional[AnalysisResult]:
        """Convert a normalized media info dictionary into an AnalysisResult.
        
        Handles:
        - Image carousels (multiple photo selection, PDF, DOCX, ZIP)
        - Video collections and reels (progressive MP4, MKV, audio track extraction)
        - Mixed media collections (images + videos in one post)
        - Dedicated audio/music track extraction
        """
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

                is_video = bool(formats) or bool(entry.get("is_video")) or entry.get("__typename") == "GraphVideo"

                if is_video:
                    has_videos = True
                    direct_url = self._select_best_video_format(formats) if formats else entry.get("video_url")
                    ext = "mp4"
                    mime = "video/mp4"
                    media_type = "video"
                    thumb = thumbnails[-1].get("url") if thumbnails else (entry.get("display_url") or entry.get("thumbnail_src"))
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
            is_video = bool(formats) or bool(info.get("is_video")) or info.get("__typename") == "GraphVideo"
            entry_id = info.get("id") or "media"

            if is_video:
                content_type = "video"
                direct_url = self._select_best_video_format(formats) if formats else info.get("video_url")
                ext = "mp4"
                mime = "video/mp4"
                thumb = thumbnails[-1].get("url") if thumbnails else (info.get("display_url") or info.get("thumbnail_src"))
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

    def _extract_via_instagram_ie(self, url: str) -> Optional[AnalysisResult]:
        """Extract media using yt-dlp's InstagramIE directly."""
        proxies = YtDlpService.get_active_proxies()
        candidate_proxies = list(proxies) if proxies else [None]
        if candidate_proxies and candidate_proxies[0] is not None:
            candidate_proxies.append(None)

        info = None
        for current_proxy in candidate_proxies[:2]:
            extra_opts = {
                "skip_download": True,
                "quiet": True,
                "socket_timeout": 8,
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

                    orig_raise_no_formats = ie.raise_no_formats
                    ie.raise_no_formats = lambda msg, expected=True: None
                    try:
                        info = ie._real_extract(url)
                    finally:
                        ie.raise_no_formats = orig_raise_no_formats

                if info and isinstance(info, dict):
                    break
            except Exception as e:
                logger.debug(f"Direct InstagramIE extraction trial failed for {url} (proxy={bool(current_proxy)}): {e}")

        if not info or not isinstance(info, dict):
            return None

        return self._convert_info_to_analysis_result(info)

    def _extract_via_embed_or_api(self, url: str) -> Optional[AnalysisResult]:
        """Fallback extractor using public Instagram embed pages or mobile API info."""
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            return None

        # 1. Try Embed page contextJSON
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
        embed_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
        }

        try:
            r = requests.get(embed_url, headers=embed_headers, timeout=6)
            if r.status_code == 200:
                key = '"contextJSON":'
                idx = r.text.find(key)
                if idx != -1:
                    substr = r.text[idx + len(key):].lstrip()
                    inner, _ = json.JSONDecoder().raw_decode(substr)
                    context = json.loads(inner)
                    media = (context.get("gql_data") or {}).get("shortcode_media")
                    if media and isinstance(media, dict):
                        res = self._convert_info_to_analysis_result(media)
                        if res and res.success and res.media_count > 0:
                            return res
        except Exception as e:
            logger.debug(f"Instagram embed contextJSON extraction failed for {shortcode}: {e}")

        # 2. Try Mobile API with X-IG-App-ID
        media_id = self._shortcode_to_mediaid(shortcode)
        if media_id and media_id != "0":
            api_url = f"https://i.instagram.com/api/v1/media/{media_id}/info/"
            mobile_headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 300.0.0.0.0",
                "X-IG-App-ID": "936619743392459",
                "X-ASBD-ID": "198387",
                "X-IG-WWW-Claim": "0",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://www.instagram.com",
                "Referer": f"https://www.instagram.com/p/{shortcode}/",
            }
            try:
                r2 = requests.get(api_url, headers=mobile_headers, timeout=6)
                if r2.status_code == 200:
                    api_data = r2.json()
                    items = api_data.get("items") or []
                    if items and isinstance(items, list):
                        item = items[0]
                        item["id"] = shortcode
                        item["title"] = (item.get("caption") or {}).get("text", "")[:100] if isinstance(item.get("caption"), dict) else f"Instagram Media {shortcode}"
                        res = self._convert_info_to_analysis_result(item)
                        if res and res.success and res.media_count > 0:
                            return res
            except Exception as e:
                logger.debug(f"Instagram mobile API extraction failed for {media_id}: {e}")

        return None

    def analyze(self, url: str) -> AnalysisResult:
        # 1. Specialized InstagramIE extraction (handles carousels & photo posts)
        direct_res = self._extract_via_instagram_ie(url)
        if direct_res and direct_res.success and direct_res.media_count > 0:
            return direct_res

        # 2. Resilient Embed & Mobile API extraction
        embed_res = self._extract_via_embed_or_api(url)
        if embed_res and embed_res.success and embed_res.media_count > 0:
            return embed_res

        # 3. Standard YtDlpService extraction
        res = YtDlpService.analyze_url(url, platform_hint="Instagram")
        if res.success and res.media_count > 0:
            return res

        # 4. Fallback to OpenGraph inspection if public web preview is available
        og_res = GenericDownloader.analyze(url)
        if og_res.success and og_res.media_count > 0:
            og_res.platform = "Instagram"
            return og_res

        return AnalysisResult(
            success=False,
            platform="Instagram",
            content_type="unknown",
            error_code="CONTENT_UNAVAILABLE",
            error_message="Unable to access Instagram post. The account may be private or requires login. If running in the cloud, ensure INSTAGRAM_COOKIES is configured in project settings."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
