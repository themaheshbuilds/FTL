from urllib.parse import urlparse
import re
import json
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

logger = get_logger("linkforge.extractors.linkedin")
LINKEDIN_PATTERN = re.compile(r"(?:[a-zA-Z0-9-]+\.)?(?:linkedin\.com|lnkd\.in)", re.IGNORECASE)


class LinkedInExtractor(BaseExtractor):
    """Extractor for LinkedIn public posts, carousels, documents, and videos."""

    def can_handle(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return bool(LINKEDIN_PATTERN.search(hostname))

    def _extract_page_content(self, url: str) -> Optional[AnalysisResult]:
        """Extract videos, multi-image carousels, documents, or single media from LinkedIn post page."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            r = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
            if r.status_code != 200:
                logger.warning(f"LinkedIn request failed with status {r.status_code} for {url}")
                return None

            resolved_url = r.url
            html = r.text
            soup = BeautifulSoup(html, "html.parser")

            # Extract title / headline
            title = None
            for script_tag in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script_tag.string or "")
                    if isinstance(data, dict):
                        title = data.get("headline") or data.get("name") or title
                except Exception:
                    pass

            # Extract description / caption
            description = None
            for script_tag in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script_tag.string or "")
                    if isinstance(data, dict):
                        description = data.get("articleBody") or data.get("text") or data.get("description") or description
                except Exception:
                    pass

            if not description:
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    description = og_desc["content"]

            if not title:
                og_title = soup.find("meta", property="og:title")
                title = og_title.get("content") if og_title else (soup.title.string if soup.title else "LinkedIn Post")

            # Clean and sanitize title
            clean_title = title.split("|")[0].strip() if "|" in title else title
            clean_title = clean_title.split("\n")[0].strip()
            clean_title = re.sub(r'[^\x20-\x7E]', '', clean_title).strip()
            clean_title = re.sub(r'^[#\s]+', '', clean_title).strip()
            clean_title = re.sub(r'\s+', ' ', clean_title)
            if len(clean_title) > 60:
                clean_title = clean_title[:60].strip()

            # -----------------------------------------------------------------
            # 1. CHECK FOR VIDEO FIRST
            # LinkedIn video posts contain <video data-sources="..."> or og:video,
            # and MUST be detected as video before checking poster thumbnails.
            # -----------------------------------------------------------------
            video_sources: List[dict] = []
            poster_url: Optional[str] = None

            for v in soup.find_all("video"):
                poster_url = v.get("data-poster-url") or v.get("poster") or poster_url
                if v.get("data-sources"):
                    try:
                        srcs = json.loads(v["data-sources"])
                        if isinstance(srcs, list):
                            for s in srcs:
                                if isinstance(s, dict) and s.get("src"):
                                    video_sources.append({
                                        "src": s["src"].replace("&amp;", "&"),
                                        "type": s.get("type", "video/mp4"),
                                        "bitrate": int(s.get("data-bitrate") or 0)
                                    })
                    except Exception:
                        pass
                elif v.get("src"):
                    video_sources.append({
                        "src": v["src"].replace("&amp;", "&"),
                        "type": "video/mp4",
                        "bitrate": 0
                    })

            # Check OpenGraph video meta tags if no video tag had sources
            if not video_sources:
                for og_v in soup.find_all("meta", property=re.compile(r"og:video(?::secure_url|:url)?", re.IGNORECASE)):
                    v_content = og_v.get("content")
                    if v_content and ("dms.licdn.com" in v_content or v_content.endswith(".mp4")):
                        video_sources.append({
                            "src": v_content.replace("&amp;", "&"),
                            "type": "video/mp4",
                            "bitrate": 0
                        })

            # If video sources found directly in HTML:
            if video_sources:
                # Sort by bitrate descending to select highest quality stream
                video_sources.sort(key=lambda x: x.get("bitrate", 0), reverse=True)
                best_video = video_sources[0]

                if not poster_url:
                    og_img = soup.find("meta", property="og:image")
                    poster_url = og_img.get("content") if og_img else None

                fname = sanitize_filename(f"{clean_title or 'linkedin_video'}.mp4")
                video_item = MediaItem(
                    url=best_video["src"],
                    media_type="video",
                    filename=fname,
                    mime_type="video/mp4",
                    title=clean_title or "LinkedIn Video",
                    thumbnail_url=poster_url
                )

                return AnalysisResult(
                    success=True,
                    platform="LinkedIn",
                    content_type="video",
                    media_count=1,
                    formats=["mp4", "mkv", "webm", "audio", "m4a"],
                    items=[video_item],
                    previews=[poster_url] if poster_url else [],
                    title=clean_title or "LinkedIn Video",
                    description=description
                )

            # Try yt-dlp on the resolved post URL if HTML didn't expose <video>
            try:
                ytdlp_res = YtDlpService.analyze_url(resolved_url, platform_hint="LinkedIn")
                if ytdlp_res.success and ytdlp_res.media_count > 0 and (
                    ytdlp_res.content_type in ("video", "video_collection") or "mp4" in ytdlp_res.formats
                ):
                    return ytdlp_res
            except Exception:
                pass

            # -----------------------------------------------------------------
            # 2. CHECK FOR MULTI-PAGE DOCUMENTS & IMAGES
            # If no video is present, collect carousel/document pages or photo.
            # -----------------------------------------------------------------
            raw_images: List[str] = []

            # 2a. Schema.org JSON-LD structured data (SocialMediaPosting / Article)
            for script_tag in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script_tag.string or "")
                    if isinstance(data, dict):
                        img_data = data.get("image")
                        if isinstance(img_data, list):
                            for im in img_data:
                                if isinstance(im, dict) and im.get("url"):
                                    raw_images.append(im["url"])
                                elif isinstance(im, str):
                                    raw_images.append(im)
                        elif isinstance(img_data, dict) and img_data.get("url"):
                            raw_images.append(img_data["url"])
                        elif isinstance(img_data, str):
                            raw_images.append(img_data)
                except Exception:
                    pass

            # 2b. Fallback: Search HTML feed-images-content if JSON-LD had no images
            if not raw_images:
                for img_tag in soup.find_all("img"):
                    src = img_tag.get("data-delayed-url") or img_tag.get("src")
                    if src and "media.licdn.com/dms/image" in src and "feedshare" in src:
                        raw_images.append(src)

            # 2c. Fallback: Check OpenGraph meta tags
            if not raw_images:
                og_img = soup.find("meta", property="og:image")
                if og_img and og_img.get("content"):
                    raw_images.append(og_img["content"])

            # Deduplicate image URLs while maintaining document page order
            clean_images: List[str] = []
            seen = set()
            for img_url in raw_images:
                clean_url = img_url.replace("&amp;", "&")
                if clean_url not in seen:
                    seen.add(clean_url)
                    clean_images.append(clean_url)

            if not clean_images:
                return None

            pad_width = 2 if len(clean_images) < 100 else 3
            items: List[MediaItem] = []
            previews: List[str] = []

            for idx, img_url in enumerate(clean_images):
                previews.append(img_url)

                page_num = idx + 1
                fname = f"page_{page_num:0{pad_width}d}.jpg"
                item = MediaItem(
                    url=img_url,
                    media_type="image",
                    filename=sanitize_filename(fname),
                    mime_type="image/jpeg",
                    title=f"Page {page_num}",
                    thumbnail_url=img_url
                )
                items.append(item)

            if len(items) > 1:
                content_type = "image_collection"
                formats = ["pdf", "docx", "zip", "images"]
            else:
                content_type = "image"
                formats = ["original", "pdf", "docx", "zip"]

            return AnalysisResult(
                success=True,
                platform="LinkedIn",
                content_type=content_type,
                media_count=len(items),
                formats=formats,
                items=items,
                previews=previews,
                title=clean_title or "LinkedIn Document",
                description=description
            )

        except Exception as e:
            logger.warning(f"Error parsing LinkedIn page for {url}: {e}")
            return None

    def analyze(self, url: str) -> AnalysisResult:
        # 1. Try page inspection (checks videos first, then carousels/documents/images)
        page_res = self._extract_page_content(url)
        if page_res and page_res.success and page_res.media_count > 0:
            return page_res

        # 2. Try yt-dlp directly
        ytdlp_res = YtDlpService.analyze_url(url, platform_hint="LinkedIn")
        if ytdlp_res.success and ytdlp_res.media_count > 0:
            return ytdlp_res

        # 3. Fallback to generic OpenGraph analyzer
        og_res = GenericDownloader.analyze(url)
        if og_res.success and og_res.media_count > 0:
            og_res.platform = "LinkedIn"
            return og_res

        return AnalysisResult(
            success=False,
            platform="LinkedIn",
            content_type="unknown",
            error_code="CONTENT_UNAVAILABLE",
            error_message="Unable to access LinkedIn post. Content may require authentication or sign-in."
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
