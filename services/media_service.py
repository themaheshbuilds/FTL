import os
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import requests
from config import Config
from models.result import AnalysisResult
from models.media import MediaItem
from services.job_service import JobService
from services.pdf_service import PdfService
from services.docx_service import DocxService
from services.archive_service import ArchiveService
from services.generic_downloader import GenericDownloader
from services.ytdlp_service import YtDlpService
from services.url_analyzer import UrlAnalyzer
from utils.filenames import sanitize_filename
from utils.mime import normalize_content_type, extension_for_mime_type
from utils.ffmpeg_helper import extract_audio, remux_video
from utils.logging import get_logger

logger = get_logger("linkforge.media_service")


class MediaService:
    """Orchestrates media processing, downloading, and packaging."""

    @classmethod
    def process_and_package(
        cls,
        url: str,
        output_format: str,
        quality: str = "best",
        custom_filename: Optional[str] = None,
        include_caption: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str], Optional[int], Optional[str]]:
        """Process and package media based on user's requested output format and options.
        
        Returns:
            (success, job_id, output_filename, mime_type, filesize, error_message)
        """
        # 1. Analyze URL
        analysis = UrlAnalyzer.analyze_url(url)
        if not analysis.success:
            return False, None, None, None, None, analysis.error_message

        # Determine clean base filename without extensions
        raw_base = (custom_filename or "").strip()
        if not raw_base:
            raw_base = analysis.title or "download_file"
        base_stem = os.path.splitext(raw_base)[0] if "." in raw_base else raw_base
        safe_base = sanitize_filename(base_stem, default_name="download_file")

        # 2. Create Job
        job = JobService.create_job(url, output_format)
        temp_dir = JobService.get_temp_dir(job.job_id)
        gen_dir = JobService.get_generated_dir(job.job_id)

        try:
            format_lower = (output_format or "original").lower()

            # --- CASE A: PDF from images / documents ---
            if format_lower in ("pdf", "images_pdf"):
                downloaded_image_paths = cls._download_items_to_dir(analysis.items, str(temp_dir), filter_type="image")
                if not downloaded_image_paths:
                    return False, None, None, None, None, "No downloadable images found to convert to PDF."

                pdf_name = f"{safe_base}.pdf"
                out_pdf_path = str(gen_dir / pdf_name)

                ok = PdfService.images_to_pdf(
                    downloaded_image_paths,
                    out_pdf_path,
                    title=analysis.title,
                    caption=analysis.description,
                    include_caption=include_caption
                )
                if not ok or not os.path.exists(out_pdf_path):
                    return False, None, None, None, None, "PDF compilation failed."

                fsize = os.path.getsize(out_pdf_path)
                JobService.update_job_success(job.job_id, out_pdf_path, pdf_name, "application/pdf", fsize)
                return True, job.job_id, pdf_name, "application/pdf", fsize, None

            # --- CASE B: Microsoft Word (.docx / .doc) ---
            if format_lower in ("doc", "docx", "word"):
                downloaded_image_paths = cls._download_items_to_dir(analysis.items, str(temp_dir), filter_type="image")
                if not downloaded_image_paths:
                    return False, None, None, None, None, "No downloadable images found to convert to Word Document."

                docx_name = f"{safe_base}.docx"
                out_docx_path = str(gen_dir / docx_name)

                ok = DocxService.images_to_docx(
                    downloaded_image_paths,
                    out_docx_path,
                    title=analysis.title,
                    caption=analysis.description,
                    include_caption=include_caption
                )
                if not ok or not os.path.exists(out_docx_path):
                    return False, None, None, None, None, "Word document generation failed."

                fsize = os.path.getsize(out_docx_path)
                docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                JobService.update_job_success(job.job_id, out_docx_path, docx_name, docx_mime, fsize)
                return True, job.job_id, docx_name, docx_mime, fsize, None

            # --- CASE C: ZIP Archive ---
            if format_lower in ("zip", "images_zip", "all_zip") or (format_lower == "images" and len(analysis.items) > 1):
                filter_type = "image" if format_lower in ("images_zip", "images") else None
                downloaded_paths = cls._download_items_to_dir(analysis.items, str(temp_dir), filter_type=filter_type)
                if not downloaded_paths:
                    return False, None, None, None, None, "No downloadable media found to package into ZIP."

                files_to_zip = [(p, os.path.basename(p)) for p in downloaded_paths]

                # Optional caption.txt inside ZIP
                if include_caption and analysis.description:
                    cap_path = str(temp_dir / "caption.txt")
                    with open(cap_path, "w", encoding="utf-8") as f:
                        f.write(f"Title: {analysis.title or 'N/A'}\n")
                        f.write(f"Platform: {analysis.platform}\n")
                        f.write(f"Source URL: {url}\n\n")
                        f.write(f"Caption:\n{analysis.description}\n")
                    files_to_zip.append((cap_path, "caption.txt"))

                zip_name = f"{safe_base}.zip"
                out_zip_path = str(gen_dir / zip_name)

                ok = ArchiveService.create_zip(files_to_zip, out_zip_path)
                if not ok or not os.path.exists(out_zip_path):
                    return False, None, None, None, None, "ZIP packaging failed."

                fsize = os.path.getsize(out_zip_path)
                JobService.update_job_success(job.job_id, out_zip_path, zip_name, "application/zip", fsize)
                return True, job.job_id, zip_name, "application/zip", fsize, None

            # --- CASE D: Video / Containers (MP4, MKV, WEBM) / Audio (MP3, M4A) ---
            if format_lower in ("mp4", "mkv", "webm", "video", "audio", "mp3", "m4a"):
                is_audio = format_lower in ("audio", "mp3", "m4a")
                audio_ext = "m4a" if format_lower == "m4a" else "mp3"
                video_container = "mkv" if format_lower == "mkv" else ("webm" if format_lower == "webm" else "mp4")

                target_format = "audio" if is_audio else quality

                # 1. Try yt-dlp first
                downloaded_file = YtDlpService.download_media(
                    url,
                    str(temp_dir),
                    format_filter=target_format
                )

                # 2. Fallback to direct download of media item stream if yt-dlp did not download
                if not downloaded_file or not os.path.exists(downloaded_file):
                    if analysis.items:
                        target_item = next((item for item in analysis.items if item.media_type in ("video", "audio")), analysis.items[0])
                        ok, dpath, err = GenericDownloader.download_file(target_item.url, str(temp_dir), target_item.filename)
                        if ok and dpath and os.path.exists(dpath):
                            downloaded_file = dpath

                if not downloaded_file or not os.path.exists(downloaded_file):
                    return False, None, None, None, None, "Could not extract or download this video. It may be restricted or unsupported."

                # If Audio was requested:
                if is_audio:
                    final_name = f"{safe_base}.{audio_ext}"
                    final_path = str(gen_dir / final_name)
                    ok = extract_audio(downloaded_file, final_path, target_format=audio_ext)
                    if not ok or not os.path.exists(final_path):
                        return False, None, None, None, None, f"Failed to extract {audio_ext.upper()} audio."

                    fsize = os.path.getsize(final_path)
                    mime = "audio/mp4" if audio_ext == "m4a" else "audio/mpeg"
                    JobService.update_job_success(job.job_id, final_path, final_name, mime, fsize)
                    return True, job.job_id, final_name, mime, fsize, None

                # If Video was requested (MP4, MKV, WEBM):
                final_name = f"{safe_base}.{video_container}"
                final_path = str(gen_dir / final_name)
                caption_text = analysis.description if include_caption else None

                ok = remux_video(downloaded_file, final_path, target_format=video_container, caption=caption_text)
                if not ok or not os.path.exists(final_path):
                    # Direct move fallback if remux was not needed and extension matches
                    curr_ext = os.path.splitext(downloaded_file)[1].lstrip('.').lower()
                    if curr_ext == video_container:
                        import shutil
                        shutil.move(downloaded_file, final_path)
                    else:
                        return False, None, None, None, None, f"Failed to package video into {video_container.upper()}."

                fsize = os.path.getsize(final_path)
                mime_map = {
                    "mp4": "video/mp4",
                    "mkv": "video/x-matroska",
                    "webm": "video/webm"
                }
                mime = mime_map.get(video_container, "video/mp4")
                JobService.update_job_success(job.job_id, final_path, final_name, mime, fsize)
                return True, job.job_id, final_name, mime, fsize, None

            # --- CASE E: Original / Direct File ---
            if analysis.items:
                target_item = analysis.items[0]
                orig_ext = os.path.splitext(target_item.filename)[1] if target_item.filename else ""
                final_name = f"{safe_base}{orig_ext}" if orig_ext else (target_item.filename or "download_file")
                ok, dpath, err = GenericDownloader.download_file(target_item.url, str(gen_dir), final_name)
                if ok and dpath and os.path.exists(dpath):
                    fname = os.path.basename(dpath)
                    fsize = os.path.getsize(dpath)
                    mime = target_item.mime_type
                    JobService.update_job_success(job.job_id, dpath, fname, mime, fsize)
                    return True, job.job_id, fname, mime, fsize, None
                return False, None, None, None, None, err or "Failed to download original file."

            return False, None, None, None, None, f"Unsupported format '{output_format}' for this content."

        except Exception as e:
            logger.error(f"Error in process_and_package for {url}: {e}", exc_info=True)
            return False, None, None, None, None, "An internal error occurred during processing."

    @classmethod
    def _download_items_to_dir(cls, items: List[MediaItem], target_dir: str, filter_type: Optional[str] = None) -> List[str]:
        """Download list of MediaItems into the directory."""
        downloaded = []
        for idx, item in enumerate(items):
            if filter_type and item.media_type != filter_type:
                continue
            fname = sanitize_filename(item.filename or f"item_{idx + 1}")
            ok, local_path, err = GenericDownloader.download_file(item.url, target_dir, fname)
            if ok and local_path:
                downloaded.append(local_path)
        return downloaded
