from urllib.parse import urlparse, parse_qs, unquote
import re
from typing import List
from extractors.base import BaseExtractor
from models.result import AnalysisResult
from models.media import MediaItem
from utils.filenames import sanitize_filename
from utils.logging import get_logger

logger = get_logger("linkforge.extractor.torrent")


class TorrentExtractor(BaseExtractor):
    """Extractor for BitTorrent Magnet URIs and .torrent files."""

    def can_handle(self, url: str) -> bool:
        low = url.strip().lower()
        return low.startswith("magnet:") or low.endswith(".torrent")

    def analyze(self, url: str) -> AnalysisResult:
        logger.info(f"Analyzing BitTorrent URI: {url[:60]}...")
        low = url.strip().lower()

        if low.startswith("magnet:"):
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)

            # Extract info hash and display name
            xt_list = qs.get("xt", [])
            dn_list = qs.get("dn", [])

            info_hash = ""
            for xt in xt_list:
                if "urn:btih:" in xt.lower():
                    info_hash = xt.split("urn:btih:")[-1]
                    break

            display_name = unquote(dn_list[0]) if dn_list else (f"Torrent_{info_hash[:10]}" if info_hash else "Torrent Download")
            safe_name = sanitize_filename(display_name)

            item = MediaItem(
                url=url,
                media_type="torrent",
                filename=f"{safe_name}.torrent",
                title=display_name,
                mime_type="application/x-bittorrent"
            )

            return AnalysisResult(
                success=True,
                platform="BitTorrent",
                content_type="torrent",
                media_count=1,
                formats=["torrent_direct", "zip"],
                items=[item],
                previews=[],
                title=display_name,
                description=f"BitTorrent Magnet Link (Hash: {info_hash or 'BTIH'})"
            )

        # .torrent file direct link
        filename = url.split("/")[-1].split("?")[0] or "download.torrent"
        title = filename.replace(".torrent", "").replace("_", " ")
        item = MediaItem(
            url=url,
            media_type="torrent",
            filename=sanitize_filename(filename),
            title=title,
            mime_type="application/x-bittorrent"
        )
        return AnalysisResult(
            success=True,
            platform="BitTorrent",
            content_type="torrent",
            media_count=1,
            formats=["torrent_direct", "zip"],
            items=[item],
            previews=[],
            title=title,
            description="BitTorrent File"
        )

    def extract(self, url: str) -> List[MediaItem]:
        res = self.analyze(url)
        return res.items if res.success else []
