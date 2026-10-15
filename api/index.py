import os
import sys
import traceback
from pathlib import Path

# Ensure project root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class VercelPathMiddleware:
    """WSGI middleware ensuring correct path routing behind Vercel serverless rewrites."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Vercel sends the client-facing path in HTTP_X_MATCHED_PATH or HTTP_X_FORWARDED_URI
        matched_path = environ.get("HTTP_X_MATCHED_PATH") or environ.get("HTTP_X_FORWARDED_URI")
        if matched_path:
            # Strip query string if present
            path = matched_path.split("?")[0]
            if path and not path.startswith("/api/index"):
                environ["PATH_INFO"] = path

        return self.wsgi_app(environ, start_response)


try:
    from app import app as flask_app
    flask_app.wsgi_app = VercelPathMiddleware(flask_app.wsgi_app)
    app = flask_app
except Exception as e:
    import logging
    from flask import Flask, jsonify

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("linkforge.bootstrap_error")
    logger.error("Failed to bootstrap LinkForge app: %s\n%s", e, traceback.format_exc())

    fallback_app = Flask(__name__)

    @fallback_app.route("/", defaults={"path": ""})
    @fallback_app.route("/<path:path>")
    def catch_all(path):
        return jsonify({
            "success": False,
            "error": {
                "code": "BOOTSTRAP_ERROR",
                "message": f"LinkForge serverless initialization error: {str(e)}",
                "traceback": traceback.format_exc()
            }
        }), 500

    app = fallback_app
