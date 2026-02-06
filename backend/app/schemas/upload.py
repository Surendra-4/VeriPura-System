from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    """Supported document types"""

    PDF = "pdf"
    IMAGE = "image"
    CSV = "csv"


class FileMetadata(BaseModel):
    """
    Metadata extracted from uploaded file.
    Immutable record of file properties.
    """

    file_id: str = Field(..., description="Unique identifier (SHA-256 hash)")
    original_filename: str = Field(..., description="User-provided filename")
    file_size: int = Field(..., description="File size in bytes", gt=0)
    mime_type: str = Field(..., description="MIME type")
    document_type: DocumentType = Field(..., description="Classified document type")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    sha256_hash: str = Field(..., description="SHA-256 checksum")

    @field_validator("original_filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Remove path separators and null bytes
        forbidden = ["/", "\\", "\0", "..", "~"]
        for char in forbidden:
            if char in v:
                raise ValueError(f"Invalid character in filename: {char}")
        if not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()


class UploadResponse(BaseModel):
    """
    Response returned after successful upload.
    """

    success: bool = True
    message: str = Field(default="File uploaded successfully")
    metadata: FileMetadata
    storage_path: str = Field(..., description="Internal storage path (relative)")


class UploadError(BaseModel):
    """
    Error response for failed uploads.
    """

    success: bool = False
    error: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
