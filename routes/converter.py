import os
import uuid
from flask import Blueprint, request, jsonify
from config import Config
from services.converter_service import ConverterService
from utils.filenames import sanitize_filename
from utils.logging import get_logger

logger = get_logger("linkforge.routes.converter")

converter_bp = Blueprint("converter", __name__, url_prefix="/api")


@converter_bp.route("/convert", methods=["POST"])
def convert_endpoint():
    """POST /api/convert
    Accepts uploaded file(s) and converts them based on conversion_type.
    """
    if "files" not in request.files and "file" not in request.files:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_FILES",
                "message": "No file(s) provided in request."
            }
        }), 400

    uploaded_files = request.files.getlist("files")
    if not uploaded_files or not uploaded_files[0].filename:
        single_file = request.files.get("file")
        if single_file and single_file.filename:
            uploaded_files = [single_file]
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "EMPTY_FILES",
                    "message": "Selected files cannot be empty."
                }
            }), 400

    conversion_type = request.form.get("conversion_type", "").strip()
    output_format = request.form.get("output_format", "").strip()
    custom_filename = request.form.get("custom_filename", "").strip()

    if not conversion_type:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_CONVERSION_TYPE",
                "message": "conversion_type is required."
            }
        }), 400

    # Save uploaded files to temporary staging folder
    staging_id = uuid.uuid4().hex[:12]
    staging_dir = str(Config.TEMP_STORAGE_DIR / f"stage_{staging_id}")
    os.makedirs(staging_dir, exist_ok=True)

    saved_paths = []
    try:
        for idx, f in enumerate(uploaded_files):
            orig_name = sanitize_filename(f.filename or f"upload_{idx + 1}")
            dest_path = os.path.join(staging_dir, orig_name)
            f.save(dest_path)
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                saved_paths.append(dest_path)

        if not saved_paths:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UPLOAD_FAILED",
                    "message": "Failed to save uploaded files."
                }
            }), 400

        ok, job_id, filename, mime_type, filesize, err = ConverterService.convert_files(
            conversion_type=conversion_type,
            input_files=saved_paths,
            output_format=output_format,
            custom_filename=custom_filename
        )

        if not ok:
            return jsonify({
                "success": False,
                "error": {
                    "code": "CONVERSION_FAILED",
                    "message": err or "Conversion failed."
                }
            }), 422

        # Format human-readable size
        size_formatted = "Unknown size"
        if filesize is not None:
            if filesize < 1024 * 1024:
                size_formatted = f"{(filesize / 1024):.1f} KB"
            else:
                size_formatted = f"{(filesize / (1024 * 1024)):.2f} MB"

        return jsonify({
            "success": True,
            "file_id": job_id,
            "filename": filename,
            "mime_type": mime_type,
            "filesize": filesize,
            "size_formatted": size_formatted
        }), 200

    finally:
        # Cleanup staging directory
        try:
            if os.path.exists(staging_dir):
                import shutil
                shutil.rmtree(staging_dir, ignore_errors=True)
        except Exception:
            pass
