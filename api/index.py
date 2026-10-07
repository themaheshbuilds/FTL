import os
import sys
import traceback
from pathlib import Path

# Ensure project root directory is on Python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from app import app
except Exception as e:
    import logging
    from flask import Flask, jsonify

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("linkforge.bootstrap_error")
    logger.error("Failed to bootstrap LinkForge app: %s\n%s", e, traceback.format_exc())

    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return jsonify({
            "success": False,
            "error": {
                "code": "BOOTSTRAP_ERROR",
                "message": f"LinkForge serverless initialization error: {str(e)}",
                "traceback": traceback.format_exc()
            }
        }), 500

