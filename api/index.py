import os
import sys
from pathlib import Path

# Ensure project root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import app


class VercelPathFix:
    """WSGI middleware ensuring correct PATH_INFO under Vercel serverless rewrites."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # When Vercel rewrites /downloader to /api/index, HTTP_X_MATCHED_PATH or
        # HTTP_X_FORWARDED_URI contains the actual client path (e.g. '/downloader').
        matched = environ.get("HTTP_X_MATCHED_PATH") or environ.get("HTTP_X_FORWARDED_URI")
        if matched:
            path = matched.split("?")[0].strip()
            if path and not path.startswith("/api/index"):
                if not path.startswith("/"):
                    path = "/" + path
                environ["PATH_INFO"] = path

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathFix(app.wsgi_app)
