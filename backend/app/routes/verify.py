from fastapi import APIRouter, HTTPException, status

from app.logger import logger
from app.schemas.ledger import LedgerIntegrityReport, LedgerRecord
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/api/v1", tags=["Verification"])


@router.get(
    "/verify/{batch_id}",
    response_model=LedgerRecord,
    responses={404: {"description": "Batch ID not found"}},
)
async def verify_batch(batch_id: str):
    """
    Retrieve verification record by batch ID.

    This is the **public traceability endpoint** - it can be:
    - Linked from QR codes
    - Shared with customers
    - Used by auditors

    No authentication required (verification records are public by design).
    """
    service = VerificationService()

    try:
        record = await service.get_verification_by_batch_id(batch_id)
        return record

    except ValueError as e:
        logger.warning(f"Batch ID lookup failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": str(e)})


@router.get("/verify/integrity/check", response_model=LedgerIntegrityReport)
async def check_ledger_integrity():
    """
    Verify cryptographic integrity of entire ledger.

    Checks:
    - Hash chain is unbroken
    - Each record hash matches its content
    - No tampering detected

    This is an administrative endpoint (add authentication in production).
    """
    service = VerificationService()

    logger.info("Ledger integrity check requested")

    report = await service.verify_ledger_integrity()

    if not report.is_valid:
        logger.error(
            f"Ledger integrity violation: {report.error_message} at record {report.first_invalid_record}"
        )

    return report
