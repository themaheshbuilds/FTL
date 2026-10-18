import os
import re
import urllib.parse
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from config import get_config, Config
from routes.health import health_bp
from routes.web import web_bp
from routes.api import api_bp
from routes.download import download_bp
from routes.converter import converter_bp
from routes.email import email_bp
from utils.logging import setup_logging, get_logger

logger = get_logger("linkforge.app")
BASE_DIR = Path(__file__).resolve().parent


def create_app(config_object=None) -> Flask:
    """Application factory for LinkForge."""
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        static_url_path="/static"
    )

    # Strict slashes configuration (permissive routing for trailing slashes)
    app.url_map.strict_slashes = False

    # Load configuration
    if config_object is None:
        config_object = get_config()
    app.config.from_object(config_object)

    # Initialize logging
    setup_logging(app.config.get("LOG_LEVEL", "INFO"))

    # Ensure storage directories exist
    try:
        config_object.ensure_storage_dirs()
    except Exception as e:
        logger.warning(f"Could not initialize local storage dirs: {e}")

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(converter_bp)
    app.register_blueprint(email_bp)

    # Response caching policy: prevent browser from caching dynamic HTML
    @app.after_request
    def set_cache_headers(response):
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # Application-wide error handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        # API endpoints and programmatic clients receive JSON
        if (
            request.path.startswith("/api/")
            or request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.headers.get("Accept") == "application/json"
        ):
            return jsonify({
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested API endpoint was not found."
                }
            }), 404

        # All browser web page navigations receive the styled LinkForge error page
        return render_template(
            "error.html",
            error_code="404",
            error_title="Page Not Found",
            error_message="The page or tool you were looking for does not exist or has moved."
        ), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            }
        }), 500

    # Wrap WSGI app with Vercel routing middleware
    app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

    return app


class VercelWSGIMiddleware:
    """WSGI Middleware for seamless Vercel serverless routing."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        current_path = environ.get("PATH_INFO", "")

        # 1. Primary mechanism: Route captured in query parameter (?__route=/...)
        if "__route=" in query_string:
            params = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            if "__route" in params and params["__route"]:
                raw_route = params["__route"][0].strip()
                clean_route = re.sub(r"^/+", "/", raw_route) if raw_route else "/"
                environ["PATH_INFO"] = clean_route

                # Remove internal __route param from QUERY_STRING
                del params["__route"]
                environ["QUERY_STRING"] = urllib.parse.urlencode(params, doseq=True)

        # 2. Secondary fallback: Check proxy / CDN path headers
        elif current_path in ("/api/index", "/api/index.py", "/api", ""):
            for header_key in (
                "HTTP_X_FORWARDED_URI",
                "HTTP_X_ORIGINAL_URI",
                "HTTP_X_VERCEL_PATH",
                "HTTP_X_MATCHED_PATH",
            ):
                val = environ.get(header_key, "")
                if val and val not in ("/api/index", "/api/index.py", "/api", "/404"):
                    clean = re.sub(r"^/+", "/", val.split("?")[0].strip())
                    environ["PATH_INFO"] = clean
                    break
            else:
                environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
