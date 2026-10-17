from flask import Blueprint, render_template, abort

web_bp = Blueprint("web", __name__)

CONVERTER_TOOLS = {
    "pdf-to-images": {
        "id": "pdf_to_images",
        "slug": "pdf-to-images",
        "title": "PDF to Images",
        "badge": "PDF → JPG / PNG",
        "icon": "📄",
        "desc": "Extract every page of any PDF into high-resolution JPG or PNG images inside a ZIP archive.",
        "accept": ".pdf",
        "multiple": False,
        "formats": [
            {"value": "jpg", "label": "JPG Images in ZIP (.zip)"},
            {"value": "png", "label": "PNG Images in ZIP (.zip)"}
        ]
    },
    "images-to-pdf": {
        "id": "images_to_pdf",
        "slug": "images-to-pdf",
        "title": "Images to PDF",
        "badge": "Images → PDF",
        "icon": "🖼️",
        "desc": "Combine multiple JPG, PNG, or WebP images into a single clean, high-resolution PDF document.",
        "accept": ".jpg,.jpeg,.png,.webp,.bmp",
        "multiple": True,
        "formats": [
            {"value": "pdf", "label": "PDF Document (.pdf)"}
        ]
    },
    "video-to-audio": {
        "id": "video_to_audio",
        "slug": "video-to-audio",
        "title": "Video to Audio",
        "badge": "Video → MP3 / M4A",
        "icon": "🎧",
        "desc": "Extract high-bitrate crystal clear audio track from any MP4, MKV, WebM, MOV, or AVI video.",
        "accept": ".mp4,.mkv,.webm,.mov,.avi,.flv",
        "multiple": False,
        "formats": [
            {"value": "mp3", "label": "MP3 Audio (192 kbps)"},
            {"value": "m4a", "label": "M4A Audio (AAC)"}
        ]
    },
    "docx-to-pdf": {
        "id": "docx_to_pdf",
        "slug": "docx-to-pdf",
        "title": "Word (DOCX) to PDF",
        "badge": "DOCX → PDF",
        "icon": "📝",
        "desc": "Convert Microsoft Word documents (.docx) to PDF with crisp layout and typography.",
        "accept": ".docx,.doc",
        "multiple": False,
        "formats": [
            {"value": "pdf", "label": "PDF Document (.pdf)"}
        ]
    },
    "pdf-to-docx": {
        "id": "pdf_to_docx",
        "slug": "pdf-to-docx",
        "title": "PDF to Word (DOCX)",
        "badge": "PDF → DOCX",
        "icon": "📑",
        "desc": "Extract text, layout, and embedded images from PDF into an editable Microsoft Word document.",
        "accept": ".pdf",
        "multiple": False,
        "formats": [
            {"value": "docx", "label": "Word Document (.docx)"}
        ]
    },
    "video-converter": {
        "id": "video_converter",
        "slug": "video-converter",
        "title": "Video Transcoder",
        "badge": "Video → MP4 / MKV / WebM",
        "icon": "🎬",
        "desc": "Transcode video files across MP4, MKV, and WebM container formats with high efficiency.",
        "accept": ".mp4,.mkv,.webm,.mov,.avi,.flv",
        "multiple": False,
        "formats": [
            {"value": "mp4", "label": "MP4 Video (H.264)"},
            {"value": "mkv", "label": "MKV Video (Lossless)"},
            {"value": "webm", "label": "WebM Video"}
        ]
    },
    "image-converter": {
        "id": "image_converter",
        "slug": "image-converter",
        "title": "Image Converter",
        "badge": "PNG / JPG → WebP",
        "icon": "🎨",
        "desc": "Convert and optimize images between PNG, JPG, and ultra-compressed WebP format.",
        "accept": ".png,.jpg,.jpeg,.webp,.bmp",
        "multiple": False,
        "formats": [
            {"value": "webp", "label": "WebP (Ultra Compressed)"},
            {"value": "png", "label": "PNG (Lossless)"},
            {"value": "jpg", "label": "JPG (Standard)"}
        ]
    }
}


@web_bp.route("/", methods=["GET"], strict_slashes=False)
@web_bp.route("/index", methods=["GET"], strict_slashes=False)
@web_bp.route("/index.html", methods=["GET"], strict_slashes=False)
@web_bp.route("/home", methods=["GET"], strict_slashes=False)
def index():
    """Render LinkForge Home Page."""
    return render_template("index.html", tools=CONVERTER_TOOLS)


@web_bp.route("/downloader", methods=["GET"], strict_slashes=False)
@web_bp.route("/downloader.html", methods=["GET"], strict_slashes=False)
@web_bp.route("/download", methods=["GET"], strict_slashes=False)
@web_bp.route("/link-downloader", methods=["GET"], strict_slashes=False)
@web_bp.route("/link-downloader.html", methods=["GET"], strict_slashes=False)
@web_bp.route("/quick-downloader", methods=["GET"], strict_slashes=False)
def downloader():
    """Render dedicated Link Downloader page."""
    return render_template("downloader.html")


@web_bp.route("/converter", methods=["GET"], strict_slashes=False)
@web_bp.route("/converter.html", methods=["GET"], strict_slashes=False)
@web_bp.route("/converters", methods=["GET"], strict_slashes=False)
@web_bp.route("/convert", methods=["GET"], strict_slashes=False)
@web_bp.route("/files", methods=["GET"], strict_slashes=False)
@web_bp.route("/file", methods=["GET"], strict_slashes=False)
@web_bp.route("/file-converter", methods=["GET"], strict_slashes=False)
@web_bp.route("/file-converters", methods=["GET"], strict_slashes=False)
@web_bp.route("/tools", methods=["GET"], strict_slashes=False)
def converter():
    """Render Universal File Converter Hub."""
    return render_template("converter.html", tools=CONVERTER_TOOLS)


@web_bp.route("/converter/<tool_slug>", methods=["GET"], strict_slashes=False)
@web_bp.route("/tool/<tool_slug>", methods=["GET"], strict_slashes=False)
@web_bp.route("/tools/<tool_slug>", methods=["GET"], strict_slashes=False)
@web_bp.route("/files/<tool_slug>", methods=["GET"], strict_slashes=False)
@web_bp.route("/file/<tool_slug>", methods=["GET"], strict_slashes=False)
def converter_tool(tool_slug):
    """Render dedicated page for a specific conversion tool."""
    tool = CONVERTER_TOOLS.get(tool_slug)
    if not tool:
        abort(404)
    other_tools = [t for s, t in CONVERTER_TOOLS.items() if s != tool_slug]
    return render_template("tool_converter.html", tool=tool, other_tools=other_tools)


@web_bp.route("/favicon.ico", methods=["GET"])
def favicon():
    return ("", 204)


@web_bp.route("/sw.js", methods=["GET"])
def service_worker():
    script = (
        "self.addEventListener('install', () => self.skipWaiting());\n"
        "self.addEventListener('activate', (e) => {\n"
        "  self.registration.unregister().then(() => {\n"
        "    return self.clients.matchAll();\n"
        "  }).then(clients => {\n"
        "    clients.forEach(c => c.navigate(c.url));\n"
        "  });\n"
        "});\n"
    )
    from flask import Response
    res = Response(script, mimetype="application/javascript")
    res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return res

