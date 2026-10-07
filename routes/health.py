from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint.
    
    Returns:
        JSON response with system status.
    """
    return jsonify({"status": "ok"}), 200

