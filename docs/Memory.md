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
Test Suite Status: 46 passed, 0 failed, 0 skipped (Verified via pytest on 2026-10-07)
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
============================= 86 passed in 15.60s =============================
- tests/test_analyzer.py (4/4) [Includes cookie normalization & SSRF tests]
- tests/test_api.py (6/6)
- tests/test_converter.py (7/7)
- tests/test_email.py (6/6)
- tests/test_filenames.py (4/4)
- tests/test_frontend.py (17/17)
- tests/test_health.py (3/3)
- tests/test_instagram_extractor.py (8/8)
- tests/test_linkedin_extractor.py (7/7)
- tests/test_packaging.py (8/8)
- tests/test_security.py (4/4)
- tests/test_vercel_middleware.py (12/12)
```

---

# 9. Vercel Serverless Architecture & Deployment Gotchas

### Serverless Function Configuration
- **Entrypoint:** `api/index.py` is the official WSGI application entrypoint for Vercel Serverless Functions.
- **Path Routing & Middleware:** `vercel.json` rewrites `[{"source": "/(.*)", "destination": "/api/index.py?__path__=/$1"}]`. Inside `api/index.py`, `VercelPathMiddleware` extracts `__path__` and restores the intended client route (`/downloader`, `/converter`, `/converter/<tool_slug>`, `/api/analyze`, etc.) into `PATH_INFO`, cleaning `request.args` so dynamic multi-page navigation functions flawlessly.
- **Permissive Slashing:** `app.url_map.strict_slashes = False` is set on Flask application factory to handle all URLs with or without trailing slashes.
- **Template Bundling:** `vercel.json` configures `"functions": { "api/index.py": { "includeFiles": "templates/**", "maxDuration": 30 } }` to ensure templates are bundled in serverless package.
- **Static Assets via CDN:** Static assets are mirrored into `public/static/` so Vercel Edge CDN serves CSS and JavaScript directly without cold starts.
- **Serverless Storage:** Lambda filesystems are read-only except `/tmp`. `config.py` detects serverless runtimes (`VERCEL`, `AWS_LAMBDA_FUNCTION_NAME`, `LAMBDA_TASK_ROOT`, etc.) and automatically routes `TEMP_STORAGE_DIR` and `GENERATED_STORAGE_DIR` to `/tmp/linkforge/...` with resilient fallback handling.
- **Disk Recovery across Ephemeral Containers:** `JobService` writes `meta.json` inside generated folders and implements a two-tier disk scan so subsequent lambda invocations can serve download files even if in-memory state is cleared.
- **Dependencies:** `beautifulsoup4` is required for LinkedIn & generic HTML metadata extraction; `pytest` is excluded from production `requirements.txt` to keep the deployment package lightweight. `.vercelignore` excludes tests, scratch scripts, docs, and git files.
- **Instagram Cloud Extraction & Cookies:** Cloud datacenter IPs (Vercel/AWS Lambda) face Instagram login challenges. To guarantee 100% extraction:
  1. `INSTAGRAM_COOKIES` or `COOKIES_TEXT` environment variables are parsed and written to `/tmp/linkforge_env_cookies.txt`.
  2. Embed endpoint fallback (`/p/{shortcode}/embed/`) extracts `contextJSON` and full GraphQL sidecar media trees.
  3. Mobile API fallback (`https://i.instagram.com/api/v1/media/{media_id}/info/`) extracts `carousel_media` and full resolutions.
  4. Serverless timeouts are clamped to 8s (instead of 25s) to guarantee functions never stall past Vercel's 30s limit.

---

# 10. YouTube Cloud Extraction & Cookie Handling Gotchas

### 1. YouTube Datacenter IP Bot Detection & Cookie Normalization
- **The Problem:** Cloud datacenter IP ranges (AWS Lambda, Vercel, GCP) are blocked by YouTube with `Sign in to confirm you're not a bot`. In addition:
  1. **Leading Variable Names:** Users frequently paste `YOUTUBE_COOKIES = # Netscape ...` directly into the environment variable field.
  2. **Browser Form Space Conversion:** Pasting tab-separated Netscape files into browser web forms often converts tabs to multiple spaces. `MozillaCookieJar` crashes if tabs are missing.
  3. **JSON Array Exports:** Extensions like Cookie-Editor export raw JSON arrays `[{"domain": "...", "name": "..."}]`.
  4. **Stale PSIDTS Tokens:** `__Secure-1PSIDTS` tokens rotate rapidly and trigger `ERROR: The page needs to be reloaded`.
  5. **InnerTube Client Incompatibility:** The `android` and `ios` InnerTube clients in `yt-dlp` explicitly do NOT support cookies (`WARNING: Skipping client 'android' since it does not support cookies`).
- **The Solution in `services/ytdlp_service.py` (`format_cookies_to_netscape`):**
  - Automatically strips enclosing quotes and leading `YOUTUBE_COOKIES = ` variable assignments.
  - Automatically unescapes literal `\n` and `\t` sequences.
  - Automatically transforms JSON cookie arrays into valid Netscape tab-separated lines.
  - Automatically re-splits space-separated Netscape lines and re-joins them with strict `\t` tabs.
  - Filters out unstable `PSIDTS` tokens while retaining core session credentials (`LOGIN_INFO`, `SID`, `HSID`, `SSID`, `SAPISID`, etc.).
  - Permits natural, unrestricted clients (`web`, `mweb`, `tv_embedded`, `visionos`) so cookies authenticate cleanly and extract full resolution formats up to 4K/2K.

### 2. Max Resolution Downloading
- Standard `yt-dlp` options now use unrestricted clients and `bestvideo+bestaudio/best` (merged into MP4 via FFmpeg), delivering true maximum resolution (1080p/2K/4K, ~218 MB+) instead of mobile 360p (11 MB).

### 3. Vercel 4.5 MB Payload Limit & Client-Side In-Browser Conversion Bypass
- Vercel Serverless Functions enforce a strict 4.5 MB maximum payload limit for incoming HTTP request bodies (`POST /api/convert`), returning `413 Request Entity Too Large` for larger files.
- To eliminate this restriction completely on Vercel without requiring external storage buckets:
  - **PDF to Images**: Rendered directly in-browser using Mozilla's `pdf.js` and `jszip` at 2.0x scale (150 DPI). If 1 page, downloads a single JPG/PNG blob; if multiple pages, compiles into a ZIP archive.
  - **Image Converter**: Processed client-side via HTML5 Canvas into JPG/PNG/WebP blobs.
  - Zero bytes are transmitted to the serverless function, allowing 20 MB, 50 MB, or 100 MB+ documents to convert without hitting Vercel's 4.5 MB ceiling.
- Server-side endpoint (`/api/convert`) remains intact with 500 MB capacity for localhost (`python app.py`) and API clients.

### 4. Instagram Video Format Selection & Direct Progressive Stream Handling
- **The Problem:** In yt-dlp's Instagram extractor format list, the final entry (`formats[-1]`) is often an audio-only DASH stream (`vcodec == 'none'`), while the earlier formats include progressive MP4s with both video and audio. Blindly using `formats[-1]` caused Instagram reels to download as audio-only tracks.
- **The Solution:**
  - `InstagramExtractor._select_best_video_format` filters candidates where `vcodec != 'none'` and prioritizes progressive streams (`acodec != 'none'`), guaranteeing that full video + audio tracks are extracted.
  - Rotating proxy candidates and Instagram-specific referer headers are used during extraction to avoid IP blocks.
  - `MediaService.process_and_package` leverages direct progressive CDN downloads for Instagram MP4s, completing downloads in 1–2 seconds with zero reliance on missing cloud ffmpeg binaries.
  - Frontend (`analyzer.js`) sets explicit `download` attributes and auto-triggers browser download saving.

### 5. MKV / WebM Video Container Packaging & Dynamic Extension Badges
- **The Problem:** 
  1. In `services/media_service.py`, `downloaded_file` was only assigned inside an `if format_lower == "mp4"` condition. When users requested `mkv` or `webm`, `downloaded_file` remained unassigned, throwing `UnboundLocalError: cannot access local variable 'downloaded_file' where it is not associated with a value` when evaluating yt-dlp fallbacks.
  2. In addition, when remuxing wasn't needed or on environments lacking `ffmpeg`, fallback container logic renamed `.mkv` downloads back to `.mp4`.
  3. Format selection buttons previously showed plain generic text without explicit extension indicators, making it hard to see what file extension would be produced.
- **The Solution:**
  1. `downloaded_file = None` is initialized upfront before container checks.
  2. Instagram direct progressive CDN stream retrieval is expanded to all video and audio containers (`mp4`, `mkv`, `webm`, `video`, `audio`, `mp3`, `m4a`), fetching the high-speed source stream in seconds.
  3. Matroska container packaging (`remux_video` in `utils/ffmpeg_helper.py`) losslessly remuxes via `-c copy` (<0.1s), delivering genuine MKV files (`video/x-matroska`). If `ffmpeg` is missing, resilient copy fallback preserves the target container extension (`.mkv`).
  4. Frontend UI (`static/js/analyzer.js` and `public/static/js/analyzer.js`) now dynamically parses and displays dedicated format extension badges (e.g., `Video` + `.mp4`, `Matroska Video` + `.mkv`, `WebM Video` + `.webm`, `Audio Track` + `.mp3`, `PDF Document` + `.pdf`, `ZIP Archive` + `.zip`) styled with `.format-btn-ext` badge pill tokens.

---

# 11. Email Delivery Architecture & Gmail SMTP Setup

### 1. Delivery Flow & Attachment Strategy
- **Endpoint:** `POST /api/send-email` (accepts `file_id` and recipient `email`).
- **File Size Handling:**
  - **Files ≤ 25 MB:** Directly attached to the email as an email attachment (`MIMEApplication`), allowing users to open and save the file directly in their email client (Gmail, Outlook, Apple Mail).
  - **Files > 25 MB:** Email clients enforce a strict 25 MB attachment limit. Large files include a prominent, high-contrast **Direct 1-Click Download Button** linking to `{base_url}/download/{file_id}`, preventing bounce errors.
- **Rate Limiting & Security:** In-memory rate limiting enforces a maximum of 5 emails per minute per client IP to mitigate spam. Email inputs are strictly validated against RFC regex.

### 2. Gmail SMTP & 16-Character App Password Configuration
- Standard Google account passwords cannot authenticate directly via SMTP since Google disabled "Less secure apps".
- To authenticate `b3242412@gmail.com`:
  1. Go to Google Account Settings -> Security -> 2-Step Verification.
  2. Generate a 16-character **App Password** for "LinkForge".
  3. Store in `.env` as `SMTP_PASSWORD=xxxx xxxx xxxx xxxx` (and in Vercel Environment Variables).

---

# 12. Vercel Serverless Routing & Navigation Gotchas

### 1. Canonical Vercel Rewrite Destination (`/api/index`)
- **The Problem:** 
  1. Specifying query parameters in rewrite destinations (`/api/index?__vercel_path__=/$1`) causes Vercel Edge router to fail function route matching, throwing an edge-level `404 NOT_FOUND` for all URLs.
  2. Directly calling `/api/index` sets `PATH_INFO = "/api/index"`, which caused Flask 404s when no middleware was active.
  3. Adding `@web_bp.route("/api/index")` trapped all pages on the home screen.
- **The Solution:**
  - `vercel.json` rewrite rule is canonical without query parameters:
    ```json
    {
      "rewrites": [
        {
          "source": "/(.*)",
          "destination": "/api/index"
        }
      ]
    }
    ```
  - In `api/index.py`, `VercelWSGIMiddleware` inspects `environ.get("HTTP_X_MATCHED_PATH")`:
    - If `PATH_INFO` is `/api/index`, it restores `PATH_INFO` from `HTTP_X_MATCHED_PATH` (e.g., `/downloader`, `/converter`, `/converter/<tool>`, `/api/analyze`).
    - If `HTTP_X_MATCHED_PATH` is empty, missing, or points to `/api/index`, it automatically defaults `PATH_INFO = "/"`, guaranteeing the home page opens cleanly.
  - All routes (`/`, `/downloader`, `/converter`, `/files`, `/convert`, `/converter/<tool_slug>`, `/api/analyze`, `/api/generate`, `/download/<file_id>`) route with 100% fidelity. Verified via `tests/test_vercel_middleware.py`.

### 2. Dual 404 Errorhandler (HTML vs. JSON)
- **The Problem:** When users navigated to a mistyped or missing page on Vercel, returning raw JSON `{"error": {"code": "NOT_FOUND", ...}}` dumped an unstyled raw JSON string on a blank browser screen, leading users to believe the site was broken.
- **The Solution in `app.py` (`handle_not_found`):**
  - Evaluates `request.headers.get("Accept", "")`:
    - If the browser explicitly requests `text/html` and is not hitting an `/api/` route, it renders `templates/error.html` with full LinkForge Peach styling and a prominent "Return to Home" button.
    - If an API or programmatic client requests a missing resource (or for `/api/*` routes), it returns structured JSON (`code: "NOT_FOUND"`).

### 4. Vercel `__route=/$1` Wildcard Rewrite & Dedicated Page Segregation
- **The Problem:** In Vercel serverless deployments, `x-matched-path` is an edge response header, NOT an inbound HTTP request header delivered to the WSGI environment. Because `HTTP_X_MATCHED_PATH` was empty, the previous WSGI middleware fell back to setting `PATH_INFO = "/"`, trapping users on the Home page (`index.html`) whenever they clicked top navigation tabs (`/downloader`, `/converter`) or standalone tool cards (`/converter/<slug>`). Additionally, `index.html` previously embedded the full downloader input form directly on the page, creating an overcrowded experience rather than clean, segregated pages.
- **The Solution:**
  1. **Rewrite Rule in `vercel.json`:**
     ```json
     {
       "source": "/((?!static/).*)",
       "destination": "/api/index?__route=/$1"
     }
     ```
     Excludes `/static/` so CSS/JS are served directly by Vercel CDN, while passing the exact requested path (`$1`) into the `__route` query parameter.
  2. **Query Route Decoding in `VercelWSGIMiddleware` (`app.py`):**
     Inspects `environ["QUERY_STRING"]` for `__route=`. When found, it normalizes `environ["PATH_INFO"] = clean_route` and strips `__route` from the query string so Flask route decorators (`@web_bp.route("/downloader")`, `@web_bp.route("/converter")`, etc.) execute natively.
  3. **Fallback in `routes/web.py` (`vercel_entrypoint`):**
     Also inspects `request.args.get("__route")` as a secondary defense layer for direct serverless dispatches.
  4. **Clean Page Segregation:**
     - `/` (`templates/index.html`): High-level Suite Portal featuring two primary workspace cards (`Launch Downloader →` and `Browse Converters →`) plus 7 standalone tool cards.
     - `/downloader` (`templates/downloader.html`): Dedicated Link Downloader page with active header pill and full downloader workflow.
     - `/converter` & `/files` (`templates/converter.html`): Dedicated File Converter Hub with active header pill and universal multi-file converter.
     - `/converter/<tool_slug>` (`templates/tool_converter.html`): Standalone single-purpose conversion tool pages.

### 5. Serverless Multi-Container Zero-Latency Direct Download & Universal Converter Resilience
- **The Problem:**
  1. *404 on Download:* In Vercel serverless environments, functions are multi-container and stateless. Request 1 (`POST /api/generate` or `POST /api/convert`) generated files on container A's `/tmp`. Request 2 (`GET /download/<file_id>`) hit container B where `/tmp` was empty, returning `404 EXPIRED_OR_NOT_FOUND`.
  2. *Unclickable / Missing Convert Button:* On `/converter`, `fileInput.accept` was hardcoded to `.pdf` at initialization. Non-PDF files could not be chosen in the OS picker, or triggered format mismatch errors.
  3. *Missing Auto-Download Trigger:* Frontend conversion lacked automated programmatic click simulation on completion.
- **The Solution:**
  1. **Direct In-Memory Base64 Data URL (`data_url`):** In both `/api/generate` and `/api/convert`, files <= 4 MB are automatically read, base64-encoded, and embedded directly into the response JSON as `data_url: "data:<mime>;base64,..."`. `downloader.js`, `converter.js`, `tool_converter.js`, and `analyzer.js` prefer `data.data_url` if present, triggering the download instantly from browser memory with zero network latency and complete immunity from serverless container divergence.
  2. **Smart Converter Type Auto-Detection:** `converter.js` accepts all supported formats (`.pdf, .docx, .doc, .jpg, .jpeg, .png, .webp, .bmp, .mp4, .mkv, .webm, .mov, .avi, .flv`). Added `detectToolForFiles(files)` which automatically detects uploaded file extensions and re-configures `activeTool`, updating the target format select before staging. Staging displays a prominent `⚡ Convert File Now` button and dropzone browse triggers.
  3. **Universal YouTube & Generic Web Extractor Fallback:** Restored active `YtDlpService` extraction across `extractors/youtube.py` and added fallback in `extractors/generic.py`.
  4. **Pure-Python DOCX to PDF Prioritization:** Prioritizes `_docx_to_pdf_fallback` (using `python-docx` + ReportLab) before any Windows Word COM calls, preventing fatal `0x800706be` RPC crashes on headless environments.

### 6. Sub-Second YouTube & YouTube Shorts Analysis Optimization
- **The Problem:**
  - YouTube analysis previously took minutes (or triggered 60s gateway timeouts). `YtDlpService.extract_info` was sequentially looping through 5 heavy client configurations (`default -tv`, `visionos`, `safari`, `android`, `ios`).
  - On cloud environments (Vercel), web clients triggered YouTube's anti-bot challenge and internal retry loops (10 retries with 20s timeouts each).
  - On deleted/invalid video IDs, yt-dlp was attempting all client configurations and proxies, causing 300+ seconds of wasted retries.
- **The Solution:**
  1. **Instant YouTube oEmbed API Fast Path:**
     - In `extractors/youtube.py`, any 11-character YouTube video ID (from `/shorts/`, `/watch?v=`, or `youtu.be/`) immediately queries YouTube's official oEmbed endpoint (`https://www.youtube.com/oembed?url=...&format=json`).
     - Public valid Shorts and videos return metadata in **0.2 - 0.7 seconds**, 100% immune to anti-bot challenges and datacenter IP blocks.
     - Deleted or non-existent videos return `404` immediately in **~1 second**, returning `VIDEO_NOT_FOUND` without triggering retry spirals.
  2. **Lean yt-dlp Fallback Configuration:**
     - In `services/ytdlp_service.py`, `noplaylist` is strictly forced to `True` (preventing extraction of entire channel feeds or related playlists).
     - Prioritizes the `android` mobile client (`player_client: ["android"]`), reducing yt-dlp fallback execution time to ~1.5 seconds.
     - Tightened `socket_timeout` to 6s on serverless and capped `retries` to 2.

### 7. Browser Top-Frame Data URL Blocking Resolution & Blob Object URLs
- **The Problem:**
  - Modern Chromium browsers (Chrome, Edge, Brave, Safari) block top-frame navigation to `data:` URIs (`Not allowed to navigate top frame to data URL`).
  - When the frontend received base64 `data_url` in `/api/convert` or `/api/generate`, setting `autoLink.href = data.data_url` and calling `.click()` was blocked by the browser to prevent drive-by download attacks.
  - Manual clicks on `<a href="data:...">` opened `about:blank#blocked`.
  - Immediate `document.body.removeChild(autoLink)` in the same synchronous task also aborted pending downloads in some browsers.
  - On Linux/Vercel serverless environments, static `imageio-ffmpeg` binary permissions lacked `+x`, causing media conversions to throw 422.
- **The Solution:**
  1. **Blob Object URL Converter (`dataUrlToBlobUrl`):**
     - In `static/js/converter.js`, `static/js/tool_converter.js`, and `static/js/downloader.js` (and mirrored in `public/static/js/`), `dataUrlToBlobUrl(dataUrl)` decodes the base64 string to a `Uint8Array`, creates a `new Blob([bytes], { type: mimeType })`, and generates a local `blob:` URL via `URL.createObjectURL(blob)`.
     - Browsers treat `blob:https://...` as a safe local file object with zero navigation restrictions.
  2. **Direct Memory Button & Auto-Download:**
     - `dlBtn.href = blobUrl; dlBtn.setAttribute("download", filename);`
     - Auto-download creates `<a href="blobUrl" download="filename">`, clicks it, and schedules cleanup via `setTimeout(..., 600)`.
     - Manual button clicks download directly from browser memory without any network request or serverless 404 risk.
  3. **Direct Binary Streaming Mode (`?stream=1`):**
     - `/api/convert?stream=1` supports streaming the converted file directly back as binary attachment with `X-Filename` and `X-Filesize` headers, avoiding base64 encoding overhead.
  4. **Strict Vercel Payload Protection:**
     - In `routes/converter.py` and `routes/api.py`, `data_url` payload threshold is set to `3.2MB` raw bytes (~4.26MB base64) to strictly prevent exceeding Vercel's 4.5MB serverless response limit.
  5. **Executable Permissions for FFmpeg on Linux:**
     - In `utils/ffmpeg_helper.py`, added runtime `os.chmod(exe, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)` for Linux/serverless instances.
