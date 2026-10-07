import json
import logging
import sys
import time
from typing import Any, Dict, Optional

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "cookie",
    "cookies",
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "session",
}


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scrub sensitive keys from log dictionaries."""
    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        else:
            sanitized[key] = value
    return sanitized


class StructuredLogFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Include structured extra fields if present
        if hasattr(record, "structured_data") and isinstance(record.structured_data, dict):
            log_entry.update(sanitize_dict(record.structured_data))

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(level_name: str = "INFO") -> None:
    """Configure root and application loggers."""
    log_level = getattr(logging, level_name.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredLogFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on re-initialization
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    operation: str,
    level: int = logging.INFO,
    job_id: Optional[str] = None,
    platform: Optional[str] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
    error_category: Optional[str] = None,
    message: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Log a structured event complying with LinkForge logging standards."""
    data: Dict[str, Any] = {
        "operation": operation,
        "success": success,
    }
    if job_id:
        data["job_id"] = job_id
    if platform:
        data["platform"] = platform
    if duration_ms is not None:
        data["duration_ms"] = round(duration_ms, 2)
    if error_category:
        data["error_category"] = error_category
    if kwargs:
        data.update(kwargs)

    msg = message or f"Operation '{operation}' {'succeeded' if success else 'failed'}"
    logger.log(level, msg, extra={"structured_data": data})
