from routes.health import health_bp
from routes.web import web_bp
from routes.api import api_bp
from routes.download import download_bp
from routes.converter import converter_bp

__all__ = ["health_bp", "web_bp", "api_bp", "download_bp", "converter_bp"]
