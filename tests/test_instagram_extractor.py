import pytest
from unittest.mock import patch, MagicMock
from extractors.instagram import InstagramExtractor
from services.media_service import MediaService
from models.result import AnalysisResult
from models.media import MediaItem


def test_instagram_can_handle():
    extractor = InstagramExtractor()
    assert extractor.can_handle("https://www.instagram.com/p/DdZSUOIn9lQ/")
    assert extractor.can_handle("https://instagram.com/reel/C1234567890/")
    assert not extractor.can_handle("https://www.youtube.com/watch?v=123")
    assert not extractor.can_handle("https://twitter.com/user/status/123")


def test_instagram_carousel_photo_extraction():
    extractor = InstagramExtractor()
    mock_info = {
        "title": "Post by test_user",
        "description": "Test carousel",
        "entries": [
            {
                "id": "item1",
                "formats": [],
                "thumbnails": [
                    {"url": "https://cdn.example.com/item1_thumb.jpg"},
                    {"url": "https://cdn.example.com/item1_highres.jpg"}
                ]
            },
            {
                "id": "item2",
                "formats": [],
                "thumbnails": [
                    {"url": "https://cdn.example.com/item2_thumb.jpg"},
                    {"url": "https://cdn.example.com/item2_highres.jpg"}
                ]
            }
        ]
    }

    with patch("extractors.instagram.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ie = MagicMock()
        mock_ie._real_extract.return_value = mock_info
        mock_ydl.get_info_extractor.return_value = mock_ie
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = extractor.analyze("https://www.instagram.com/p/test_carousel/")
        assert res.success is True
        assert res.platform == "Instagram"
        assert res.content_type == "image_collection"
        assert res.media_count == 2
        assert "pdf" in res.formats
        assert "zip" in res.formats
        assert res.items[0].url == "https://cdn.example.com/item1_highres.jpg"
        assert res.items[0].media_type == "image"
        assert res.items[1].url == "https://cdn.example.com/item2_highres.jpg"


def test_instagram_single_photo_extraction():
    extractor = InstagramExtractor()
    mock_info = {
        "id": "single123",
        "title": "Single Photo",
        "formats": [],
        "thumbnails": [
            {"url": "https://cdn.example.com/single_thumb.jpg"},
            {"url": "https://cdn.example.com/single_full.jpg"}
        ]
    }

    with patch("extractors.instagram.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ie = MagicMock()
        mock_ie._real_extract.return_value = mock_info
        mock_ydl.get_info_extractor.return_value = mock_ie
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = extractor.analyze("https://www.instagram.com/p/single123/")
        assert res.success is True
        assert res.content_type == "image"
        assert res.media_count == 1
        assert res.items[0].url == "https://cdn.example.com/single_full.jpg"


def test_instagram_private_or_restricted():
    extractor = InstagramExtractor()
    with patch.object(extractor, "_extract_via_instagram_ie", return_value=None):
        with patch("services.ytdlp_service.YtDlpService.analyze_url") as mock_ytdlp:
            mock_ytdlp.return_value = AnalysisResult(
                success=False,
                platform="Instagram",
                content_type="unknown",
                error_code="EXTRACTION_FAILED",
                error_message="Private"
            )
            with patch("services.generic_downloader.GenericDownloader.analyze") as mock_gen:
                mock_gen.return_value = AnalysisResult(
                    success=False,
                    platform="Generic",
                    content_type="unknown",
                    error_code="NO_MEDIA_FOUND",
                    error_message="No media"
                )

                res = extractor.analyze("https://www.instagram.com/p/private_post/")
                assert res.success is False
                assert res.error_code == "CONTENT_UNAVAILABLE"


def test_instagram_video_progressive_selection():
    extractor = InstagramExtractor()
    mock_info = {
        "id": "reel_test",
        "title": "Video by test_creator",
        "formats": [
            {"format_id": "prog1", "vcodec": None, "acodec": None, "url": "https://cdn.example.com/progressive_video.mp4", "height": 720},
            {"format_id": "dash_v", "vcodec": "vp9", "acodec": "none", "url": "https://cdn.example.com/dash_video_only.mp4", "height": 1080},
            {"format_id": "dash_a", "vcodec": "none", "acodec": "mp4a", "url": "https://cdn.example.com/dash_audio_only.m4a"}
        ],
        "thumbnails": [
            {"url": "https://cdn.example.com/thumb.jpg"}
        ]
    }

    with patch("extractors.instagram.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ie = MagicMock()
        mock_ie._real_extract.return_value = mock_info
        mock_ydl.get_info_extractor.return_value = mock_ie
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = extractor.analyze("https://www.instagram.com/reel/reel_test/")
        assert res.success is True
        assert res.content_type == "video"
        assert res.media_count == 1
        # MUST select progressive video, NOT the audio-only dash stream!
        assert res.items[0].url == "https://cdn.example.com/progressive_video.mp4"
