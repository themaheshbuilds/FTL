import os
import zipfile
import pytest
from PIL import Image
from services.pdf_service import PdfService
from services.archive_service import ArchiveService


@pytest.fixture
def sample_images(tmp_path):
    """Create sample dummy images for packaging tests."""
    img1_path = str(tmp_path / "img1.jpg")
    img2_path = str(tmp_path / "img2.png")

    # Image 1 (RGB)
    img1 = Image.new("RGB", (200, 200), color="blue")
    img1.save(img1_path, "JPEG")

    # Image 2 (RGBA)
    img2 = Image.new("RGBA", (300, 150), color=(255, 0, 0, 200))
    img2.save(img2_path, "PNG")

    return [img1_path, img2_path]


def test_images_to_pdf(tmp_path, sample_images):
    """Test converting image collection to a valid PDF document."""
    out_pdf = str(tmp_path / "output.pdf")
    success = PdfService.images_to_pdf(sample_images, out_pdf)

    assert success is True
    assert os.path.exists(out_pdf)
    assert os.path.getsize(out_pdf) > 0

    # Ensure valid PDF header
    with open(out_pdf, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"


def test_create_zip_archive(tmp_path, sample_images):
    """Test archiving multiple files into a secure ZIP file."""
    out_zip = str(tmp_path / "output.zip")
    files_to_zip = [
        (sample_images[0], "first_photo.jpg"),
        (sample_images[1], "second_photo.png"),
    ]

    success = ArchiveService.create_zip(files_to_zip, out_zip)
    assert success is True
    assert os.path.exists(out_zip)

    # Inspect zip contents
    with zipfile.ZipFile(out_zip, "r") as zf:
        namelist = zf.namelist()
        assert "first_photo.jpg" in namelist
        assert "second_photo.png" in namelist
        # Test integrity
        assert zf.testzip() is None


def test_images_to_pdf_with_caption(tmp_path, sample_images):
    """Test converting image collection to PDF with title and caption cover page."""
    out_pdf = str(tmp_path / "with_caption.pdf")
    success = PdfService.images_to_pdf(
        sample_images,
        out_pdf,
        title="Full Stack Handbook",
        caption="A complete guide to backend and frontend engineering.",
        include_caption=True
    )

    assert success is True
    assert os.path.exists(out_pdf)
    with open(out_pdf, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_images_to_docx(tmp_path, sample_images):
    """Test converting image collection to a Microsoft Word document (.docx)."""
    from services.docx_service import DocxService
    out_docx = str(tmp_path / "output.docx")
    success = DocxService.images_to_docx(
        sample_images,
        out_docx,
        title="DSA Handwritten Notes",
        caption="Summary notes covering Binary Trees and Dynamic Programming.",
        include_caption=True
    )

    assert success is True
    assert os.path.exists(out_docx)
    assert os.path.getsize(out_docx) > 0
    # Valid docx is a PK zip archive
    with open(out_docx, "rb") as f:
        assert f.read(2) == b"PK"


def test_media_service_docx_and_custom_filename(tmp_path):
    """Test MediaService packaging into DOCX with custom filename and caption."""
    from unittest.mock import patch
    from models.result import AnalysisResult
    from models.media import MediaItem
    from services.media_service import MediaService

    img_path = str(tmp_path / "slide1.jpg")
    img = Image.new("RGB", (100, 100), color="purple")
    img.save(img_path, "JPEG")

    items = [
        MediaItem(url="http://fake.url/img1.jpg", media_type="image", filename="slide1.jpg")
    ]
    fake_result = AnalysisResult(
        success=True,
        platform="LinkedIn",
        content_type="image_collection",
        media_count=1,
        items=items,
        title="Original LinkedIn Post Title",
        description="Here is the full description and caption."
    )

    with patch("services.url_analyzer.UrlAnalyzer.analyze_url", return_value=fake_result):
        with patch.object(MediaService, "_download_items_to_dir", return_value=[img_path]):
            ok, job_id, filename, mime, size, err = MediaService.process_and_package(
                url="https://lnkd.in/p/test",
                output_format="docx",
                custom_filename="my_custom_cheat_sheet",
                include_caption=True
            )

            assert ok is True
            assert filename == "my_custom_cheat_sheet.docx"
            assert mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            assert size is not None and size > 0


def test_media_service_mkv_packaging(tmp_path):
    """Test MediaService packaging video into MKV container with correct MIME and extension."""
    from unittest.mock import patch
    from models.result import AnalysisResult
    from models.media import MediaItem
    from services.media_service import MediaService

    fake_video = tmp_path / "dummy_reel.mp4"
    fake_video.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00" + b"A" * 150000)

    items = [
        MediaItem(url="https://instagram.com/reel_vid.mp4", media_type="video", filename="dummy_reel.mp4")
    ]
    fake_result = AnalysisResult(
        success=True,
        platform="Instagram",
        content_type="video",
        media_count=1,
        items=items,
        title="Trending Reel",
        description="Epic video moment"
    )

    with patch("services.url_analyzer.UrlAnalyzer.analyze_url", return_value=fake_result):
        with patch("services.generic_downloader.GenericDownloader.download_file", return_value=(True, str(fake_video), None)):
            ok, job_id, filename, mime, size, err = MediaService.process_and_package(
                url="https://www.instagram.com/reel/DeKey7XS1dU/",
                output_format="mkv"
            )

            assert ok is True, f"Packaging failed: {err}"
            assert filename.endswith(".mkv"), f"Expected .mkv filename, got {filename}"
            assert mime == "video/x-matroska", f"Expected video/x-matroska, got {mime}"
            assert size is not None and size > 0


