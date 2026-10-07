import time
from typing import Tuple
from models.result import AnalysisResult
from utils.validation import validate_url
from services.platform_detector import PlatformDetector
from services.extraction_service import extraction_service
from utils.logging import get_logger, log_event

logger = get_logger("linkforge.url_analyzer")


class UrlAnalyzer:
    """Orchestrates URL security verification, platform detection, and extraction analysis."""

    @staticmethod
    def analyze_url(raw_url: str) -> AnalysisResult:
        start_time = time.time()

        # 1. Validate & normalize URL (with SSRF protection)
        is_valid, normalized_url, error_msg = validate_url(raw_url)
        if not is_valid:
            log_event(
                logger,
                operation="url_analysis",
                success=False,
                error_category="VALIDATION_ERROR",
                message=error_msg,
                raw_url=raw_url
            )
            return AnalysisResult(
                success=False,
                platform="Unknown",
                content_type="unknown",
                error_code="INVALID_URL",
                error_message=error_msg or "The provided URL is invalid or unsafe."
            )

        # 2. Detect platform
        detected_platform = PlatformDetector.detect_platform(normalized_url)

        # 3. Dispatch to Extraction Service
        try:
            result = extraction_service.analyze(normalized_url)
            duration_ms = (time.time() - start_time) * 1000

            log_event(
                logger,
                operation="url_analysis",
                platform=result.platform or detected_platform,
                duration_ms=duration_ms,
                success=result.success,
                error_category=result.error_code if not result.success else None,
                media_count=result.media_count
            )
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Error during analysis of {normalized_url}: {e}", exc_info=True)
            log_event(
                logger,
                operation="url_analysis",
                platform=detected_platform,
                duration_ms=duration_ms,
                success=False,
                error_category="INTERNAL_ANALYSIS_ERROR"
            )
            return AnalysisResult(
                success=False,
                platform=detected_platform,
                content_type="unknown",
                error_code="EXTRACTION_FAILED",
                error_message="An error occurred while analyzing the URL."
            )
