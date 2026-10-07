# LinkForge - Development Memory

> This file is the persistent architectural memory of LinkForge.
> Update it whenever an important architectural, technical, or product decision is made.
> It captures key decisions, constraints, and current state—not a line-by-line diary.

---

# 1. Current State

```text
Project: LinkForge
Tagline: One Link. Any File.
Architecture: Dual-Workflow Platform (Link Downloader & Universal File Converter)
Backend: Python 3.11 / Flask
Frontend: Vanilla HTML5 / CSS / JavaScript (Single-Page Application)

Current Phase:
  Phase 12 (Universal File Converter Suite) - COMPLETED

Current Test Status:
  45 passed, 0 failed, 0 skipped (Verified in 9.16s via pytest on 2026-10-07)

Link Workflow Status:
  Operational (YouTube, Instagram, LinkedIn, Reddit, X / Twitter, Facebook, Generic)
  Supports multi-page PDF compilation, multi-media ZIP archives, MP4 video, and audio extraction.

Converter Workflow Status:
  Operational via POST /api/convert:
  • PDF to Images (PyMuPDF at 150 DPI; single page or multi-page ZIP)
  • Images to PDF (ReportLab & Pillow)
  • Word (DOCX) to PDF (Windows MS Word COM automation with ReportLab fallback)
  • PDF to Word (DOCX) (PyMuPDF text and embedded image extraction)
  • Video to Audio (FFmpeg extraction to MP3 192kbps or M4A AAC)
  • Video Converter (FFmpeg container remux to MP4, MKV, WebM)
  • Image Converter (Pillow format transform between JPG, PNG, WebP)

Security Status:
  Core Hardened: SSRF protection (loopback/private IP blocking), Path traversal protection,
  Subprocess argument hardening, Isolated job directories, 30-minute auto-cleanup.
  Production Hardening (IP rate-limiting, reverse proxy) pending.

Next Task:
  Phase 15 (Production Preparation - WSGI/Gunicorn setup, reverse proxy, monitoring)
  and Phase 13 additions (rate-limiting).
```

---

# 2. Project Identity

- **Name:** LinkForge
- **Tagline:** One Link. Any File.
- **Framework:** Flask (Python)
- **Design Aesthetic:** Modern light-first interface (Plus Jakarta Sans, JetBrains Mono, indigo accents)

---

# 3. Core Architecture Decisions

## Dual-Workflow Separation
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

### Key Principles
1. **LINK EXTRACTION != FILE CONVERSION:** Extraction logic handles external network requests, SSRF guards, and platform scrapers. Conversion handles local file transforms. Keep them decoupled.
2. **Backend Controls Format Catalog:** The backend computes valid output formats based on detected media type or tool category; the frontend renders them dynamically.
3. **No Authentication Bypass:** LinkForge only processes public content. It never circumvents login screens, DRM, or private accounts.
4. **Isolated Job Sandboxes:** All operations write to `storage/generated/<job_id>/` with 30-minute lifetime managed by `CleanupService`.

---

## 4. Key Engines & Libraries

- **Web Server:** Flask 3.1+ application factory pattern
- **Video & Audio Extraction:** `yt-dlp`
- **Video & Audio Transcoding:** `imageio-ffmpeg` (bundled static FFmpeg binary)
- **PDF Generation & Rasterization:**
  - Rasterization (PDF -> Images): PyMuPDF (`fitz` 1.25+)
  - Compilation (Images -> PDF): ReportLab & Pillow (`services/pdf_service.py`)
- **Word Processing:**
  - `python-docx` for document structure and text/image extraction
  - Microsoft Word COM automation (`win32com.client`) on Windows for 100% native layout fidelity with pure Python fallback
- **Packaging:** Standard library `zipfile` with path-sanitized entries

---

## 5. Security & Safety Implementation

- **SSRF Defense:** `utils/security.py` resolves target hostnames and validates that destination IPs are strictly public, rejecting `127.0.0.1`, RFC1918 private ranges, and cloud metadata (`169.254.169.254`).
- **Path Traversal Defense:** `utils/filenames.py` strips `..`, illegal characters, and normalizes file extensions.
- **Subprocess Safety:** FFmpeg arguments are assembled programmatically into discrete list tokens without invoking `shell=True`.
- **Credential Scrubbing:** Structured logs redact query parameters containing tokens, cookies, or auth keys.

---

## 6. Endpoints Reference

- `POST /api/analyze` - Validates URL, identifies platform, returns media type and supported formats.
- `POST /api/generate` - Packages media from analyzed URL into selected format.
- `POST /api/convert` - Multipart endpoint converting local uploaded files.
- `GET /download/<file_id>` - Streams the completed file with proper headers.
- `GET /health` - Health probe returning `{"status": "ok"}`.
- `GET /` - Serves the unified single-page application.

---

## 7. Phase Completion Record

```text
PHASE: Phase 0 - Project Foundation
STATUS: COMPLETED
DATE: 2026-10-06
TESTS: tests/test_health.py (2/2 passed)
NOTES: Application factory, storage setup, structured logging, health check.
```

```text
PHASE: Phases 1 through 11 - LinkForge MVP Core
STATUS: COMPLETED
DATE: 2026-10-06
TESTS: 24/24 passed
NOTES: End-to-end link extraction pipeline, modular extractors (Instagram, LinkedIn, YouTube, etc.), packaging (PDF/ZIP/DOCX), SSRF security, and responsive UI.
```

```text
PHASE: Phase 12 - Universal File Converter Suite
STATUS: COMPLETED
DATE: 2026-10-07
TESTS: 45/45 passed (Full test suite verified in 9.16s)
NOTES: Built local conversion suite with dedicated POST /api/convert endpoint. Implemented PDF to Images (PyMuPDF), Images to PDF (ReportLab), Word to PDF (Word COM + Fallback), PDF to Word, Video to Audio (FFmpeg), Video Converter, and Image Converter. Integrated mode switcher tabs, drag-and-drop workspace, format selectors, and custom file renaming.
```
