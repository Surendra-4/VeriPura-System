import mimetypes
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.infra.storage import StorageService
from app.logger import logger
from app.ml.pipeline import MLPipeline
from app.ml.parser import ParserError
from app.schemas.upload import DocumentType, FileMetadata
from app.schemas.validation import RuleViolationSchema, ValidationResponse


class DocumentServiceError(Exception):
    """Business logic errors for document processing"""

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class DocumentService:
    """
    Business logic for document ingestion.
    Validates files, orchestrates storage, extracts metadata.
    """

    def __init__(self):
        self.settings = get_settings()
        self.storage = StorageService()

    @staticmethod
    def classify_document_type(mime_type: str, extension: str) -> DocumentType:
        """
        Determine document type from MIME type and extension.
        """
        mime_lower = mime_type.lower()
        ext_lower = extension.lower()

        if mime_lower == "application/pdf" or ext_lower == ".pdf":
            return DocumentType.PDF
        elif mime_lower.startswith("image/") or ext_lower in [".png", ".jpg", ".jpeg"]:
            return DocumentType.IMAGE
        elif mime_lower == "text/csv" or ext_lower == ".csv":
            return DocumentType.CSV
        else:
            raise DocumentServiceError(
                message=f"Unsupported file type: {mime_type}",
                error_code="UNSUPPORTED_FILE_TYPE",
            )

    def validate_file(self, filename: str, file_size: int, mime_type: str) -> None:
        """
        Validate file before processing.
        Raises DocumentServiceError if validation fails.
        """
        # Check size
        if file_size > self.settings.max_upload_size:
            max_mb = self.settings.max_upload_size / (1024 * 1024)
            raise DocumentServiceError(
                message=f"File too large. Maximum size: {max_mb:.1f} MB",
                error_code="FILE_TOO_LARGE",
            )

        if file_size == 0:
            raise DocumentServiceError(message="File is empty", error_code="EMPTY_FILE")

        # Check extension
        extension = Path(filename).suffix.lower()
        if extension not in self.settings.allowed_extensions:
            allowed = ", ".join(self.settings.allowed_extensions)
            raise DocumentServiceError(
                message=f"Invalid file type. Allowed: {allowed}",
                error_code="INVALID_FILE_TYPE",
            )

        # Verify MIME type matches extension
        expected_mime = mimetypes.guess_type(filename)[0]
        if (
            expected_mime
            and mime_type != "application/octet-stream"
            and not mime_type.startswith(expected_mime.split("/")[0])
        ):
            raise DocumentServiceError(
                message="File extension does not match content type",
                error_code="MIME_MISMATCH",
            )

    async def validate_document(
        self, metadata: FileMetadata, file_path: Path
    ) -> ValidationResponse:
        """
        Run ML validation on uploaded document.

        Args:
            metadata: File metadata from upload
            file_path: Path to stored file

        Returns:
            ValidationResponse with fraud score
        """
        pipeline = MLPipeline()

        try:
            result = await pipeline.validate_document(
                file_path=file_path, file_id=metadata.file_id, doc_type=metadata.document_type
            )
        except ParserError as e:
            raise DocumentServiceError(
                message=(
                    "Could not parse document content. The file may be corrupted "
                    "or not a valid PDF/image/CSV."
                ),
                error_code="DOCUMENT_PARSE_FAILED",
            ) from e

        # Convert to response schema
        violations = [
            RuleViolationSchema(
                rule_name=v.rule_name,
                severity=v.severity,
                message=v.message,
                feature_values=v.feature_values,
            )
            for v in result.rule_violations
        ]

        return ValidationResponse(
            file_id=result.file_id,
            fraud_score=result.fraud_score,
            is_anomaly=result.is_anomaly,
            risk_level=result.risk_level,
            rule_violations=violations,
            top_features=result.top_features,
            text_excerpt=result.text_excerpt,
        )

    async def process_upload(self, file: UploadFile) -> FileMetadata:
        """
        Main upload processing pipeline:
        1. Validate file
        2. Save to storage
        3. Extract metadata
        4. Return structured metadata

        Raises:
            DocumentServiceError: If any validation or processing fails
        """
        logger.info(f"Processing upload: {file.filename}")

        # Read file content once
        content = await file.read()
        file_size = len(content)

        # Validate
        self.validate_file(
            filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
        )

        # Create BinaryIO-like object for storage
        from io import BytesIO

        file_obj = BytesIO(content)

        # Save to storage
        file_hash, storage_path = await self.storage.save_file(file_obj, file.filename)

        # Classify document type
        extension = Path(file.filename).suffix
        doc_type = self.classify_document_type(
            file.content_type or "application/octet-stream",
            extension,
        )

        # Build metadata
        metadata = FileMetadata(
            file_id=file_hash,
            original_filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            document_type=doc_type,
            upload_timestamp=datetime.utcnow(),
            sha256_hash=file_hash,
        )

        logger.info(f"Upload complete: {file_hash} ({doc_type.value})")
        return metadata
