import os
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from config import TestingConfig
from services.email_service import EmailService
from services.job_service import JobService


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        yield client


def test_email_validation():
    """Test EmailService email format validation."""
    assert EmailService.validate_email("user@example.com") is True
    assert EmailService.validate_email("test.name+tag@sub.domain.co") is True
    assert EmailService.validate_email("b3242412@gmail.com") is True

    assert EmailService.validate_email("") is False
    assert EmailService.validate_email("not-an-email") is False
    assert EmailService.validate_email("missing@tld") is False
    assert EmailService.validate_email("spaces in@email.com") is False
    assert EmailService.validate_email(None) is False


def test_send_email_missing_payload(client):
    """Test POST /api/send-email with empty body."""
    res = client.post("/api/send-email", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_FILE_ID"


def test_send_email_missing_email(client):
    """Test POST /api/send-email with missing recipient."""
    res = client.post("/api/send-email", json={"file_id": "abc12345"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_EMAIL"


def test_send_email_invalid_recipient_format(client):
    """Test POST /api/send-email with invalid recipient format."""
    res = client.post("/api/send-email", json={"file_id": "abc12345", "email": "invalid-address"})
    assert res.status_code == 422
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_EMAIL"


def test_send_email_nonexistent_file(client):
    """Test POST /api/send-email when file_id does not exist."""
    res = client.post("/api/send-email", json={"file_id": "nonexistent999", "email": "target@example.com"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMAIL_DELIVERY_FAILED"


def test_send_email_successful_mock_smtp(client, tmp_path):
    """Test POST /api/send-email with mocked SMTP server."""
    # 1. Create a dummy job with an existing output file
    job = JobService.create_job("https://example.com/test", "pdf")
    dummy_file = tmp_path / "test_document.pdf"
    dummy_file.write_bytes(b"%PDF-1.4 sample pdf content for email testing")

    JobService.update_job_success(
        job_id=job.job_id,
        output_path=str(dummy_file),
        filename="test_document.pdf",
        mime_type="application/pdf",
        filesize=os.path.getsize(dummy_file)
    )

    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        with patch("config.Config.SMTP_PASSWORD", "test-app-password-1234"):
            res = client.post("/api/send-email", json={
                "file_id": job.job_id,
                "email": "recipient@example.com"
            })

            assert res.status_code == 200
            data = res.get_json()
            assert data["success"] is True
            assert "successfully sent" in data["message"].lower()

            # Verify SMTP interactions
            mock_smtp_instance.starttls.assert_called_once()
            mock_smtp_instance.login.assert_called_once()
            mock_smtp_instance.sendmail.assert_called_once()
            mock_smtp_instance.quit.assert_called_once()
