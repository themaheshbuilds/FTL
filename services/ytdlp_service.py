import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import yt_dlp
from models.result import AnalysisResult
from models.media import MediaItem
from utils.logging import get_logger, log_event
from utils.filenames import sanitize_filename
from utils.ffmpeg_helper import get_ffmpeg_executable

logger = get_logger("linkforge.ytdlp")


class YtDlpService:
    """Encapsulates all interaction with yt-dlp."""

    @classmethod
    def get_cookie_file(cls) -> Optional[str]:
        """Discover cookies file from path or environment variable."""
        cookie_path = os.getenv("YOUTUBE_COOKIES_PATH") or os.getenv("COOKIES_FILE")
        if cookie_path and os.path.isfile(cookie_path):
            return cookie_path

        local_cookie = Path(__file__).resolve().parent.parent / "cookies.txt"
        if local_cookie.is_file():
            return str(local_cookie)

        raw_cookies = os.getenv("YOUTUBE_COOKIES")
        if raw_cookies:
            import tempfile
            tmp_cookie = Path(tempfile.gettempdir()) / "yt_cookies.txt"
            try:
                tmp_cookie.write_text(raw_cookies.strip(), encoding="utf-8")
                return str(tmp_cookie)
            except Exception:
                pass
        return None

    @classmethod
    def get_default_opts(cls, extra_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Standardized yt-dlp options ensuring safety, ffmpeg integration, and cloud-resilient execution."""
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": 25,
            "extract_flat": False,
            "noplaylist": False,
            "ignoreerrors": True,
            "nocheckcertificate": False,
            "windowsfilenames": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios"],
                    "player_skip": ["webpage", "configs"]
                }
            }
        }

        cookie_file = cls.get_cookie_file()
        if cookie_file:
            opts["cookiefile"] = cookie_file

        ffmpeg_bin = get_ffmpeg_executable()
        if ffmpeg_bin:
            opts["ffmpeg_location"] = ffmpeg_bin

        if extra_opts:
            # Deep merge extractor_args if present
            if "extractor_args" in extra_opts and "extractor_args" in opts:
                merged_extractor_args = dict(opts["extractor_args"])
                merged_extractor_args.update(extra_opts["extractor_args"])
                extra_copy = dict(extra_opts)
                extra_copy["extractor_args"] = merged_extractor_args
                opts.update(extra_copy)
            else:
                opts.update(extra_opts)
        return opts

    @classmethod
    def extract_info(cls, url: str) -> Optional[Dict[str, Any]]:
        """Extract metadata without downloading files, using progressive fallback clients."""
        client_configs = [
            # 1. Primary: android + ios mobile InnerTube endpoints (bypasses bot detection & 429 webpage blocks)
            {"player_client": ["android", "ios"], "player_skip": ["webpage", "configs"]},
            # 2. Fallback: dedicated android client
            {"player_client": ["android"], "player_skip": ["webpage", "configs"]},
            # 3. Fallback: dedicated ios client
            {"player_client": ["ios"], "player_skip": ["webpage", "configs"]},
            # 4. Fallback: TV and web embedded endpoints
            {"player_client": ["tv", "web_embedded"], "player_skip": ["webpage", "configs"]},
            # 5. Generic yt-dlp fallback
            {}
        ]

        for config in client_configs:
            try:
                extra = {"skip_download": True}
                if config:
                    extra["extractor_args"] = {"youtube": config}
                opts = cls.get_default_opts(extra)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        return info
            except Exception as e:
                logger.warning(f"yt-dlp extraction trial failed for {url} with client config {config}: {e}")

        return None


    @classmethod
    def analyze_url(cls, url: str, platform_hint: str = "Platform") -> AnalysisResult:
        """Analyze URL through yt-dlp and return structured AnalysisResult."""
        info = cls.extract_info(url)
        if not info:
            return AnalysisResult(
                success=False,
                platform=platform_hint,
                content_type="unknown",
                error_code="EXTRACTION_FAILED",
                error_message="Could not extract public media from this URL. Content may be private, require login, or be unsupported."
            )

        # Detect playlist / multi-entries
        entries = info.get("entries")
        if entries and isinstance(entries, list):
            items: List[MediaItem] = []
            previews: List[str] = []
            has_videos = False
            has_images = False

            for idx, entry in enumerate(entries):
                if not entry:
                    continue
                direct_url = entry.get("url") or (entry.get("formats") and entry["formats"][-1].get("url"))
                thumbnail = entry.get("thumbnail")
                ext = entry.get("ext", "mp4")
                title = entry.get("title", f"media_{idx + 1}")
                is_video = ext in ("mp4", "webm", "mkv", "mov")

                if is_video:
                    has_videos = True
                else:
                    has_images = True

                if thumbnail and thumbnail not in previews:
                    previews.append(thumbnail)

                item = MediaItem(
                    url=direct_url or url,
                    media_type="video" if is_video else "image",
                    filename=sanitize_filename(f"{title}.{ext}"),
                    mime_type=f"video/{ext}" if is_video else f"image/{ext}",
                    title=title,
                    thumbnail_url=thumbnail,
                    filesize=entry.get("filesize") or entry.get("filesize_approx"),
                    duration=entry.get("duration")
                )
                items.append(item)

            if not items:
                return AnalysisResult(
                    success=False,
                    platform=info.get("extractor_key") or platform_hint,
                    content_type="unknown",
                    error_code="NO_MEDIA_FOUND",
                    error_message="No downloadable media items found in this collection."
                )

            if has_videos and has_images:
                content_type = "mixed"
                formats = ["zip", "images_pdf", "images_zip", "mp4"]
            elif has_videos:
                content_type = "video_collection"
                formats = ["zip", "mp4"]
            else:
                content_type = "image_collection"
                formats = ["pdf", "docx", "zip", "images"]

            return AnalysisResult(
                success=True,
                platform=info.get("extractor_key") or platform_hint,
                content_type=content_type,
                media_count=len(items),
                formats=formats,
                items=items,
                previews=previews,
                title=info.get("title") or f"{platform_hint} Collection",
                description=info.get("description")
            )

        # Single entry
        ext = info.get("ext", "mp4")
        thumbnail = info.get("thumbnail")
        title = info.get("title", "media_item")
        is_video = ext in ("mp4", "webm", "mkv", "mov", "flv") or bool(info.get("vcodec") and info.get("vcodec") != "none")
        is_audio = ext in ("mp3", "m4a", "wav", "aac", "opus") or (info.get("vcodec") == "none" and info.get("acodec") != "none")

        previews = [thumbnail] if thumbnail else []

        if is_video:
            content_type = "video"
            formats = ["mp4", "mkv", "webm", "audio", "m4a"]
        elif is_audio:
            content_type = "audio"
            formats = ["audio", "m4a"]
        else:
            content_type = "image"
            formats = ["original", "pdf", "docx", "zip"]

        # Ensure valid direct media URL
        media_url = info.get("url")
        raw_formats = info.get("formats") or []
        valid_formats = [f for f in raw_formats if f.get("url") and f.get("vcodec") != "none"]
        if not valid_formats:
            valid_formats = [f for f in raw_formats if f.get("url")]

        if not media_url and valid_formats:
            media_url = valid_formats[-1].get("url")
            chosen_ext = valid_formats[-1].get("ext")
            if chosen_ext and chosen_ext not in ("mhtml",):
                ext = chosen_ext

        item = MediaItem(
            url=media_url or url,
            media_type=content_type,
            filename=sanitize_filename(f"{title}.{ext}"),
            mime_type=f"video/{ext}" if is_video else (f"audio/{ext}" if is_audio else f"image/{ext}"),
            title=title,
            thumbnail_url=thumbnail,
            filesize=info.get("filesize") or info.get("filesize_approx"),
            duration=info.get("duration")
        )

        return AnalysisResult(
            success=True,
            platform=info.get("extractor_key") or platform_hint,
            content_type=content_type,
            media_count=1,
            formats=formats,
            items=[item],
            previews=previews,
            title=title,
            description=info.get("description")
        )

    @classmethod
    def download_media(
        cls,
        url: str,
        target_dir: str,
        filename_template: str = "%(title).80s.%(ext)s",
        format_filter: str = "best"
    ) -> Optional[str]:
        """Download media via yt-dlp to isolated target directory with audio/video merge and progressive stream support."""
        output_path = os.path.join(target_dir, filename_template)
        ffmpeg_bin = get_ffmpeg_executable()
        
        custom_opts: Dict[str, Any] = {
            "skip_download": False,
            "outtmpl": output_path,
        }

        if format_filter == "audio":
            custom_opts["format"] = "bestaudio/best"
            if ffmpeg_bin:
                custom_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
        elif format_filter == "1080p":
            custom_opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best[ext=mp4]/18/best"
            custom_opts["merge_output_format"] = "mp4"
            custom_opts["final_ext"] = "mp4"
            if ffmpeg_bin:
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
        elif format_filter == "720p":
            custom_opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best[ext=mp4]/18/best"
            custom_opts["merge_output_format"] = "mp4"
            custom_opts["final_ext"] = "mp4"
            if ffmpeg_bin:
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
        elif format_filter == "480p":
            custom_opts["format"] = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best[ext=mp4]/18/best"
            custom_opts["merge_output_format"] = "mp4"
            custom_opts["final_ext"] = "mp4"
            if ffmpeg_bin:
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
        else:
            # Default best video + best audio merged into mp4, with fallback to progressive mp4 (18 or best[ext=mp4])
            custom_opts["format"] = "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/18/bv*+ba/b/best"
            custom_opts["merge_output_format"] = "mp4"
            custom_opts["final_ext"] = "mp4"
            if ffmpeg_bin:
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]

        opts = cls.get_default_opts(custom_opts)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return None

            # Locate downloaded file in target_dir
            candidates = []
            for fname in os.listdir(target_dir):
                # Ignore unfinished or part files
                if fname.endswith((".part", ".ytdl", ".temp", ".aria2")):
                    continue
                fpath = os.path.join(target_dir, fname)
                if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
                    candidates.append((fpath, os.path.getsize(fpath), os.path.getmtime(fpath)))

            if not candidates:
                logger.warning(f"No completed file found in {target_dir} after yt-dlp download.")
                return None

            # Pick largest/newest completed candidate file
            candidates.sort(key=lambda c: (c[1], c[2]), reverse=True)
            return candidates[0][0]

        except Exception as e:
            logger.error(f"Failed to download media via yt-dlp from {url}: {e}", exc_info=True)
            return None
