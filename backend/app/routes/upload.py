from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.logger import logger
from app.schemas.upload import UploadError, UploadResponse
from app.services.document_service import DocumentService, DocumentServiceError

router = APIRouter(prefix="/api/v1", tags=["Upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
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
    - Storage path for internal reference
    """
    document_service = DocumentService()

    try:
        metadata = await document_service.process_upload(file)

        # Construct relative storage path for response
        relative_path = f"{metadata.sha256_hash[:2]}/{metadata.sha256_hash[2:4]}/{metadata.file_id}"

        return UploadResponse(
            metadata=metadata,
            storage_path=relative_path,
        )

    except DocumentServiceError as e:
        logger.warning(f"Upload validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": e.message, "error_code": e.error_code},
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
