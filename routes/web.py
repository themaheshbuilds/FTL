from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.route("/", methods=["GET"])
def index():
    """Render LinkForge main interface."""
    return render_template("index.html")
