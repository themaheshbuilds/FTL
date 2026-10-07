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
    client = request.args.get("client", "android")
    
    opts = YtDlpService.get_default_opts({
        "skip_download": True,
        "extractor_args": {
            "youtube": {
                "player_client": [client],
                "player_skip": ["webpage", "configs"]
            }
        }
    })
    
    res = {
        "url": url,
        "client": client,
        "node": shutil.which("node"),
        "cookies_present": bool(YtDlpService.get_cookie_file()),
        "env_vercel": bool(os.getenv("VERCEL"))
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            res["success"] = True
            res["title"] = info.get("title") if info else None
            res["formats_count"] = len(info.get("formats", [])) if info else 0
    except Exception as e:
        res["success"] = False
        res["error_type"] = type(e).__name__
        res["error_message"] = str(e)
        
    return jsonify(res), 200


