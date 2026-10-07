import os
import shutil
import time
from pathlib import Path
from config import Config
from utils.logging import get_logger

logger = get_logger("linkforge.cleanup")


class CleanupService:
    """Manages periodic and on-demand cleanup of temporary and generated files."""

    @classmethod
    def clean_expired_files(cls, max_age_minutes: int = Config.FILE_EXPIRATION_MINUTES) -> int:
        """Scan temp and generated storage folders and remove expired items."""
        now = time.time()
        max_age_seconds = max_age_minutes * 60
        cleaned_count = 0

        target_dirs = [Config.TEMP_STORAGE_DIR, Config.GENERATED_STORAGE_DIR]

        for base_dir in target_dirs:
            if not base_dir.exists():
                continue

            for entry in os.scandir(base_dir):
                # Never remove .gitkeep
                if entry.name == ".gitkeep":
                    continue

                try:
                    stat = entry.stat()
                    file_age = now - stat.st_mtime
                    if file_age > max_age_seconds:
                        if entry.is_dir():
                            shutil.rmtree(entry.path, ignore_errors=True)
                            cleaned_count += 1
                        elif entry.is_file():
                            os.remove(entry.path)
                            cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Error cleaning expired item {entry.path}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} expired storage items.")
        return cleaned_count

    @classmethod
    def cleanup_job(cls, job_id: str) -> None:
        """Immediately remove isolated storage directories for a specific job."""
        if not job_id or not job_id.isalnum():
            return

        temp_dir = Config.TEMP_STORAGE_DIR / job_id
        gen_dir = Config.GENERATED_STORAGE_DIR / job_id

        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if gen_dir.exists():
            shutil.rmtree(gen_dir, ignore_errors=True)
