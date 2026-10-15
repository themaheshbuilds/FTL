import os
import sys
import traceback
from pathlib import Path
from urllib.parse import parse_qs, unquote

# Ensure project root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class VercelPathMiddleware:
    """WSGI middleware ensuring correct path routing behind Vercel serverless rewrites."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")

        # 1. Primary: Extract captured path from Vercel rewrite parameter (?__path__=...)
        if "__path__=" in query_string:
            qs = parse_qs(query_string)
            if "__path__" in qs and qs["__path__"]:
                raw_path = unquote(qs["__path__"][0]).strip()
                if not raw_path.startswith("/"):
                    raw_path = "/" + raw_path
                # Normalize double slashes
                while "//" in raw_path:
                    raw_path = raw_path.replace("//", "/")
                environ["PATH_INFO"] = raw_path

                # Remove __path__ parameter from query string so request.args remains clean
                clean_params = [p for p in query_string.split("&") if not p.startswith("__path__=")]
                environ["QUERY_STRING"] = "&".join(clean_params)

        # 2. Secondary fallback: HTTP_X_MATCHED_PATH / HTTP_X_FORWARDED_URI if not pointing to script
        elif "HTTP_X_MATCHED_PATH" in environ or "HTTP_X_FORWARDED_URI" in environ:
            matched_path = environ.get("HTTP_X_MATCHED_PATH") or environ.get("HTTP_X_FORWARDED_URI")
            if matched_path:
                path = matched_path.split("?")[0].strip()
                if path and not path.startswith("/api/index"):
                    if not path.startswith("/"):
                        path = "/" + path
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
