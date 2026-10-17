import os
import sys
from pathlib import Path

# Ensure project root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import app


class VercelWSGIMiddleware:
    """WSGI Middleware for seamless Vercel serverless routing."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get("HTTP_X_MATCHED_PATH", "")
        current_path = environ.get("PATH_INFO", "")

        # When Vercel rewrites to /api/index, current_path is '/api/index'.
        # Resolve real path from HTTP_X_MATCHED_PATH if available, or fallback to '/'
        if current_path in ("/api/index", "/api/index.py", "/api"):
            if matched_path and matched_path not in ("/api/index", "/api/index.py", "/api", "/404"):
                clean = matched_path.split("?")[0].strip()
                if not clean.startswith("/"):
                    clean = "/" + clean
                environ["PATH_INFO"] = clean
            else:
                environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
