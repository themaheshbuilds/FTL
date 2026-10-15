import os
import re
import time
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Tuple, Optional, Dict, List

from config import Config
from services.job_service import JobService
from utils.logging import get_logger

logger = get_logger("linkforge.email_service")

# Regex for email validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Maximum attachment size for standard email providers (25 MB)
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024


class EmailService:
    """Handles sending generated and converted files to user email addresses via SMTP or Resend."""

    # In-memory IP rate limiter: {ip: [timestamps]}
    _ip_history: Dict[str, List[float]] = {}
    _MAX_PER_MINUTE = 5

    @classmethod
    def _is_rate_limited(cls, ip: str) -> bool:
        """Check if client IP has exceeded the allowed email rate."""
        if not ip:
            return False
        now = time.time()
        cls._ip_history[ip] = [t for t in cls._ip_history.get(ip, []) if now - t < 60.0]
        if len(cls._ip_history[ip]) >= cls._MAX_PER_MINUTE:
            return True
        cls._ip_history[ip].append(now)
        return False

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate recipient email address syntax and length."""
        if not email or not isinstance(email, str):
            return False
        email_clean = email.strip()
        if len(email_clean) > 100 or len(email_clean) < 5:
            return False
        return bool(EMAIL_REGEX.match(email_clean))

    @classmethod
    def format_size(cls, size_bytes: int) -> str:
        """Human-readable size format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    @classmethod
    def send_file_email(
        cls,
        file_id: str,
        recipient_email: str,
        client_ip: str = "",
        base_url: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """Send generated or converted file to recipient email.
        
        Returns:
            Tuple of (success: bool, error_message_or_success_message: Optional[str])
        """
        # 1. Validate Email
        recipient = (recipient_email or "").strip().lower()
        if not cls.validate_email(recipient):
            return False, "Please provide a valid recipient email address."

        # 2. Rate limit check
        if cls._is_rate_limited(client_ip):
            return False, "Too many email requests. Please wait a minute before sending another file."

        # 3. Locate File
        file_path = None
        filename = "download_file"
        file_size = 0

        job = JobService.get_job(file_id)
        if job and job.output_file_path and os.path.exists(job.output_file_path):
            file_path = job.output_file_path
            filename = job.output_filename or os.path.basename(file_path)
            file_size = job.filesize or os.path.getsize(file_path)
        else:
            # Resilient disk search for serverless cold-start instances
            gen_dir = Config.GENERATED_STORAGE_DIR / file_id
            if gen_dir.exists() and gen_dir.is_dir():
                files = [p for p in gen_dir.iterdir() if p.is_file()]
                if files:
                    file_path = str(files[0])
                    filename = files[0].name
                    file_size = os.path.getsize(file_path)

        if not file_path or not os.path.exists(file_path):
            return False, "The file is no longer available or has expired. Please regenerate it."

        # 4. Check attachment feasibility (<= 25 MB)
        can_attach = file_size <= MAX_ATTACHMENT_BYTES
        size_str = cls.format_size(file_size)
        download_url = f"{base_url.rstrip('/')}/download/{file_id}" if base_url else f"/download/{file_id}"

        # 5. Build Email Content
        subject = f"Your file is ready: {filename} ({size_str})"
        sender_name = Config.SMTP_FROM_NAME or "LinkForge"
        sender_email = Config.SMTP_USER or "b3242412@gmail.com"

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = recipient

        # Alternative part for plain text & HTML
        alt_part = MIMEMultipart("alternative")

        plain_text = (
            f"Hello,\n\n"
            f"Your file '{filename}' ({size_str}) is ready.\n\n"
            f"{'The file is attached to this email.' if can_attach else 'Due to email provider size limits (>25 MB), your file is available via direct download.'}\n\n"
            f"Download Link: {download_url}\n\n"
            f"Note: Temporary links remain available for 30 minutes.\n\n"
            f"— {sender_name}"
        )

        attachment_badge = (
            '<div style="margin-top: 15px; padding: 10px 14px; background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; border-radius: 4px; color: #047857; font-size: 14px;">'
            '📎 <strong>File Attached:</strong> This file is attached directly to this email.'
            '</div>'
            if can_attach else
            '<div style="margin-top: 15px; padding: 10px 14px; background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; border-radius: 4px; color: #1d4ed8; font-size: 14px;">'
            '🚀 <strong>Large File Notice:</strong> Since this file exceeds 25 MB, click the button below to download it securely.'
            '</div>'
        )

        html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; margin: 0; padding: 24px; color: #e2e8f0; }}
  .container {{ max-width: 580px; margin: 0 auto; background: #1e293b; border-radius: 12px; border: 1px solid #334155; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
  .header {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
  .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
  .content {{ padding: 28px 24px; }}
  .file-box {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 18px; margin: 20px 0; }}
  .file-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }}
  .file-label {{ color: #94a3b8; font-weight: 500; }}
  .file-val {{ color: #f8fafc; font-weight: 600; word-break: break-all; }}
  .btn-container {{ text-align: center; margin: 28px 0 16px; }}
  .btn {{ display: inline-block; background: #4f46e5; color: #ffffff !important; text-decoration: none; font-weight: 600; font-size: 15px; padding: 14px 28px; border-radius: 8px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35); }}
  .footer {{ padding: 20px 24px; background: #0f172a; border-top: 1px solid #334155; text-align: center; font-size: 12px; color: #64748b; }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚡ LinkForge File Delivery</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; margin: 0 0 16px; color: #cbd5e1;">Your requested file has been generated and is ready for use.</p>
      
      <div class="file-box">
        <div style="font-size: 16px; font-weight: 700; color: #818cf8; margin-bottom: 12px;">📁 File Details</div>
        <div style="margin-bottom: 8px;"><span style="color: #94a3b8;">Filename:</span> <strong style="color: #ffffff;">{filename}</strong></div>
        <div style="margin-bottom: 8px;"><span style="color: #94a3b8;">Filesize:</span> <strong style="color: #ffffff;">{size_str}</strong></div>
        <div><span style="color: #94a3b8;">Status:</span> <strong style="color: #10b981;">✓ Ready</strong></div>
      </div>

      {attachment_badge}

      <div class="btn-container">
        <a href="{download_url}" class="btn" target="_blank">⬇️ Download File</a>
      </div>
    </div>
    <div class="footer">
      <p style="margin: 0 0 6px;">LinkForge — Universal Downloader & File Converter</p>
      <p style="margin: 0;">Temporary downloads automatically expire in 30 minutes.</p>
    </div>
  </div>
</body>
</html>"""

        alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
        alt_part.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alt_part)

        # 6. Attach File if <= 25 MB
        if can_attach:
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                part = MIMEApplication(file_data, Name=filename)
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)
            except Exception as e:
                logger.warning(f"Could not attach file to email, proceeding with link only: {e}")

        # 7. Deliver via SMTP
        smtp_user = Config.SMTP_USER
        smtp_pass = Config.SMTP_PASSWORD

        if not smtp_pass:
            return False, (
                "Email delivery is not fully configured yet. "
                "A 16-character Google App Password must be added to SMTP_PASSWORD in .env."
            )

        try:
            host = Config.SMTP_HOST or "smtp.gmail.com"
            port = int(Config.SMTP_PORT or 587)
            logger.info(f"Connecting to SMTP {host}:{port} to send file to {recipient}...")

            server = smtplib.SMTP(host, port, timeout=25)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [recipient], msg.as_string())
            server.quit()

            logger.info(f"Successfully emailed {filename} to {recipient}")
            return True, f"File successfully sent to {recipient}!"

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed for user {smtp_user}: {e}")
            return False, "Gmail authentication failed. Please check your 16-character Google App Password in SMTP_PASSWORD."
        except Exception as e:
            logger.error(f"SMTP send error to {recipient}: {e}", exc_info=True)
            return False, f"Email delivery failed: {str(e)}"
