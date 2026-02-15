# /Users/vaibhavithakur/veripura-system/backend/app/config.py

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Defaults are suitable for local development.
    """

    # Application
    app_name: str = "VeriPura Backend"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Paths (relative to project root)
    base_dir: Path = Path(__file__).parent.parent
    upload_dir: Path = base_dir / "data" / "uploads"
    model_dir: Path = base_dir / "models"
    ledger_path: Path = base_dir / "data" / "ledger.jsonl"

    # File Upload Limits
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_extensions: set[str] = {".pdf", ".png", ".jpg", ".jpeg", ".csv"}

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_origin_regex: str | None = r"https://.*\.vercel\.app$"

    # Logging
    log_level: str = "INFO"

    tesseract_cmd: str = "tesseract"
    model_version: str = "v1"
    anomaly_threshold: float = 0.6  # Scores above this are flagged
    anomaly_decision_threshold: float = -0.08  # decision_function <= threshold => anomaly
    min_text_length: int = 10  # Minimum characters for valid document
    max_text_length: int = 100000  # Maximum characters to process

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # QR Code Configuration
    qr_code_size: int = 300  # Pixels (square)
    qr_base_url: str = "http://localhost:8000"  # Will be replaced in production

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Normalize configured origins to avoid slash mismatch:
        # browser Origin header is sent without trailing slash.
        self.cors_origins = [origin.rstrip("/") for origin in self.cors_origins]
        self.qr_base_url = self.qr_base_url.rstrip("/")

        # Ensure critical directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance. Call this instead of instantiating Settings directly.
    """
    return Settings()
