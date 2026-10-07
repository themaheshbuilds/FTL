from flask import Blueprint, jsonify, request
import os
import shutil
import sys
import yt_dlp
from services.ytdlp_service import YtDlpService

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint.
    
    Returns:
        JSON response with system status.
    """
    return jsonify({"status": "ok"}), 200


@health_bp.route("/api/debug_yt", methods=["GET"])
def debug_yt():
    url = request.args.get("url", "https://youtu.be/xvT1jH8B9AM")
    client = request.args.get("client", "service")
    
    extra = {
        "skip_download": True,
        "ignoreerrors": False,
    }
    if client:
        extra["extractor_args"] = {
            "youtube": {
                "player_client": [client],
                "player_skip": ["webpage", "configs"]
            }
        }
        
    use_cookies = request.args.get("cookies", "1") != "0"
    opts = YtDlpService.get_default_opts(extra)
    if not use_cookies:
        opts.pop("cookiefile", None)
        
    cookie_file = YtDlpService.get_cookie_file()
    cookies_count = 0
    if cookie_file and os.path.exists(cookie_file):
        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies_count = len([line for line in f if line.strip() and not line.startswith("#")])
        except Exception:
            pass
    
    res = {
        "url": url,
        "client": client or "default",
        "use_cookies": use_cookies,
        "node": shutil.which("node"),
        "cookies_present": bool(cookie_file),
        "cookies_count": cookies_count,
        "proxy_configured": len(YtDlpService.get_active_proxies()) > 0,
        "proxies_count": len(YtDlpService.get_active_proxies()),
        "env_vercel": bool(os.getenv("VERCEL"))
    }
    
    try:
        if client == "service":
            info, err = YtDlpService.extract_info(url)
            if not info:
                raise Exception(err or "Extraction failed via service")
        else:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        
        res["success"] = True
        res["info_keys"] = list(info.keys()) if info else []
        res["title"] = info.get("title") if info else None
        res["formats_count"] = len(info.get("formats", [])) if info else 0
    except Exception as e:
        res["success"] = False
        res["error_type"] = type(e).__name__
        res["error_message"] = str(e)
        
    return jsonify(res), 200


