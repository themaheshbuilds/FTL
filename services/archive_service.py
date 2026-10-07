import os
import zipfile
from typing import List, Tuple
from config import Config
from utils.filenames import sanitize_filename
from utils.logging import get_logger

logger = get_logger("linkforge.archive_service")


class ArchiveService:
    """Creates secure ZIP archives of downloaded media files."""

    @classmethod
    def create_zip(cls, files_to_zip: List[Tuple[str, str]], output_zip_path: str) -> bool:
        """Create a ZIP archive from a list of (local_file_path, desired_arcname) pairs.
        
        Prevents path traversal in arcnames and enforces total uncompressed size limits.
        """
        if not files_to_zip:
            logger.warning("No files provided for ZIP archive.")
            return False

        try:
            os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
            total_uncompressed_bytes = 0
            existing_arcnames = set()

            with zipfile.ZipFile(output_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for file_path, arcname in files_to_zip:
                    if not os.path.exists(file_path):
                        continue

                    file_size = os.path.getsize(file_path)
                    total_uncompressed_bytes += file_size
                    if total_uncompressed_bytes > Config.MAX_FILE_SIZE_BYTES:
                        logger.warning("ZIP creation exceeded maximum uncompressed size limit.")
                        zf.close()
                        if os.path.exists(output_zip_path):
                            os.remove(output_zip_path)
                        return False

                    # Sanitize internal zip filename to eliminate path traversal
                    safe_arcname = sanitize_filename(arcname)
                    # Deduplicate internal names
                    counter = 1
                    name, ext = os.path.splitext(safe_arcname)
                    unique_arcname = safe_arcname
                    while unique_arcname in existing_arcnames:
                        unique_arcname = f"{name}_{counter}{ext}"
                        counter += 1
                    existing_arcnames.add(unique_arcname)

                    zf.write(file_path, arcname=unique_arcname)

            return os.path.exists(output_zip_path) and os.path.getsize(output_zip_path) > 0

        except Exception as e:
            logger.error(f"Failed to create ZIP archive at {output_zip_path}: {e}", exc_info=True)
            if os.path.exists(output_zip_path):
                try:
                    os.remove(output_zip_path)
                except Exception:
                    pass
            return False
