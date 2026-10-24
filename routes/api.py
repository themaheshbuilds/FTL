from flask import Blueprint, request, jsonify
from services.url_analyzer import UrlAnalyzer
from services.media_service import MediaService
from utils.logging import get_logger

logger = get_logger("linkforge.api")

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/analyze", methods=["POST"], strict_slashes=False)
def analyze_endpoint():
    """POST /api/analyze
    Analyzes submitted URL and returns detected content metadata and available formats.
    """
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request must be JSON with a 'url' field."
            }
        }), 400

    data = request.get_json() or {}
    raw_url = data.get("url")

    if not raw_url or not isinstance(raw_url, str):
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_URL",
                "message": "A valid URL string is required."
            }
        }), 400

    result = UrlAnalyzer.analyze_url(raw_url)
    status_code = 200 if result.success else 422
    return jsonify(result.to_dict()), status_code


@api_bp.route("/generate", methods=["POST"], strict_slashes=False)
def generate_endpoint():
    """POST /api/generate
    Processes and packages content into the requested format (PDF, ZIP, MP4, original).
    """
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request must be JSON."
            }
        }), 400

    data = request.get_json() or {}
    url = data.get("url")
    output_format = data.get("output_format") or data.get("format") or "original"
    quality = data.get("quality", "best")
    custom_filename = data.get("custom_filename") or data.get("filename")
    include_caption = bool(data.get("include_caption", False))

    if not url or not isinstance(url, str):
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_URL",
                "message": "URL is required."
            }
        }), 400

    selected_indices = data.get("selected_indices")
    if selected_indices is not None and not isinstance(selected_indices, list):
        selected_indices = None

    ok, job_id, filename, mime_type, filesize, err = MediaService.process_and_package(
        url=url,
        output_format=output_format,
        quality=quality,
        custom_filename=custom_filename,
        include_caption=include_caption,
        selected_indices=selected_indices
    )

    if not ok:
        return jsonify({
            "success": False,
            "error": {
                "code": "GENERATION_FAILED",
                "message": err or "Failed to process and package media."
            }
        }), 422

    # Format human-readable size
    size_formatted = "Unknown size"
    if filesize is not None:
        if filesize < 1024 * 1024:
            size_formatted = f"{(filesize / 1024):.1f} KB"
        else:
            size_formatted = f"{(filesize / (1024 * 1024)):.2f} MB"

    res_payload = {
        "success": True,
        "file_id": job_id,
        "filename": filename,
        "mime_type": mime_type,
        "filesize": filesize,
        "size_formatted": size_formatted,
        "download_url": f"/download/{job_id}"
    }

    # Embed data_url or direct_url for instant 0-latency serverless download
    try:
        from services.job_service import JobService
        import base64
        import os
        job = JobService.get_job(job_id)
        if job and getattr(job, "direct_url", None):
            res_payload["direct_url"] = job.direct_url
            res_payload["download_url"] = job.direct_url
        elif job and job.output_file_path and os.path.isfile(job.output_file_path):
            actual_size = os.path.getsize(job.output_file_path)
            if actual_size <= int(3.2 * 1024 * 1024):
                with open(job.output_file_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                res_payload["data_url"] = f"data:{mime_type or 'application/octet-stream'};base64,{b64}"
    except Exception as e:
        logger.debug(f"Could not build data_url for job {job_id}: {e}")

    return jsonify(res_payload), 200
