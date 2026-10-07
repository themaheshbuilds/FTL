import uuid
import time
from pathlib import Path
from typing import Optional, Dict
from config import Config
from models.job import Job
from services.cleanup_service import CleanupService
from utils.logging import get_logger

logger = get_logger("linkforge.job_service")


class JobService:
    """Manages job lifecycles, isolated workspaces, and lookup."""

    _jobs: Dict[str, Job] = {}

    @classmethod
    def create_job(cls, url: str, requested_format: str) -> Job:
        """Create a new job with an isolated directory."""
        # Trigger cleanup of expired files periodically
        CleanupService.clean_expired_files()

        job_id = uuid.uuid4().hex[:12]
        expires_at = time.time() + (Config.FILE_EXPIRATION_MINUTES * 60)

        job = Job(
            job_id=job_id,
            url=url,
            requested_format=requested_format,
            status="queued",
            created_at=time.time(),
            expires_at=expires_at
        )

        # Allocate directories
        temp_dir = cls.get_temp_dir(job_id)
        gen_dir = cls.get_generated_dir(job_id)
        temp_dir.mkdir(parents=True, exist_ok=True)
        gen_dir.mkdir(parents=True, exist_ok=True)

        cls._jobs[job_id] = job
        return job

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID, returning None if expired or not found."""
        job = cls._jobs.get(job_id)
        if not job:
            return None
        if job.is_expired():
            job.status = "expired"
            CleanupService.cleanup_job(job_id)
            cls._jobs.pop(job_id, None)
            return None
        return job

    @classmethod
    def get_temp_dir(cls, job_id: str) -> Path:
        """Get the isolated temp directory path for a job."""
        return Config.TEMP_STORAGE_DIR / job_id

    @classmethod
    def get_generated_dir(cls, job_id: str) -> Path:
        """Get the isolated generated directory path for a job."""
        return Config.GENERATED_STORAGE_DIR / job_id

    @classmethod
    def update_job_success(cls, job_id: str, output_path: str, filename: str, mime_type: str, filesize: int) -> None:
        """Update job upon successful completion."""
        job = cls._jobs.get(job_id)
        if job:
            job.status = "completed"
            job.output_file_path = output_path
            job.output_filename = filename
            job.mime_type = mime_type
            job.filesize = filesize

    @classmethod
    def update_job_failure(cls, job_id: str, error_code: str, error_message: str) -> None:
        """Update job upon failure."""
        job = cls._jobs.get(job_id)
        if job:
            job.status = "failed"
            job.error_code = error_code
            job.error_message = error_message
