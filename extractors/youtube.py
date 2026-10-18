from urllib.parse import urlparse
import re
from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService
from utils.logging import get_logger

logger = get_logger("linkforge.extractor.youtube")

YOUTUBE_PATTERN = re.compile(r"(?:www\.)?(?:youtube\.com|youtu\.be)", re.IGNORECASE)


class YouTubeExtractor(BaseExtractor):
    """Extractor for YouTube videos, shorts, and audio extraction."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(YOUTUBE_PATTERN.search(hostname))

    def analyze(self, url: str) -> AnalysisResult:
        logger.info(f"Analyzing YouTube URL: {url}")

        # 1. Fast path: Direct YouTube oEmbed API (< 0.4s, zero-bot-block, works on Vercel)
        match = re.search(r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})", url)
        if match:
            video_id = match.group(1)
            try:
                import requests
                from utils.filenames import sanitize_filename
                oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                resp = requests.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
                if resp.status_code == 200:
                    data = resp.json()
                    title = (data.get("title") or f"YouTube Video {video_id}").strip()
                    author = (data.get("author_name") or "").strip()
                    thumb = data.get("thumbnail_url") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    item = MediaItem(
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        media_type="video",
                        filename=sanitize_filename(f"{title}.mp4"),
                        mime_type="video/mp4",
                        title=title,
                        thumbnail_url=thumb
                    )
                    return AnalysisResult(
                        success=True,
                        platform="YouTube",
                        content_type="video",
                        media_count=1,
                        formats=["mp4", "mkv", "webm", "audio", "m4a"],
                        items=[item],
                        previews=[thumb],
                        title=title,
                        description=f"By {author}" if author else None
                    )
                elif resp.status_code == 404:
                    return AnalysisResult(
                        success=False,
                        platform="YouTube",
                        content_type="video",
                        error_code="VIDEO_NOT_FOUND",
                        error_message="This YouTube video or Short does not exist or has been removed."
                    )
            except Exception as e:
                logger.debug(f"oEmbed fast path failed for {url}, falling back to yt-dlp: {e}")

        # 2. Fallback to optimized yt-dlp analysis
        res = YtDlpService.analyze_url(url, platform_hint="YouTube")
        if res.success:
            return res

        return AnalysisResult(
            success=False,
            platform="YouTube",
            content_type="video",
            error_code=res.error_code or "YOUTUBE_FETCH_FAILED",
            error_message=res.error_message or "Unable to extract video streams from this YouTube URL. It may be private or restricted."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
