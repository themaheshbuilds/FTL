# LinkForge - AI Developer Context

## 1. Current State

```text
Project: LinkForge
Tagline: One Link. Any File.
Backend: Python 3.11 / Flask
Frontend: Vanilla HTML5 / Modern CSS / Vanilla JavaScript (SPA)

Primary Workflows:
  1. Link Downloader: Public URL analysis, media extraction, dynamic packaging (PDF/ZIP/MP4/Audio)
  2. Universal File Converter: Local file conversion suite (PDF, DOCX, Media, Images)

Current Phase:
  Phase 12 (Universal File Converter Suite) - COMPLETED

Current Test Status:
  45 passed, 0 failed, 0 skipped (Verified in 9.16s via pytest on 2026-10-07)

Current Major Capabilities:
  • SSRF-safe URL validation and protocol enforcement
  • Modular platform extractors (Instagram, LinkedIn, YouTube, X, Reddit, Facebook, Generic)
  • Dynamic media packaging: Images to PDF, Multi-file ZIP, Caption toggle, Custom filename
  • Local format conversions:
      - PDF to Images (PyMuPDF at 150 DPI; single page or multi-page ZIP)
      - Images to PDF (ReportLab & Pillow)
      - Word (DOCX) to PDF (Windows MS Word COM automation with ReportLab fallback)
      - PDF to Word (DOCX) (PyMuPDF text and embedded image extraction)
      - Video to Audio (FFmpeg extraction to MP3 / M4A)
      - Video Converter (FFmpeg remux to MP4, MKV, WebM)
      - Image Converter (Pillow format transform between JPG, PNG, WebP)
  • Isolated job directories (storage/generated/<job_id>) and 30-minute auto-cleanup

Current Next Task:
  Phase 15 (Production Preparation - WSGI, reverse proxy, production monitoring) and
  Phase 13 additions (rate limiting).
```

---

## 2. Source of Truth Priority

When documentation or code appears contradictory, resolve using this strict priority order:

1. **Actual current code behavior** (What the code actually does right now)
2. **Actual passing tests** (What is verified via automated pytest execution)
3. **`Memory.md`** (Persistent architectural records and technical decisions)
4. **`Rules.md`** (Mandatory engineering constraints and security rules)
5. **`PRD.md`** (Product specifications and API contracts)
6. **`Structure.md`** (Filesystem organization and component responsibilities)
7. **`Design.md`** (UI/UX layout specifications and component states)
8. **`Phases.md`** (Development roadmap and completion milestones)
9. **`DeveloperContext.md`** (This instruction manual for AI coding agents)

If an architectural conflict arises, update the documentation so it reflects reality. Never invent features or declare unverified tasks complete.

---

## 3. Architecture & Core Workflows

LinkForge comprises two distinct workflows that converge on shared infrastructure:

```text
                    LINKFORGE
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       LINK WORKFLOW         FILE WORKFLOW
             │                     │
        URL Analyzer          Tool Catalog
             │                     │
      Platform Detector     File Staging
             │                     │
         Extractors         Converter Engines
             │                     │
       Media Objects          Output File
             │                     │
      Media Packaging              │
             │                     │
             └──────────┬──────────┘
                        │
                        ▼
               SHARED INFRASTRUCTURE
                 • JobService & IDs
                 • Storage Isolation
                 • CleanupService
                 • GET /download/<file_id>
```

### Critical Separation Principle
- **LINK EXTRACTION != FILE CONVERSION**
- Never route local file conversion through URL extractors.
- Keep `services/converter_service.py` decoupled from `services/extraction_service.py` and `services/media_service.py`.

---

## 4. API Endpoints

| Endpoint | Method | Workflow | Description |
| :--- | :--- | :--- | :--- |
| `/api/analyze` | `POST` | Link | Validates URL, detects platform, returns metadata and format choices |
| `/api/generate` | `POST` | Link | Asynchronously packages media into chosen format (PDF, ZIP, MP4, etc.) |
| `/api/convert` | `POST` | Converter | Accepts `multipart/form-data` uploads and converts via native engines |
| `/download/<file_id>`| `GET` | Shared | Streams the generated/converted file with sanitized attachment name |
| `/health` | `GET` | System | Returns `{"status": "ok"}` for monitoring |
| `/` | `GET` | Web | Serves the single-page application interface |

---

## 5. Security & Safety Rules

1. **Zero Trust for Inputs:** Never trust remote filenames, uploaded filenames, MIME types, or user extensions. Sanitize all filenames with `utils/filenames.py`.
2. **SSRF Guarding:** Reject loopback IPs (`127.0.0.1`), RFC1918 subnets, cloud metadata (`169.254.169.254`), and non-HTTP/HTTPS schemes.
3. **Subprocess Hardening:** When calling FFmpeg, construct argument lists strictly from validated parameters. Never pass user strings into shell commands.
4. **Temporary Isolation:** Every job operates in a unique directory (`storage/generated/<job_id>`). Clean up temporary staging folders immediately upon job completion or failure.
5. **No Authentication Bypass:** Strictly honor platform access boundaries. Do not bypass paywalls, private account locks, or DRM.

---

## 6. Definition of Done

A task is only complete when:
1. Code works and handles edge/error cases gracefully.
2. Verified by automated tests without errors or warnings.
3. Security considerations are upheld.
4. Documentation files are updated to reflect the change.
5. `Memory.md` is updated with decisions and current phase status.
