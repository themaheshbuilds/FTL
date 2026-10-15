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
        import json

        job = cls._jobs.get(job_id)
        if not job:
            # Fallback 1: check meta.json in generated directory
            try:
                gen_dir = cls.get_generated_dir(job_id)
                meta_file = gen_dir / "meta.json"
                if meta_file.is_file():
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    job = Job(
                        job_id=job_id,
                        url=data.get("url", ""),
                        requested_format=data.get("requested_format", ""),
                        status=data.get("status", "completed"),
                        created_at=data.get("created_at", time.time()),
                        expires_at=data.get("expires_at", time.time() + 1800),
                        output_file_path=data.get("output_file_path"),
                        output_filename=data.get("output_filename"),
                        mime_type=data.get("mime_type"),
                        filesize=data.get("filesize")
                    )
                    cls._jobs[job_id] = job
            except Exception as e:
                logger.debug(f"Failed to read disk job metadata for {job_id}: {e}")

        # Fallback 2: check if any file exists in generated directory
        if not job:
            try:
                gen_dir = cls.get_generated_dir(job_id)
                if gen_dir.is_dir():
                    files = [f for f in gen_dir.iterdir() if f.is_file() and f.name != "meta.json"]
                    if files:
                        target = files[0]
                        from utils.mime import guess_mime_type
                        job = Job(
                            job_id=job_id,
                            url="",
                            requested_format="original",
                            status="completed",
                            created_at=time.time(),
                            expires_at=time.time() + 1800,
                            output_file_path=str(target),
                            output_filename=target.name,
                            mime_type=guess_mime_type(target.name),
                            filesize=target.stat().st_size
                        )
                        cls._jobs[job_id] = job
            except Exception as e:
                logger.debug(f"Failed to scan generated directory for {job_id}: {e}")

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
        import json

        job = cls._jobs.get(job_id)
        if job:
            job.status = "completed"
            job.output_file_path = output_path
            job.output_filename = filename
            job.mime_type = mime_type
            job.filesize = filesize

        # Persist metadata to disk for serverless worker persistence
        try:
            gen_dir = cls.get_generated_dir(job_id)
            meta_file = gen_dir / "meta.json"
            meta_data = {
                "job_id": job_id,
                "output_file_path": str(output_path),
                "output_filename": filename,
                "mime_type": mime_type,
                "filesize": filesize,
                "expires_at": job.expires_at if job else (time.time() + 1800),
                "status": "completed"
            }
            meta_file.write_text(json.dumps(meta_data), encoding="utf-8")
        except Exception as e:
            logger.debug(f"Could not persist job metadata to disk for {job_id}: {e}")

    @classmethod
    def update_job_failure(cls, job_id: str, error_code: str, error_message: str) -> None:
        """Update job upon failure."""
        job = cls._jobs.get(job_id)
        if job:
            job.status = "failed"
            job.error_code = error_code
            job.error_message = error_message
