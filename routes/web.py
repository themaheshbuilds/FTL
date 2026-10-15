from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.route("/", methods=["GET"])
@web_bp.route("/index", methods=["GET"])
@web_bp.route("/api/index", methods=["GET"])
@web_bp.route("/api/index.py", methods=["GET"])
def index():
    """Render LinkForge main interface."""
    return render_template("index.html")


@web_bp.route("/converter", methods=["GET"])
def converter():
    """Render LinkForge converter interface."""
    return render_template("converter.html")


