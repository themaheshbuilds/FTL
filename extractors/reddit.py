from urllib.parse import urlparse
import re
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from services.ytdlp_service import YtDlpService
from services.generic_downloader import GenericDownloader
from utils.filenames import sanitize_filename
from utils.logging import get_logger

logger = get_logger("linkforge.extractor.reddit")

REDDIT_PATTERN = re.compile(r"(?:www\.)?(?:reddit\.com|redd\.it|sh\.reddit\.com|old\.reddit\.com)", re.IGNORECASE)


class RedditExtractor(BaseExtractor):
    """Extractor for Reddit video posts, image galleries, and links."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(REDDIT_PATTERN.search(hostname))

    def analyze(self, url: str) -> AnalysisResult:
        logger.info(f"Analyzing Reddit URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        # 1. Strategy A: RapidSave Resolver (Extracts full audio-video muxed MP4 or images)
        try:
            r = requests.get(f"https://rapidsave.com/info?url={url}", headers=headers, timeout=8)
            if r.status_code == 200 and r.text:
                soup = BeautifulSoup(r.text, "html.parser")
                title_el = soup.find("h2")
                title = (title_el.text.strip() if title_el else "Reddit Post") or "Reddit Post"

                dl_btn = soup.find("a", class_="downloadbutton")
                dl_url = dl_btn.get("href") if dl_btn else None

                img_tag = soup.find("img", class_="img-fluid")
                img_url = img_tag.get("src") if img_tag else None

                is_video = bool(dl_url and any(k in dl_url.lower() for k in ("sd.rapidsave", ".mp4", "v.redd.it", "packaged-media")))

                if dl_url and is_video:
                    item = MediaItem(
                        url=dl_url,
                        media_type="video",
                        filename=sanitize_filename(f"{title}.mp4"),
                        mime_type="video/mp4",
                        title=title,
                        thumbnail_url=img_url
                    )
                    return AnalysisResult(
                        success=True,
                        platform="Reddit",
                        content_type="video",
                        media_count=1,
                        formats=["mp4", "mkv", "webm", "audio", "m4a"],
                        items=[item],
                        previews=[img_url] if img_url else [],
                        title=title,
                        description=f"Reddit Video • {title}"
                    )
                elif img_url and not is_video:
                    ext = "png" if ".png" in img_url.lower() else "jpg"
                    item = MediaItem(
                        url=img_url,
                        media_type="image",
                        filename=sanitize_filename(f"{title}.{ext}"),
                        mime_type=f"image/{ext}",
                        title=title,
                        thumbnail_url=img_url
                    )
                    return AnalysisResult(
                        success=True,
                        platform="Reddit",
                        content_type="image",
                        media_count=1,
                        formats=["original", "pdf", "docx", "zip"],
                        items=[item],
                        previews=[img_url],
                        title=title,
                        description=f"Reddit Image • {title}"
                    )
                elif dl_url and not dl_url.startswith("https://www.reddit.com"):
                    ext = "mp4" if dl_url.endswith(".mp4") else ("jpg" if dl_url.endswith(".jpg") else "file")
                    item = MediaItem(
                        url=dl_url,
                        media_type="video" if ext == "mp4" else ("image" if ext == "jpg" else "generic"),
                        filename=sanitize_filename(f"{title}.{ext}"),
                        mime_type="video/mp4" if ext == "mp4" else "application/octet-stream",
                        title=title
                    )
                    return AnalysisResult(
                        success=True,
                        platform="Reddit",
                        content_type="video" if ext == "mp4" else "media",
                        media_count=1,
                        formats=["mp4", "zip", "original"] if ext == "mp4" else ["original", "zip"],
                        items=[item],
                        title=title
                    )
        except Exception as e:
            logger.debug(f"RapidSave resolver for Reddit failed: {e}")

        # 2. Strategy B: Reddit Official oEmbed API
        try:
            oembed_url = f"https://www.reddit.com/oembed?url={url}"
            resp = requests.get(oembed_url, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title") or "Reddit Post"
                author = data.get("author_name") or ""
                desc = f"Posted by u/{author} on Reddit" if author else "Reddit Post"

                ydl_res = YtDlpService.analyze_url(url, platform_hint="Reddit")
                if ydl_res.success and ydl_res.items:
                    return ydl_res

                item = MediaItem(
                    url=url,
                    media_type="generic",
                    filename=sanitize_filename(f"{title}.txt"),
                    mime_type="text/plain",
                    title=title
                )
                return AnalysisResult(
                    success=True,
                    platform="Reddit",
                    content_type="post",
                    media_count=1,
                    formats=["original", "zip"],
                    items=[item],
                    title=title,
                    description=desc
                )
        except Exception as e:
            logger.debug(f"Reddit oEmbed failed: {e}")

        # 3. Strategy C: Standard yt-dlp analysis
        res = YtDlpService.analyze_url(url, platform_hint="Reddit")
        if res.success:
            return res

        # 4. Strategy D: Generic OpenGraph analysis
        og_res = GenericDownloader.analyze(url)
        if og_res.success:
            og_res.platform = "Reddit"
            return og_res

        return AnalysisResult(
            success=False,
            platform="Reddit",
            content_type="unknown",
            error_code="CONTENT_UNAVAILABLE",
            error_message="Unable to access Reddit post. Content may be restricted, private, or removed."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
