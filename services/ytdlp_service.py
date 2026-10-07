import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import yt_dlp
from models.result import AnalysisResult
from models.media import MediaItem
from utils.logging import get_logger, log_event
from utils.filenames import sanitize_filename
from utils.ffmpeg_helper import get_ffmpeg_executable

logger = get_logger("linkforge.ytdlp")


def format_cookies_to_netscape(raw_content: str) -> str:
    """Ensure cookie content is in Netscape format with strict tab separation.
    Handles JSON arrays, space-separated lines (from web form paste), leading variable names,
    and removes unstable *PSIDTS tokens that trigger 'The page needs to be reloaded' errors.
    """
    import re
    stripped = raw_content.strip()
    if (stripped.startswith('"') and stripped.endswith('"')) or (stripped.startswith("'") and stripped.endswith("'")):
        stripped = stripped[1:-1].strip()
    if "\n" not in stripped and "\\n" in stripped:
        stripped = stripped.replace("\\n", "\n")
    if "\t" not in stripped and "\\t" in stripped:
        stripped = stripped.replace("\\t", "\t")
    # Strip variable assignments if pasted like 'YOUTUBE_COOKIES = ...'
    stripped = re.sub(r'^\s*YOUTUBE_COOKIES\s*=\s*', '', stripped, flags=re.IGNORECASE).strip()

    # Case A: JSON format [ { "domain": ".youtube.com", ... } ]
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            import json
            cookie_list = json.loads(stripped)
            filtered = [c for c in cookie_list if isinstance(c, dict) and 'PSIDTS' not in c.get('name', '')]
            lines = ["# Netscape HTTP Cookie File"]
            for c in filtered:
                domain = c.get("domain", "")
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c.get("path", "/")
                secure = "TRUE" if c.get("secure", False) else "FALSE"
                expiry = str(int(c.get("expirationDate") or 2147483647))
                name = c.get("name", "")
                value = c.get("value", "")
                if name:
                    lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")
            return "\n".join(lines)
        except Exception:
            pass

    # Case B: Netscape format (either tab-separated or space-separated from web form paste)
    lines = ["# Netscape HTTP Cookie File"]
    for line in stripped.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            parts = line.split("\t")
        else:
            parts = re.split(r'\s+', line, maxsplit=6)
        if len(parts) >= 7:
            if 'PSIDTS' in parts[5]:
                continue
            lines.append("\t".join(parts[:7]))
    return "\n".join(lines)


class YtDlpService:
    """Encapsulates all interaction with yt-dlp."""

    @classmethod
    def get_cookie_file(cls) -> Optional[str]:
        """Discover cookies file from path or environment variable, auto-converting JSON if needed."""
        # 1. Explicit path in env
        cookie_path = os.getenv("YOUTUBE_COOKIES_PATH") or os.getenv("COOKIES_FILE")
        if cookie_path and os.path.isfile(cookie_path):
            return cookie_path

        # 2. Local JSON file in project root
        local_json = Path(__file__).resolve().parent.parent / "www_youtube_com_cookies.json"
        if local_json.is_file():
            try:
                converted = format_cookies_to_netscape(local_json.read_text(encoding="utf-8"))
                out_txt = Path(__file__).resolve().parent.parent / "cookies.txt"
                out_txt.write_text(converted, encoding="utf-8")
                return str(out_txt)
            except Exception:
                pass

        # 3. Local Netscape cookies.txt
        local_cookie = Path(__file__).resolve().parent.parent / "cookies.txt"
        if local_cookie.is_file():
            return str(local_cookie)

        # 4. Raw cookies from environment variable
        raw_cookies = os.getenv("YOUTUBE_COOKIES")
        if raw_cookies:
            import tempfile
            tmp_cookie = Path(tempfile.gettempdir()) / "yt_cookies.txt"
            try:
                converted = format_cookies_to_netscape(raw_cookies)
                tmp_cookie.write_text(converted.strip(), encoding="utf-8")
                return str(tmp_cookie)
            except Exception:
                pass
        return None

    @classmethod
    def get_default_opts(cls, extra_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Standardized yt-dlp options ensuring safety, ffmpeg integration, and full resolution support."""
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
        }

        cookie_file = cls.get_cookie_file()
        if cookie_file:
            opts["cookiefile"] = cookie_file

        proxy = os.getenv("YOUTUBE_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if proxy:
            opts["proxy"] = proxy

        ffmpeg_bin = get_ffmpeg_executable()
        if ffmpeg_bin:
            opts["ffmpeg_location"] = ffmpeg_bin

        if extra_opts:
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
    def extract_info(cls, url: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """Extract metadata without downloading files, attempting full resolution first then mobile fallbacks."""
        client_configs = [
            # 1. Primary: Unrestricted clients (enables 4K, 1440p, 1080p, 720p full adaptive streams)
            None,
            # 2. Cloud Fallback: android + ios mobile InnerTube endpoints (bypasses bot detection on datacenter IPs)
            {"player_client": ["android", "ios"], "player_skip": ["webpage", "configs"]},
            # 3. Fallback: dedicated android client
            {"player_client": ["android"], "player_skip": ["webpage", "configs"]},
            # 4. Fallback: dedicated ios client
            {"player_client": ["ios"], "player_skip": ["webpage", "configs"]},
            # 5. Fallback: TV and web embedded endpoints
            {"player_client": ["tv", "web_embedded"], "player_skip": ["webpage", "configs"]},
        ]

        last_error = ""
        for config in client_configs:
            try:
                extra = {"skip_download": True, "ignoreerrors": False}
                if config:
                    extra["extractor_args"] = {"youtube": config}
                opts = cls.get_default_opts(extra)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info and info.get("title"):
                        return info, ""
            except Exception as e:
                last_error = str(e)
                logger.warning(f"yt-dlp extraction trial failed for {url} with client config {config}: {e}")

        return None, last_error


    @classmethod
    def analyze_url(cls, url: str, platform_hint: str = "Platform") -> AnalysisResult:
        """Analyze URL through yt-dlp and return structured AnalysisResult."""
        info, last_error = cls.extract_info(url)
        if not info:
            is_bot_blocked = "sign in to confirm you" in last_error.lower() or "bot" in last_error.lower()
            if is_bot_blocked:
                err_code = "BOT_VERIFICATION_REQUIRED"
                err_msg = (
                    "YouTube anti-bot verification blocked this cloud request ('Sign in to confirm you\'re not a bot'). "
                    "On cloud hosting (Vercel), add your YOUTUBE_COOKIES in Vercel Environment Variables to authenticate."
                )
            else:
                err_code = "EXTRACTION_FAILED"
                err_msg = "Could not extract public media from this URL. Content may be private, require login, or be unsupported."

            return AnalysisResult(
                success=False,
                platform=platform_hint,
                content_type="unknown",
                error_code=err_code,
                error_message=err_msg
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
            if ffmpeg_bin:
                custom_opts["format"] = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
                custom_opts["merge_output_format"] = "mp4"
                custom_opts["final_ext"] = "mp4"
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
            else:
                custom_opts["format"] = "best[height<=1080][ext=mp4]/best[ext=mp4]/18/best"
        elif format_filter == "720p":
            if ffmpeg_bin:
                custom_opts["format"] = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
                custom_opts["merge_output_format"] = "mp4"
                custom_opts["final_ext"] = "mp4"
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
            else:
                custom_opts["format"] = "best[height<=720][ext=mp4]/best[ext=mp4]/18/best"
        elif format_filter == "480p":
            if ffmpeg_bin:
                custom_opts["format"] = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
                custom_opts["merge_output_format"] = "mp4"
                custom_opts["final_ext"] = "mp4"
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
            else:
                custom_opts["format"] = "best[height<=480][ext=mp4]/best[ext=mp4]/18/best"
        else:
            # Default "best" = MAXIMUM QUALITY available (4K, 1440p, 1080p full HD merged)
            if ffmpeg_bin:
                custom_opts["format"] = "bestvideo+bestaudio/best"
                custom_opts["merge_output_format"] = "mp4"
                custom_opts["final_ext"] = "mp4"
                custom_opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
            else:
                custom_opts["format"] = "best[ext=mp4]/best/18"

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
