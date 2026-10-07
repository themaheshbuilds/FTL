# LinkForge - Project Structure

## 1. Dual-Workflow Architecture

LinkForge is structured around two distinct operational workflows sharing unified infrastructure for job isolation, temporary storage, and file delivery:

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
                     • Job Manager & UUID
                     • Filename Sanitization
                     • Isolated Storage
                     • 30-Min Auto-Cleanup
                             │
                             ▼
                    GET /download/<file_id>
```

### Architectural Separation Principle
- **LINK EXTRACTION != FILE CONVERSION**
- **Link Workflow:** Specializes in network I/O, SSRF validation, platform authentication boundaries, metadata parsing, and packaging public social media.
- **File Workflow:** Specializes in local format manipulation (rasterization, COM automation, transcode, remux) with zero upload latency or remote platform dependence.
- Neither workflow is forced into the other's processing pipeline.

---

## 2. Directory Structure (Actual Filesystem)

```text
Link to File Downloader/
│
├── app.py                     # Flask application factory, error handlers & blueprint registration
├── config.py                  # Environment-specific configuration classes (Dev, Test, Prod)
├── requirements.txt           # Core Python dependencies
├── .env                       # Local environment variables
├── .env.example               # Example template for environment configuration
├── .gitignore                 # Git ignore rules
├── README.md                  # Project overview and quickstart guide
│
├── routes/                    # HTTP Blueprints & API routing
│   ├── __init__.py            # Blueprint registry
│   ├── api.py                 # POST /api/analyze & POST /api/generate (Link Downloader)
│   ├── converter.py           # POST /api/convert (Universal File Converter)
│   ├── download.py            # GET /download/<file_id> (Temporary file delivery)
│   ├── health.py              # GET /health (Heartbeat probe)
│   └── web.py                 # GET / (Single-page application render)
│
├── services/                  # Business logic & pipeline engines
│   ├── __init__.py
│   ├── archive_service.py     # ZIP compression and multi-file packaging
│   ├── cleanup_service.py     # Temporary storage garbage collection & file expiration
│   ├── converter_service.py   # Multi-format conversion engines (PDF, DOCX, Media, Images)
│   ├── docx_service.py        # Word document assembly (.docx)
│   ├── extraction_service.py  # Dispatcher routing URLs to matching extractors
│   ├── generic_downloader.py  # Streamed direct HTTP downloader & OpenGraph scraper
│   ├── job_service.py         # Job creation, state management & registry
│   ├── media_service.py       # High-level media orchestrator (PDF, ZIP, DOCX, video)
│   ├── pdf_service.py         # Pillow + ReportLab multi-page PDF generation
│   ├── platform_detector.py   # Domain parsing and platform classification
│   ├── url_analyzer.py        # URL security checks, sanitization, and dispatch
│   └── ytdlp_service.py       # yt-dlp metadata extraction and video stream fetcher
│
├── extractors/                # Platform-specific public media extractors
│   ├── __init__.py            # Extractor registry
│   ├── base.py                # Abstract BaseExtractor class
│   ├── facebook.py            # Facebook & Facebook Reels extractor
│   ├── generic.py             # Fallback generic HTML/OpenGraph extractor
│   ├── instagram.py           # Instagram photos, carousels, reels & audio
│   ├── linkedin.py            # LinkedIn documents (PDF), videos & images
│   ├── reddit.py              # Reddit videos, audio muxing & galleries
│   ├── twitter.py             # X / Twitter video & image extractor
│   └── youtube.py             # YouTube & YouTube Shorts extractor
│
├── models/                    # Data transfer objects & models
│   ├── __init__.py
│   ├── job.py                 # Job & JobStatus lifecycle models
│   ├── media.py               # MediaItem & MediaType models
│   └── result.py              # ExtractionResult & AnalysisResult models
│
├── utils/                     # Low-level utilities & security helpers
│   ├── __init__.py
│   ├── ffmpeg_helper.py       # FFmpeg wrapper for audio extraction & container remuxing
│   ├── filenames.py           # Filename sanitization, path-traversal prevention, unique naming
│   ├── logging.py             # Structured JSON logger with credential scrubbing
│   ├── mime.py                # MIME-to-extension resolution & header helpers
│   ├── security.py            # SSRF validation, private IP filter, URL scheme guards
│   └── validation.py          # Input payload format validation
│
├── templates/                 # Frontend templates
│   └── index.html             # Single-Page Application (Downloader & Converter views)
│
├── static/                    # Frontend assets
│   ├── css/
│   │   ├── style.css          # Core design tokens, layout variables, typography
│   │   └── components.css     # UI components, mode tabs, tool cards, dropzone, chips
│   │
│   └── js/
│       ├── analyzer.js        # Link Downloader analyze / format generation controller
│       ├── app.js             # General app controller & modal management
│       ├── converter.js       # Universal File Converter UI, catalog & upload controller
│       └── downloader.js      # Polling & file download trigger
│
├── storage/                   # Isolated local filesystem storage
│   ├── temp/                  # Staging for active downloads and uploads
│   └── generated/             # Staged output files indexed by <job_id>
│
├── tests/                     # Automated test suite (pytest)
│   ├── __init__.py
│   ├── test_analyzer.py       # URL validation, SSRF checks, platform detection
│   ├── test_api.py            # Downloader API endpoints & download delivery
│   ├── test_converter.py      # Converter endpoints (PDF, DOCX, images, formats)
│   ├── test_filenames.py      # Filename sanitization & path safety
│   ├── test_frontend.py       # Frontend view & static asset loading
│   ├── test_health.py         # /health and 404 error handler
│   ├── test_instagram_extractor.py # Instagram public carousel/photo extraction
│   ├── test_linkedin_extractor.py  # LinkedIn documents, shortlinks & video
│   ├── test_packaging.py      # PDF, ZIP, DOCX generation & caption injection
│   └── test_security.py       # SSRF private IP, loopback, and scheme tests
│
└── docs/                      # Architectural & project documentation
    ├── Design.md              # UI/UX specification & component states
    ├── DeveloperContext.md    # Instructions and operational rules for AI coding agents
    ├── Memory.md              # Persistent project memory & architecture decisions
    ├── PRD.md                 # Product requirements document
    ├── Phases.md              # Development phases & completion records
    ├── Rules.md               # Engineering rules, security constraints & standards
    └── Structure.md           # Filesystem hierarchy & component responsibilities
```

---

## 3. Directory Responsibilities

| Directory | Primary Responsibility | Architectural Rule |
| :--- | :--- | :--- |
| `routes/` | HTTP request handling, argument parsing, status codes | Must NEVER execute raw conversion or extraction logic directly; must delegate to services. |
| `services/` | Core business logic, packaging, conversion, job lifecycle | Pure logic and workflow orchestration; independent of HTTP request objects. |
| `extractors/` | Platform-specific parsing for public media | Must implement `BaseExtractor` interface; isolated from other platforms. |
| `models/` | Type definitions and standardized data models | Dataclasses holding typed state (`MediaItem`, `Job`, `ExtractionResult`). |
| `utils/` | Low-level sanitization, security checks, and logging | Stateless helper functions; no business workflow knowledge. |
| `templates/` | HTML views | Semantic HTML5 structure for single-page dynamic interface. |
| `static/` | Vanilla CSS and modular JavaScript | Zero-framework frontend handling user events, API fetch calls, and DOM states. |
| `storage/` | Temporary file storage | Isolated per job (`storage/generated/<job_id>`); auto-cleaned on expiry. |
| `tests/` | Automated test verification | Must cover both workflows, security edge cases, and failure modes. |

---

## 4. Workflows & Interfaces

### A. Link Workflow
```text
User Input URL
     │
     ▼
URLAnalyzer.analyze(url)
     ├── security.is_safe_url (SSRF check)
     └── platform_detector.detect_platform
     │
     ▼
ExtractionService.extract(url)
     └── Matches extractor (e.g. InstagramExtractor, LinkedInExtractor, YtdlpService)
     │
     ▼
MediaService.process_content
     └── Evaluates content_type -> Returns available formats (PDF, ZIP, MP4, etc.)
     │
     ▼
User selects output format -> POST /api/generate
     └── ArchiveService / PdfService / MediaService builds output in storage/generated/<job_id>/
     │
     ▼
Download ready via GET /download/<job_id>
```

### B. File Conversion Workflow
```text
User Selects Tool (e.g. PDF to Images, DOCX to PDF, Video to Audio)
     │
     ▼
User stages file(s) via Drag & Drop or File Picker -> POST /api/convert
     ├── Staged in storage/temp/stage_<id>/
     └── Input validated against accepted extensions
     │
     ▼
ConverterService.convert_files(conversion_type, input_files, output_format, custom_filename)
     ├── pdf_to_images: PyMuPDF (fitz) rendering pages at 150 DPI -> Image(s) or ZIP
     ├── images_to_pdf: PdfService.images_to_pdf -> Multi-page PDF
     ├── docx_to_pdf: MS Word COM automation with ReportLab fallback -> PDF
     ├── pdf_to_docx: PyMuPDF text & embedded image extraction -> DOCX
     ├── video_to_audio: FFmpegHelper.extract_audio -> MP3 / M4A
     ├── video_converter: FFmpegHelper.remux_video -> MP4 / MKV / WebM
     └── image_converter: Pillow format transcode -> JPG / PNG / WebP
     │
     ▼
Output saved to storage/generated/<job_id>/<sanitized_filename>
     ├── Registered with JobService
     └── Temporary staging directory immediately deleted
     │
     ▼
Download ready via GET /download/<job_id>
```

---

## 5. Storage Architecture

```text
storage/
├── temp/                      # Ephemeral scratch space
│   ├── stage_<uuid>/          # Isolated upload staging (deleted immediately post-conversion)
│   └── dl_<uuid>/             # Active stream downloads (deleted post-packaging)
│
└── generated/                 # Packaged & converted artifacts ready for user download
    └── <job_id>/              # Job-specific directory
        └── output_file.ext    # Served via /download/<job_id>
```

All files inside `storage/generated/<job_id>` are automatically purged after 30 minutes by `CleanupService.cleanup_expired_jobs()`.
