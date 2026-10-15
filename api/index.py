import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote

# Ensure project root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import app


class VercelPathMiddleware:
    """WSGI middleware ensuring correct PATH_INFO under Vercel serverless rewrites."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        target_path = None

        # 1. Primary: Extract original path from Vercel rewrite parameter (?__vercel_path__=...)
        if "__vercel_path__=" in query_string:
            qs = parse_qs(query_string)
            if "__vercel_path__" in qs and qs["__vercel_path__"]:
                target_path = unquote(qs["__vercel_path__"][0]).strip()

            # Clean __vercel_path__ out of QUERY_STRING so Flask request.args stays clean
            clean_params = [
                p for p in query_string.split("&")
                if not p.startswith("__vercel_path__=")
            ]
            environ["QUERY_STRING"] = "&".join(clean_params)

        # 2. Secondary fallback: Platform headers
        elif "HTTP_X_FORWARDED_PATH" in environ:
            target_path = environ["HTTP_X_FORWARDED_PATH"]
        elif "HTTP_X_MATCHED_PATH" in environ:
            matched = environ["HTTP_X_MATCHED_PATH"].strip()
            if matched and not matched.startswith("/api/index"):
                target_path = matched

        # 3. Tertiary fallback: If path is literally '/api/index' or '/api/index.py', default to root '/'
        current_path = environ.get("PATH_INFO", "")
        if not target_path and (current_path == "/api/index" or current_path == "/api/index.py" or current_path == "/api"):
            target_path = "/"

        # Apply target path if resolved
        if target_path:
            target_path = target_path.split("?")[0].strip()
            if not target_path.startswith("/"):
                target_path = "/" + target_path
            while "//" in target_path:
                target_path = target_path.replace("//", "/")
            environ["PATH_INFO"] = target_path

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
