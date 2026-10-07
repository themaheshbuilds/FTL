# LinkForge - Product Requirements Document (PRD)

## 1. Product Identity

- **Name:** LinkForge
- **Tagline:** One Link. Any File.
- **Framework:** Python / Flask
- **Type:** Unified Web Application (Link Downloader & Universal File Converter)

---

## 2. Product Overview

LinkForge is a high-performance web platform combining two distinct capabilities:

1. **Link Downloader:** Analyzes public web and social media links, detects platforms and content structures, and packages media into clean files (original video/audio, multi-page PDFs, or ZIP archives).
2. **Universal File Converter:** A zero-limit local conversion suite allowing users to transform documents, audio, videos, and images directly on their machine without third-party cloud uploads.

Both workflows share unified local storage, job isolation, and temporary file delivery mechanisms.

---

## 3. Core Workflows

### A. Link Workflow
```text
User pastes public URL
        ↓
SSRF & Scheme Validation (HTTP/HTTPS only)
        ↓
Platform Detection (YouTube, Instagram, LinkedIn, Reddit, TikTok, X, etc.)
        ↓
Public Media Extraction (yt-dlp, custom extractors, generic HTTP)
        ↓
Dynamic Output Formats Evaluated
        ↓
User Selects Output (e.g. PDF, ZIP, MP4, Audio)
        ↓
Job Executed -> Output in storage/generated/<job_id>/
        ↓
Direct Download Delivery
```

### B. File Converter Workflow
```text
User selects Conversion Tool (e.g. PDF to Images, DOCX to PDF, Video to Audio)
        ↓
File(s) staged via Drag-and-Drop or File Picker
        ↓
Output format & optional custom filename selected
        ↓
POST /api/convert (multipart/form-data)
        ↓
Native Conversion Engine processes file in isolated scratch space
        ↓
Output registered in JobService -> storage/generated/<job_id>/
        ↓
Direct Download Delivery
```

---

## 4. Supported Platforms & Capabilities

### Link Downloader (Public Content Only)
Platform support is modular and provided on a **best-effort** basis:

| Platform | Primary Media Types | Available Outputs |
| :--- | :--- | :--- |
| **Instagram** | Posts, carousels, reels, audio | Original images, ZIP, Multi-page PDF, MP4 |
| **LinkedIn** | Document posts (slides), videos, image posts | Multi-page PDF, MP4, original images |
| **YouTube** | Videos, Shorts, audio streams | MP4 (Best, 1080p, 720p, 480p), Audio (MP3/M4A) |
| **TikTok** | Public videos | MP4, MP3 |
| **Reddit** | Videos (muxed audio/video), image galleries | MP4, ZIP, Multi-page PDF |
| **X / Twitter** | Videos, multi-image posts | MP4, ZIP, PDF |
| **Facebook** | Public posts, public reels | MP4 |
| **Direct URLs** | Direct files, OpenGraph web pages | Original file, PDF |

### Universal File Converter (Verified Local Conversions)

| Category | Conversion Type | Source Formats | Target Outputs | Engine |
| :--- | :--- | :--- | :--- | :--- |
| **PDF** | `pdf_to_images` | `.pdf` | High-res JPG, PNG (Single image or multi-page ZIP) | PyMuPDF (`fitz`) |
| **PDF** | `images_to_pdf` | `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp` | Multi-page PDF document | ReportLab & Pillow |
| **PDF** | `pdf_to_docx` | `.pdf` | Editable Word document (`.docx`) | PyMuPDF + `python-docx` |
| **Documents** | `docx_to_pdf` | `.docx`, `.doc` | High-fidelity PDF document | Word COM Automation + Fallback |
| **Audio** | `video_to_audio` | `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi` | MP3 (192 kbps), M4A (AAC) | FFmpeg Helper |
| **Video** | `video_converter` | `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi` | MP4, MKV, WebM | FFmpeg Helper |
| **Images** | `image_converter`| `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp` | PNG, JPG, WebP | Pillow |

---

## 5. Security & Legal Boundaries

LinkForge operates under strict compliance rules:

- **Public Content Only:** Processes only publicly accessible web links.
- **No Access Bypasses:** Strictly prohibits bypassing authentication, paywalls, private accounts, DRM, or access controls.
- **SSRF Defenses:** Blocks loopback addresses (`127.0.0.1`), private RFC1918 subnets, cloud metadata endpoints (`169.254.169.254`), and unsafe URL schemes (`file://`, `ftp://`).
- **Filename Sanitization:** All incoming remote and uploaded filenames are sanitized via `sanitize_filename()` to prevent directory traversal (`../`).
- **Storage Isolation:** Every generation and conversion job executes in an isolated temporary directory. Files expire automatically after 30 minutes.

---

## 6. API Specification

### 1. `POST /api/analyze`
Analyzes a URL and returns detected content metadata and available packaging formats.
- **Request:**
  ```json
  {
    "url": "https://www.instagram.com/p/example/"
  }
  ```
- **Response (Success - 200):**
  ```json
  {
    "success": true,
    "platform": "Instagram",
    "content_type": "image_collection",
    "media_count": 8,
    "has_caption": true,
    "caption": "Post description text...",
    "formats": ["pdf", "zip", "images"]
  }
  ```
- **Response (Error - 400 / 422):**
  ```json
  {
    "success": false,
    "error": {
      "code": "SSRF_BLOCKED",
      "message": "Access to local or private network addresses is forbidden."
    }
  }
  ```

### 2. `POST /api/generate`
Packages media from an analyzed link into the requested format.
- **Request:**
  ```json
  {
    "url": "https://www.instagram.com/p/example/",
    "output_format": "pdf",
    "quality": "best",
    "custom_filename": "my_portfolio",
    "with_caption": false
  }
  ```
- **Response (Success - 200):**
  ```json
  {
    "success": true,
    "file_id": "ab12cd34ef56",
    "filename": "my_portfolio.pdf",
    "filesize": 4823910,
    "size_formatted": "4.60 MB"
  }
  ```

### 3. `POST /api/convert`
Uploads local file(s) and executes a file conversion.
- **Request:** `multipart/form-data`
  - `files`: File object(s) (single or multiple)
  - `conversion_type`: `pdf_to_images` | `images_to_pdf` | `docx_to_pdf` | `pdf_to_docx` | `video_to_audio` | `video_converter` | `image_converter`
  - `output_format`: Target format (e.g., `jpg`, `pdf`, `mp3`, `webp`)
  - `custom_filename`: Optional custom filename string
- **Response (Success - 200):**
  ```json
  {
    "success": true,
    "file_id": "7890abcdef12",
    "filename": "my_document.pdf",
    "filesize": 128450,
    "mime_type": "application/pdf",
    "size_formatted": "125.4 KB"
  }
  ```
- **Response (Error - 400 / 422):**
  ```json
  {
    "success": false,
    "error": {
      "code": "MISSING_CONVERSION_TYPE",
      "message": "conversion_type is required."
    }
  }
  ```

### 4. `GET /download/<file_id>`
Delivers a packaged or converted temporary file for download.
- **Path Parameter:** `file_id` (Hexadecimal job ID)
- **Response:** File binary stream with `Content-Disposition: attachment; filename="<sanitized_name>"`
- **Response (Expired or Not Found - 404):**
  ```json
  {
    "success": false,
    "error": {
      "code": "EXPIRED_OR_NOT_FOUND",
      "message": "This file has expired or does not exist."
    }
  }
  ```

### 5. `GET /health`
Heartbeat monitoring endpoint.
- **Response (200):** `{"status": "ok"}`

---

## 7. Frontend User Interface

The application is implemented as an integrated Single-Page Application (SPA) with a top navigation mode switch:

1. **Header Tabs:**
   - `Link Downloader` tab: Displays URL input, quick platform badges, and media preview.
   - `File Converter` tab: Displays category filters (All, Documents, Video & Audio, Images), interactive tool cards, drag-and-drop file staging, dynamic format selectors, and custom filename input.
2. **Dynamic Result Cards:**
   - Media Preview card with format action buttons.
   - Success card with direct download button, file size, and 30-minute expiry notice.
   - Human-readable error cards explaining access constraints without raw stack traces.
