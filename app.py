import os
from pathlib import Path
from flask import Flask, jsonify
from config import get_config, Config
from routes.health import health_bp
from routes.web import web_bp
from routes.api import api_bp
from routes.download import download_bp
from routes.converter import converter_bp
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

    # Application-wide error handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found."
            }
        }), 404

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

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
