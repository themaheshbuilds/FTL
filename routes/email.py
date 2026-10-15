from flask import Blueprint, request, jsonify
from services.email_service import EmailService
from utils.logging import get_logger

logger = get_logger("linkforge.routes.email")

email_bp = Blueprint("email", __name__)


@email_bp.route("/api/send-email", methods=["POST"], strict_slashes=False)
@email_bp.route("/api/email", methods=["POST"], strict_slashes=False)
def send_email_route():
    """POST /api/send-email
    Deliver a generated or converted file to a user's email address.
    """
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id", "").strip()
    recipient_email = data.get("email", "").strip()

    if not file_id:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_FILE_ID",
                "message": "File identifier is required."
            }
        }), 400

    if not recipient_email:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_EMAIL",
                "message": "Recipient email address is required."
            }
        }), 400

    if not EmailService.validate_email(recipient_email):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_EMAIL",
                "message": "Please enter a valid email address."
            }
        }), 422

    # Client IP for rate limiting
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else request.remote_addr or "unknown"
    base_url = request.host_url.rstrip("/")

    success, msg = EmailService.send_file_email(
        file_id=file_id,
        recipient_email=recipient_email,
        client_ip=client_ip,
        base_url=base_url
    )

    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": "EMAIL_DELIVERY_FAILED",
                "message": msg or "Could not deliver email at this time."
            }
        }), 400

    return jsonify({
        "success": True,
        "message": msg or f"File successfully sent to {recipient_email}!"
    }), 200
