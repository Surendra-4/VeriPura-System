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

    # Logging
    log_level: str = "INFO"
    
    tesseract_cmd: str = "/opt/homebrew/bin/tesseract"  
    model_version: str = "v1"
    anomaly_threshold: float = 0.6  # Scores above this are flagged
    min_text_length: int = 10  # Minimum characters for valid document
    max_text_length: int = 100000  # Maximum characters to process

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
