from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from app.infra.qr_generator import QRGenerator, QRGeneratorError
from app.logger import logger

router = APIRouter(prefix="/api/v1", tags=["QR Codes"])


# =========================
# Existing Endpoint (UNCHANGED)
# =========================
@router.get(
    "/qr/{batch_id}",
    responses={
        200: {"content": {"image/png": {}}, "description": "QR code image"},
        404: {"description": "Batch ID not found"},
    },
)
async def get_qr_code(batch_id: str):
    """
    Download QR code image for a batch ID.

    Returns PNG image (300x300px by default).
    Suitable for:
    - Printing on labels/packaging
    - Embedding in documents
    - Sharing digitally

    If QR code doesn't exist, it will be generated on-demand.
    """
    qr_generator = QRGenerator()

    try:
        # Check if QR exists, generate if not
        qr_path = qr_generator.get_qr_path(batch_id)

        if qr_path is None:
            # Generate QR on-demand
            logger.info(f"Generating QR on-demand for {batch_id}")
            qr_path = qr_generator.generate(batch_id)

        # Read image data
        with open(qr_path, "rb") as f:
            img_data = f.read()

        # Return as image response
        return Response(content=img_data, media_type="image/png")

    except QRGeneratorError as e:
        logger.error(f"QR generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to generate QR code",
                "error_code": "QR_GENERATION_FAILED",
            },
        )

    except Exception as e:
        logger.error(f"Unexpected QR error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Batch ID not found",
                "error_code": "BATCH_NOT_FOUND",
            },
        )


# =========================
# NEW: Base64 QR Response Model
# =========================
class QRCodeResponse(BaseModel):
    """Response containing base64-encoded QR code"""

    batch_id: str
    qr_code_base64: str
    format: str = "png"
    size: int


# =========================
# NEW: Base64 QR Endpoint
# =========================
@router.get("/qr/{batch_id}/base64", response_model=QRCodeResponse)
async def get_qr_code_base64(batch_id: str):
    """
    Get QR code as base64-encoded string.

    Useful for:
    - Embedding in JSON responses
    - Frontend display without separate image request
    - Email/document generation

    Response format:
    {
      "batch_id": "BATCH-...",
      "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "format": "png",
      "size": 300
    }

    To display in HTML:
    <img src="data:image/png;base64,{qr_code_base64}" />
    """
    qr_generator = QRGenerator()

    try:
        # Ensure QR exists
        qr_path = qr_generator.get_qr_path(batch_id)

        if qr_path is None:
            logger.info(f"Generating QR on-demand for {batch_id}")
            qr_path = qr_generator.generate(batch_id)

        # Get base64
        qr_base64 = qr_generator.get_qr_as_base64(batch_id)

        return QRCodeResponse(
            batch_id=batch_id,
            qr_code_base64=qr_base64,
            format="png",
            size=qr_generator.settings.qr_code_size,
        )

    except Exception as e:
        logger.error(f"QR base64 generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Batch ID not found",
                "error_code": "BATCH_NOT_FOUND",
            },
        )
