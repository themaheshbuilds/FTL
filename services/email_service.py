import os
import re
import time
import uuid
import smtplib
from pathlib import Path
from datetime import datetime, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
from typing import Tuple, Optional, Dict, List

from config import Config
from services.job_service import JobService
from utils.logging import get_logger

logger = get_logger("linkforge.email_service")

# Regex for email validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")



class EmailService:
    """Handles sending generated and converted files to user email addresses via SMTP."""

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
    def validate_email(cls, email: Optional[str]) -> bool:
        if not email or not isinstance(email, str):
            return False
        return bool(EMAIL_REGEX.match(email.strip()))

    is_valid_email = validate_email

    @staticmethod
    def format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        return f"{size_bytes / (1024 ** 3):.1f} GB"

    @classmethod
    def send_file_email(
        cls,
        recipient: str = "",
        file_id: str = "",
        client_ip: str = "",
        base_url: str = "",
        recipient_email: str = "",
    ) -> Tuple[bool, str]:
        """
        Send a file to the recipient email. Returns (success, message).
        Files are always attached directly to the email.
        """
        recipient = (recipient or recipient_email or "").strip()

        # 1. Validate email
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
            gen_dir = Config.GENERATED_STORAGE_DIR / file_id
            if gen_dir.exists() and gen_dir.is_dir():
                files = [p for p in gen_dir.iterdir() if p.is_file()]
                if files:
                    file_path = str(files[0])
                    filename = files[0].name
                    file_size = os.path.getsize(file_path)

        if not file_path or not os.path.exists(file_path):
            return False, "The file is no longer available or has expired. Please regenerate it."

        # 4. Always attach the file directly
        size_str = cls.format_size(file_size)
        download_url = f"{base_url.rstrip('/')}/download/{file_id}" if base_url else f"/download/{file_id}"

        # 5. Build Email
        smtp_user = Config.SMTP_USER
        smtp_pass = Config.SMTP_PASSWORD
        sender_name = Config.SMTP_FROM_NAME or "LinkForge"

        if not smtp_pass:
            return False, (
                "Email delivery is not configured. "
                "Please add your Gmail App Password to SMTP_PASSWORD in .env."
            )

        # Created date string
        created_date_str = ""
        if job and job.created_at:
            if isinstance(job.created_at, (int, float)):
                from datetime import datetime
                created_date_str = datetime.fromtimestamp(job.created_at).strftime("%B %d, %Y")
            elif hasattr(job.created_at, "strftime"):
                created_date_str = job.created_at.strftime("%B %d, %Y")

        # Clean subject - no emoji (spam trigger)
        subject = f"Your file is ready: {filename} ({size_str})"

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{smtp_user}>"
        msg["To"] = recipient
        msg["Reply-To"] = smtp_user
        msg["Date"] = formatdate(localtime=False)
        msg["Message-ID"] = make_msgid(domain="gmail.com")
        msg["X-Mailer"] = "LinkForge/1.0"
        msg["MIME-Version"] = "1.0"
        # Precedence bulk helps avoid out-of-office autoreplies, not spam classification
        msg["Precedence"] = "bulk"

        # 6. Build plain text body (important for spam score)
        attach_note = "The file is attached directly to this email."

        plain_text = (
            f"Hello,\n\n"
            f"Your file '{filename}' ({size_str}) is ready.\n\n"
            f"{attach_note}\n\n"
            f"Download link: {download_url}\n\n"
            f"Note: Download links expire after 30 minutes.\n\n"
            f"-- {sender_name} Team"
        )

        # 7. Build clean HTML body
        status_block = (
            '<div style="margin-top:16px;padding:12px 16px;background:#f0fdf4;'
            'border-left:4px solid #16a34a;border-radius:4px;color:#15803d;font-size:14px;">'
            '<strong>File Attached:</strong> Your file is attached directly to this email.</div>'
        )

        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your file is ready - LinkForge</title>
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 16px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;border:1px solid #e2e8f0;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:28px 24px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.3px;">
              LinkForge - File Ready
            </h1>
            <p style="margin:8px 0 0;color:#c7d2fe;font-size:14px;">Your download has been prepared</p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:28px 24px;">
            <p style="margin:0 0 20px;font-size:15px;color:#374151;line-height:1.6;">
              Hello,<br><br>
              Your file has been processed and is ready for you.
            </p>
            <!-- File details box -->
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:0;">
              <tr><td style="padding:16px 20px;">
                <p style="margin:0 0 10px;font-size:13px;font-weight:600;color:#6366f1;text-transform:uppercase;letter-spacing:0.5px;">File Details</p>
                <table width="100%" cellpadding="4" cellspacing="0">
                  <tr>
                    <td style="color:#6b7280;font-size:14px;width:90px;">Filename</td>
                    <td style="color:#111827;font-size:14px;font-weight:600;">{filename}</td>
                  </tr>
                  <tr>
                    <td style="color:#6b7280;font-size:14px;">Size</td>
                    <td style="color:#111827;font-size:14px;font-weight:600;">{size_str}</td>
                  </tr>
                  <tr>
                    <td style="color:#6b7280;font-size:14px;width:90px;">Created On</td>
                    <td style="color:#111827;font-size:14px;font-weight:600;">{created_date_str}</td>
                  </tr>
                  <tr>
                    <td style="color:#6b7280;font-size:14px;">Status</td>
                    <td style="color:#16a34a;font-size:14px;font-weight:600;">Ready</td>
                  </tr>
                </table>
              </td></tr>
            </table>

            {status_block}

            <!-- Download button -->
            <div style="text-align:center;margin:28px 0 8px;">
              <a href="{download_url}"
                 style="display:inline-block;background:#4f46e5;color:#ffffff;text-decoration:none;
                        font-weight:600;font-size:15px;padding:14px 32px;border-radius:8px;
                        box-shadow:0 4px 12px rgba(79,70,229,0.3);">
                Download File
              </a>
            </div>
            <p style="text-align:center;margin:8px 0 0;font-size:12px;color:#9ca3af;">
              Link expires in 30 minutes
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:16px 24px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0;font-size:12px;color:#9ca3af;">
              Sent by LinkForge - Universal Downloader &amp; File Converter<br>
              This is an automated message. Please do not reply to this email.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

        # Attach text + html as alternatives
        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
        alt_part.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alt_part)

        # 8. Always attach the file
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            part = MIMEApplication(file_data, Name=filename)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)
        except Exception as e:
            logger.warning(f"Could not attach file: {e}")

        # 9. Send via SMTP
        try:
            host = Config.SMTP_HOST or "smtp.gmail.com"
            port = int(Config.SMTP_PORT or 587)
            logger.info(f"Connecting SMTP {host}:{port} -> {recipient}")

            server = smtplib.SMTP(host, port, timeout=25)
            try:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [recipient], msg.as_string())
            finally:
                server.quit()

            logger.info(f"Email sent: {filename} -> {recipient}")
            return True, f"File successfully sent to {recipient}!"

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP auth failed for {smtp_user}: {e}")
            return False, "Gmail authentication failed. Please verify your App Password in SMTP_PASSWORD."
        except Exception as e:
            logger.error(f"SMTP send error -> {recipient}: {e}", exc_info=True)
            return False, f"Email delivery failed: {str(e)}"
