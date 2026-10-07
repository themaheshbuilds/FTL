# LinkForge - Development Rules

These rules are mandatory for all contributors and AI coding agents.

---

## 1. General Architecture Rules

1. **Understand Before Modifying:** Do not write or refactor code until the architecture, responsibilities, and data contracts are understood.
2. **No Business Logic in Routes:** Flask route functions must strictly handle HTTP concerns (request parsing, response formatting, status codes). All business logic belongs in `services/`.
3. **Decoupled Workflows:** Keep the **Link Downloader** workflow and the **Universal File Converter** workflow completely separated. Do not route local file conversions through link extraction services.
4. **Shared Infrastructure:** Both workflows must share job management (`JobService`), filename sanitization (`utils/filenames.py`), storage sandboxing (`storage/generated/<job_id>`), and download delivery (`/download/<file_id>`).

---

## 2. Core Security & SSRF Defense

1. **Never Trust User Inputs:** Never trust remote filenames, uploaded filenames, file extensions, or MIME headers.
2. **SSRF Guarding:** Every URL analyzed by LinkForge must pass `utils.security.is_safe_url()`:
   - Must use `http://` or `https://`.
   - Must not resolve to `127.0.0.1`, `::1`, RFC1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs, or cloud metadata endpoints (`169.254.169.254`).
3. **No Authentication Bypass:** Strictly honor platform boundaries. Never implement mechanisms to bypass logins, paywalls, private accounts, or DRM.

---

## 3. Converter Security & File Processing Rules

1. **Upload Sanitization:** All uploaded filenames must be sanitized via `sanitize_filename()` before writing to disk to prevent directory traversal (`../`).
2. **Decompression & ZIP Bomb Protection:**
   - When extracting or packaging archives, inspect entry paths to prevent zip-slip traversal.
   - Do not extract archives with disproportionate uncompressed sizes.
3. **Image & PDF Resource Exhaustion Protection:**
   - PIL limits (`Image.MAX_IMAGE_PIXELS`) must remain active to prevent decompression bombs.
   - Avoid loading entire multi-gigabyte video files into RAM; stream files to disk.
4. **Subprocess Hardening:**
   - When invoking FFmpeg or external utilities, never use `shell=True`.
   - All arguments must be passed as an explicit list of validated tokens with hardcoded flags.
5. **COM Automation Teardown (Windows):**
   - When using Microsoft Word COM (`win32com.client`), always wrap operations in `try...finally`.
   - In the `finally` block, explicitly close documents, call `Quit()`, delete COM object references (`del wdoc`, `del word`), and call `pythoncom.CoUninitialize()` to prevent orphaned processes or COM RPC crashes.
6. **Mandatory Job Isolation & Cleanup:**
   - Temporary uploads must write to isolated staging folders (`storage/temp/stage_<id>/`).
   - Staging folders must be purged in a `finally` block immediately after conversion completes or fails.
   - Converted output must reside in `storage/generated/<job_id>/`.
   - All output files must be subjected to 30-minute automatic expiration via `CleanupService`.

---

## 4. Error Handling & Privacy Rules

1. **Zero Stack Traces in Production:** Never expose raw Python tracebacks, internal filesystem paths, environment variables, or secrets in user-facing responses.
2. **Predictable JSON Error Schema:**
   ```json
   {
     "success": false,
     "error": {
       "code": "ERROR_CODE",
       "message": "Human-readable explanation."
     }
   }
   ```
3. **Structured Logging:**
   - Use `utils.logging.get_logger()`.
   - Include job IDs, platforms, and operational context in log entries.
   - Automatically redact cookies, access tokens, and sensitive query parameters.

---

## 5. Frontend & UI Contracts

1. **Backend Controls Format Catalog:** The frontend must never hardcode output format assumptions. The backend dynamically computes available formats based on content detection.
2. **One Primary Action:** Keep views focused, clear, and uncluttered.
3. **Accurate State Feedback:** Never fake progress percentages. Use genuine loading and processing indicators.

---

## 6. Definition of Done

A feature, extractor, or converter is NOT complete until:
1. Implementation is functional and handles edge cases.
2. Tested with passing automated tests in `pytest`.
3. Memory and relevant documentation are updated.
4. Temporary storage cleanup is verified on both success and failure paths.
