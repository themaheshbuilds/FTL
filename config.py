import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "linkforge-default-dev-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Serverless environment detection
    IS_SERVERLESS = bool(
        os.getenv("VERCEL")
        or os.getenv("VERCEL_ENV")
        or os.getenv("VERCEL_REGION")
        or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
        or os.getenv("LAMBDA_TASK_ROOT")
    )

    # Storage paths
    if IS_SERVERLESS:
        TEMP_STORAGE_DIR = Path(os.getenv("TEMP_STORAGE_DIR", "/tmp/linkforge/temp")).resolve()
        GENERATED_STORAGE_DIR = Path(os.getenv("GENERATED_STORAGE_DIR", "/tmp/linkforge/generated")).resolve()
    else:
        TEMP_STORAGE_DIR = Path(os.getenv("TEMP_STORAGE_DIR", BASE_DIR / "storage" / "temp")).resolve()
        GENERATED_STORAGE_DIR = Path(os.getenv("GENERATED_STORAGE_DIR", BASE_DIR / "storage" / "generated")).resolve()

    # Constraints
    MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", 524_288_000))  # 500 MB default
    DOWNLOAD_TIMEOUT_SECONDS = int(os.getenv("DOWNLOAD_TIMEOUT_SECONDS", 60))
    FILE_EXPIRATION_MINUTES = int(os.getenv("FILE_EXPIRATION_MINUTES", 30))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def ensure_storage_dirs(cls) -> None:
        """Ensure temporary and generated storage directories exist."""
        try:
            cls.TEMP_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            cls.GENERATED_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Fallback for read-only serverless filesystems (e.g. Vercel)
            cls.TEMP_STORAGE_DIR = Path("/tmp/linkforge/temp").resolve()
            cls.GENERATED_STORAGE_DIR = Path("/tmp/linkforge/generated").resolve()
            try:
                cls.TEMP_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
                cls.GENERATED_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    TEMP_STORAGE_DIR = BASE_DIR / "storage" / "test_temp"
    GENERATED_STORAGE_DIR = BASE_DIR / "storage" / "test_generated"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    env_name = os.getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env_name, DevelopmentConfig)
