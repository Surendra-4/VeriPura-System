from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.logger import logger
from app.schemas.upload import UploadError
from app.schemas.validation import ValidationResponse
from app.services.document_service import DocumentService, DocumentServiceError
from app.services.verification_service import VerificationService  # NEW IMPORT

router = APIRouter(prefix="/api/v1", tags=["Upload"])


@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": UploadError, "description": "Validation error"},
        413: {"model": UploadError, "description": "File too large"},
        500: {"model": UploadError, "description": "Server error"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="Document to upload (PDF, image, or CSV)"),
):
    """
    Upload a supply chain document for validation.

    Accepts:
    - PDF files (invoices, certificates, reports)
    - Images (PNG, JPG, JPEG) - scanned documents
    - CSV files (shipment data, inventory logs)

    Returns:
    - File metadata including unique file ID (SHA-256 hash)
    - ML validation results (fraud score, risk level)
    - Storage path for internal reference
    - Ledger verification record
    """
    document_service = DocumentService()

    try:
        # Step 1: Process upload
        metadata = await document_service.process_upload(file)

        # Step 2: Get file path for validation
        storage_service = document_service.storage

        file_path = storage_service.get_file_path(
            metadata.sha256_hash,
            Path(metadata.original_filename).suffix,
        )

        # Step 3: Run ML validation
        validation: ValidationResponse = await document_service.validate_document(
            metadata,
            file_path,
        )

        # Step 4: Record in ledger (NEW)
        verification_service = VerificationService()
        ledger_record = await verification_service.record_verification(
            metadata,
            validation,
        )

        # Construct relative storage path for response
        relative_path = (
            f"{metadata.sha256_hash[:2]}/"
            f"{metadata.sha256_hash[2:4]}/"
            f"{metadata.file_id}"
        )

        # Combined response (UPDATED)
        return {
            "upload": {
                "success": True,
                "message": "File uploaded and validated successfully",
                "metadata": metadata.model_dump(),
                "storage_path": relative_path,
            },
            "validation": validation.model_dump(),
            "verification": {
                "batch_id": ledger_record.batch_id,
                "recorded_at": ledger_record.timestamp.isoformat(),
                "record_hash": ledger_record.record_hash,
                "verification_url": f"/api/v1/verify/{ledger_record.batch_id}",
                "qr_code_url": f"/api/v1/qr/{ledger_record.batch_id}",
            },
        }

    except DocumentServiceError as e:
        logger.warning(f"Upload validation failed: {e.message}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "error_code": e.error_code,
            },
        )

    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An unexpected error occurred during upload",
                "error_code": "INTERNAL_ERROR",
            },
        )