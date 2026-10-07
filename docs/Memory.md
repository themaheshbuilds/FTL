# LinkForge - Development Memory

> This file is the definitive, persistent memory of LinkForge.
> Read this file first to obtain complete context of the application, architecture, APIs,
> engines, file manifests, and gotchas without needing to inspect multiple files repeatedly.

---

# 1. Current State & Repository Information

```text
Project: LinkForge
Tagline: One Link. Any File.
Type: Dual-Workflow Web Application (Link Downloader + Universal File Converter)
Language / Runtime: Python 3.11+
Framework: Flask 3.1+ (Application Factory pattern)
Frontend: Vanilla HTML5 / Modern CSS / Vanilla JavaScript (Single-Page Application)

GitHub Repository: https://github.com/themaheshbuilds/FTL.git
Active Git Branch: main
Deployment Target: Vercel (Serverless Python via vercel.json & api/index.py)

Current Phase: Phase 12 (Universal File Converter Suite) - COMPLETED
Test Suite Status: 45 passed, 0 failed, 0 skipped (Verified via pytest on 2026-10-07)
Next Priorities: Phase 15 (Production Deployment & Monitoring) + Phase 13 additions (rate-limiting)
```

---

# 2. Universal Rule for All New Projects

> [!IMPORTANT]
> **MANDATORY CONTEXT PACK FOR EVERY NEW PROJECT:**
> Whenever initiating or bootstrapping ANY new project in this workspace or future projects,
> you MUST immediately create the standard **7-file Documentation Context Pack** inside `docs/`:
> 1. `docs/PRD.md` — Product Requirements Document (Scope, features, APIs, compliance)
> 2. `docs/Structure.md` — Complete directory hierarchy, component roles, data flow diagrams
> 3. `docs/Rules.md` — Engineering rules, security constraints, and coding standards
> 4. `docs/Phases.md` — Phased development roadmap with explicit completion milestones
> 5. `docs/Design.md` — UI/UX design specifications, tokens, components, and all screen states
> 6. `docs/Memory.md` — Persistent architectural memory, technology decisions, and technical gotchas
> 7. `docs/DeveloperContext.md` — AI agent operating guide, source-of-truth priority, Definition of Done

---

# 3. Dual-Workflow Architecture

LinkForge operates two decoupled workflows that share common delivery infrastructure:

```text
                    LINKFORGE PLATFORM
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
      LINK WORKFLOW                     FILE WORKFLOW
    (Public Link Media)              (Local Format Shift)
            │                                 │
       URL Analyzer                      Tool Catalog
            │                         (Categories & Formats)
     Platform Detector                        │
            │                          File Upload &
        Extractors                   Staging Workspace
            │                                 │
      Media Objects                   Converter Engine
            │                                 │
     Media Packaging                     Converted File
    (PDF / ZIP / Audio)                       │
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
                    SHARED INFRASTRUCTURE
                     • Job Manager & UUIDs
                     • Filename Sanitization
                     • Isolated Storage Sandboxes
                     • 30-Min Auto-Cleanup
                     • Writable /tmp Fallback for Vercel
                             │
                             ▼
                    GET /download/<file_id>
```

### Architectural Axiom
- **LINK EXTRACTION != FILE CONVERSION:** Extraction logic handles network requests, SSRF defenses, and platform scrapers. Conversion handles local file format transformations. Keep them decoupled.

---

# 4. Complete Project File Manifest & Function Map

Use this directory and file manifest to instantly understand the purpose of each file:

### Core Configuration & Serverless Entrypoints
- [`app.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/app.py): Application factory `create_app()`, registers blueprints, defines global 404/500 JSON error handlers, exports `app = create_app()`.
- [`config.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/config.py): Environment-based configurations (`DevelopmentConfig`, `TestingConfig`, `ProductionConfig`). Detects serverless runtimes (`VERCEL=1`) and routes storage to `/tmp/linkforge/` with automatic fallback if base directory is read-only.
- [`api/index.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/api/index.py): Vercel serverless function entrypoint that puts project root on `sys.path` and imports `app`.
- [`vercel.json`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/vercel.json): Vercel routing rules rewriting `/(.*)` to `/api/index`.
- [`requirements.txt`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/requirements.txt): Pinned dependencies (`Flask`, `Werkzeug`, `requests`, `httpx`, `Pillow`, `reportlab`, `yt-dlp`, `imageio-ffmpeg`, `python-dotenv`, `python-docx`, `PyMuPDF`, `pytest`).
- [`.gitignore`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/.gitignore): Ignores `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.vercel`, `storage/temp/*`, `storage/generated/*`, `storage/test_*`.

### Routes (`routes/`)
- [`routes/__init__.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/routes/__init__.py): Blueprint export hub.
- [`routes/web.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/routes/web.py): `GET /` — Renders `templates/index.html`.
- [`routes/health.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/routes/health.py): `GET /health` — Health check returning `{"status": "ok"}`.
- [`routes/api.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/routes/api.py):
  - `POST /api/analyze` — Accepts JSON `{"url": "..."}`, validates URL, detects platform, returns metadata and format choices.
  - `POST /api/generate` — Accepts JSON `{"url": "...", "output_format": "...", "custom_filename": "...", "with_caption": bool}`, executes media packaging.
- [`routes/converter.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/routes/converter.py):
  - `POST /api/convert` — Accepts `multipart/form-data` with `files`, `conversion_type`, `output_format`, `custom_filename`. Stages files, calls `ConverterService`, registers job, cleans staging dir.
- [`routes/download.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/routes/download.py):
  - `GET /download/<file_id>` — Streams the generated file with `Content-Disposition: attachment; filename="<sanitized_name>"` and checks expiration.

### Services (`services/`)
- [`services/url_analyzer.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/url_analyzer.py): Validates URL scheme, executes SSRF checks, normalizes tracking params, dispatches to platform detector.
- [`services/platform_detector.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/platform_detector.py): Matches hostname and regexes to classify platform (Instagram, LinkedIn, YouTube, TikTok, Reddit, X, Facebook, Generic).
- [`services/extraction_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/extraction_service.py): Routes URLs to appropriate platform extractor class.
- [`services/converter_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/converter_service.py): Complete conversion engine:
  - `pdf_to_images`: PyMuPDF rasterization at 150 DPI (single image or multi-page ZIP).
  - `images_to_pdf`: Pillow & ReportLab multi-page compilation via `PdfService`.
  - `docx_to_pdf`: Microsoft Word COM automation (`win32com.client`) on Windows with fallback ReportLab converter.
  - `pdf_to_docx`: PyMuPDF text & embedded image extraction into `python-docx`.
  - `video_to_audio`: FFmpeg audio stream extraction to MP3 (192 kbps) or M4A (AAC).
  - `video_converter`: FFmpeg container remuxing/transcoding to MP4, MKV, WebM.
  - `image_converter`: Pillow format conversion between JPG, PNG, WebP.
- [`services/media_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/media_service.py): High-level media packaging coordinator for Link Downloader (generates PDFs, ZIPs, DOCX, video streams).
- [`services/pdf_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/pdf_service.py): Compiles image lists into multi-page PDFs with automatic aspect ratio scaling and optional caption page insertion.
- [`services/archive_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/archive_service.py): Creates sanitized ZIP archives from lists of files or image URLs.
- [`services/docx_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/docx_service.py): Converts image carousels into Word documents (`.docx`).
- [`services/generic_downloader.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/generic_downloader.py): Streamed direct HTTP downloader and OpenGraph HTML parser.
- [`services/ytdlp_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/ytdlp_service.py): Subprocess/library wrapper for `yt-dlp` metadata extraction and video downloading.
- [`services/job_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/job_service.py): Job lifecycle coordinator (`queued`, `completed`, `failed`, `expired`), allocates `storage/temp/<id>` and `storage/generated/<id>`.
- [`services/cleanup_service.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/services/cleanup_service.py): Background and on-demand garbage collector purging files older than 30 minutes.

### Extractors (`extractors/`)
- [`extractors/base.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/base.py): Base class requiring `can_handle(url)`, `analyze(url)`, and `extract(url)`.
- [`extractors/instagram.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/instagram.py): Extracts posts, multi-photo carousels, reels, and video direct streams.
- [`extractors/linkedin.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/linkedin.py): Extracts documents (multi-page PDF slides up to 50+ pages), videos (via `<video data-sources="...">` and `og:video`), shortlinks (`lnkd.in`), and single images.
- [`extractors/youtube.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/youtube.py): YouTube video, shorts, and audio stream extraction via `ytdlp_service`.
- [`extractors/twitter.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/twitter.py): X / Twitter videos and image galleries.
- [`extractors/reddit.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/reddit.py): Reddit video (including separate audio/video stream muxing) and image galleries.
- [`extractors/facebook.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/facebook.py): Public Facebook posts and reels.
- [`extractors/generic.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/extractors/generic.py): OpenGraph media fallback for generic websites and direct URLs.

### Utilities (`utils/`)
- [`utils/security.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/utils/security.py): SSRF protection (`is_safe_url`) blocking private IPs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.1`), cloud metadata (`169.254.169.254`), and non-HTTP schemes.
- [`utils/filenames.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/utils/filenames.py): `sanitize_filename` (strips `..`, illegal characters, and normalizes file extensions).
- [`utils/ffmpeg_helper.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/utils/ffmpeg_helper.py): Locates FFmpeg binary (`imageio-ffmpeg`), executes audio extraction (`-vn -b:a 192k`) and container remuxing (`-c copy`) safely without `shell=True`.
- [`utils/mime.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/utils/mime.py): Content-Type parsing and bidirectional MIME-to-extension resolution.
- [`utils/logging.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/utils/logging.py): Structured JSON logging with automatic scrubbing of cookies, auth tokens, and sensitive query params.
- [`utils/validation.py`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/utils/validation.py): Payload verification helper.

### Frontend (`templates/` & `static/`)
- [`templates/index.html`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/templates/index.html): Single-Page Application HTML with header mode switch (`#tab-downloader` and `#tab-converter`), Downloader view, Converter view, tool catalog, drag-and-drop workspace, staged file chips, format dropdown, and result cards.
- [`static/css/style.css`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/static/css/style.css): Design system tokens, color variables, typography (`Plus Jakarta Sans`), reset.
- [`static/css/components.css`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/static/css/components.css): Mode tabs, tool cards grid, drag-and-drop dropzone, file chips, responsive layouts.
- [`static/js/app.js`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/static/js/app.js): Core app controller, input clear/paste listeners, modal dialogues.
- [`static/js/analyzer.js`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/static/js/analyzer.js): Downloader form submit, loading animation, dynamic format button generation, generate request dispatch.
- [`static/js/converter.js`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/static/js/converter.js): Converter tool catalog, category filter pills, drag-and-drop file staging, chips, format selection, FormData upload to `/api/convert`.
- [`static/js/downloader.js`](file:///c:/Users/vilas/Desktop/Link%20to%20File%20Downloader/static/js/downloader.js): Polling and download trigger helper.

---

# 5. Converter Engines & Capabilities Matrix

| Conversion Type | Source Formats | Target Format | Engine | Technical Implementation |
| :--- | :--- | :--- | :--- | :--- |
| `pdf_to_images` | `.pdf` | `jpg`, `png` | PyMuPDF (`fitz`) | Renders pages at 150 DPI. If 1 page: outputs image file; if >1 page: outputs zip archive containing `page_01.jpg`, etc. |
| `images_to_pdf` | `.jpg`, `.png`, `.webp`, `.bmp` | `pdf` | ReportLab + Pillow | Scales image dimensions proportionally, compiles into multi-page PDF document. |
| `docx_to_pdf` | `.docx`, `.doc` | `pdf` | Word COM / ReportLab | Windows: MS Word COM automation (`win32com.client.DispatchEx("Word.Application")`). Non-Windows fallback: ReportLab paragraph parser. |
| `pdf_to_docx` | `.pdf` | `docx` | PyMuPDF + python-docx | Extracts text blocks with formatting and embedded raster images into Word document. |
| `video_to_audio` | `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi` | `mp3`, `m4a` | FFmpeg (`imageio-ffmpeg`) | MP3: `-vn -c:a libmp3lame -b:a 192k`. M4A: `-vn -c:a aac -b:a 192k`. |
| `video_converter` | `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi` | `mp4`, `mkv`, `webm` | FFmpeg (`imageio-ffmpeg`) | Video container remuxing/transcoding using list arguments without shell invocation. |
| `image_converter`| `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp` | `png`, `jpg`, `webp` | Pillow (`PIL.Image`) | Format transcode, converts RGBA to RGB for JPEG target. |

---

# 6. Important Technical Gotchas & Implementation Lessons

1. **Windows COM Automation (`win32com.client`):**
   - When converting Word DOCX to PDF, Word spawns an out-of-process COM server.
   - You MUST call `pythoncom.CoInitialize()` at start and `pythoncom.CoUninitialize()` in a `finally` block.
   - You MUST explicitly call `wdoc.Close(False)`, `word.Quit()`, and `del wdoc`, `del word` in `finally` before `CoUninitialize()`. Failing to delete COM pointers before quitting causes `Windows fatal exception: code 0x800706ba` (RPC server unavailable).
2. **LinkedIn Multi-Page Document Posts:**
   - LinkedIn embeds documents as carousel slides with image URLs containing page indices (`data-li-page-url`, `page-url`, `manifest`).
   - If only parsing the primary container, only page 1 is returned. The extractor parses all image manifestations and falls back to regex matching page URLs to ensure all 20+ pages are captured.
3. **LinkedIn Videos:**
   - LinkedIn video posts render with `<video data-sources="...">` containing JSON-encoded video streams, or OpenGraph `og:video`.
   - The extractor checks for video data sources first before falling back to poster images.
4. **Reddit Video Audio Separation:**
   - Reddit hosts video and audio in separate DASH streams. Downloading only the video results in a muted file.
   - `reddit.py` and `ytdlp_service` detect audio streams and remux them via FFmpeg.
5. **Vercel Serverless Read-Only Filesystem:**
   - In AWS Lambda / Vercel Serverless, the project root is strictly read-only.
   - `config.py` detects `VERCEL=1` and sets `TEMP_STORAGE_DIR` and `GENERATED_STORAGE_DIR` to `/tmp/linkforge/temp` and `/tmp/linkforge/generated`, with automatic fallback on `OSError: [Errno 30] Read-only file system`.

---

# 7. Complete API Reference

### 1. `POST /api/analyze`
- **Request:** `{"url": "https://..."}`
- **Response (200):**
  ```json
  {
    "success": true,
    "platform": "Instagram",
    "content_type": "image_collection",
    "media_count": 8,
    "has_caption": true,
    "caption": "Post text description...",
    "formats": ["pdf", "zip", "images"]
  }
  ```

### 2. `POST /api/generate`
- **Request:**
  ```json
  {
    "url": "https://...",
    "output_format": "pdf",
    "quality": "best",
    "custom_filename": "my_download",
    "with_caption": false
  }
  ```
- **Response (200):**
  ```json
  {
    "success": true,
    "file_id": "a1b2c3d4e5f6",
    "filename": "my_download.pdf",
    "filesize": 4823910,
    "size_formatted": "4.60 MB"
  }
  ```

### 3. `POST /api/convert`
- **Request:** `multipart/form-data`
  - `files`: File payload (single or multiple)
  - `conversion_type`: `pdf_to_images` | `images_to_pdf` | `docx_to_pdf` | `pdf_to_docx` | `video_to_audio` | `video_converter` | `image_converter`
  - `output_format`: `jpg` | `png` | `pdf` | `docx` | `mp3` | `m4a` | `mp4` | `mkv` | `webm` | `webp`
  - `custom_filename`: Optional string
- **Response (200):**
  ```json
  {
    "success": true,
    "file_id": "f6e5d4c3b2a1",
    "filename": "my_converted_file.pdf",
    "filesize": 128450,
    "mime_type": "application/pdf",
    "size_formatted": "125.4 KB"
  }
  ```

### 4. `GET /download/<file_id>`
- **Response:** File binary stream with sanitized attachment filename header. 404 if expired or not found.

### 5. `GET /health`
- **Response (200):** `{"status": "ok"}`

---

# 8. Test Suite Verification

Run all tests via:
```bash
pytest -v
```
**Current Verified Result:**
```text
============================= 45 passed in 9.31s =============================
- tests/test_analyzer.py (3/3)
- tests/test_api.py (6/6)
- tests/test_converter.py (7/7)
- tests/test_filenames.py (4/4)
- tests/test_frontend.py (3/3)
- tests/test_health.py (2/2)
- tests/test_instagram_extractor.py (4/4)
- tests/test_linkedin_extractor.py (7/7)
- tests/test_packaging.py (5/5)
- tests/test_security.py (4/4)
```
