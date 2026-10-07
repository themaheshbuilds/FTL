import os
from pathlib import Path
from flask import Blueprint, send_file, jsonify, abort
from services.job_service import JobService
from utils.logging import get_logger

logger = get_logger("linkforge.download")

download_bp = Blueprint("download", __name__)


@download_bp.route("/download/<file_id>", methods=["GET"])
@download_bp.route("/api/download/<file_id>", methods=["GET"])
def download_file(file_id: str):
    """GET /download/<file_id>
    Streams or delivers the generated package file to the user.
    """
    # 1. Path traversal protection: file_id must be alphanumeric
    if not file_id or not file_id.isalnum() or len(file_id) > 32:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_FILE_ID",
                "message": "Invalid download identifier."
            }
        }), 400

    job = JobService.get_job(file_id)
    if not job:
        return jsonify({
            "success": False,
            "error": {
                "code": "EXPIRED_OR_NOT_FOUND",
                "message": "This download has expired or does not exist."
            }
        }), 404

    if not job.output_file_path or not os.path.exists(job.output_file_path):
        return jsonify({
            "success": False,
            "error": {
                "code": "FILE_MISSING",
                "message": "Generated file is no longer available on the server."
            }
        }), 404

    logger.info(f"Serving download for job {file_id}: {job.output_filename}")

    return send_file(
        job.output_file_path,
        as_attachment=True,
        download_name=job.output_filename or "download_file",
        mimetype=job.mime_type or "application/octet-stream"
    )
