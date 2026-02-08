from app.infra.batch_id import BatchIDGenerator
from app.infra.ledger import Ledger
from app.infra.qr_generator import QRGenerator
from app.logger import logger
from app.schemas.ledger import (
    DocumentMetadataSummary,
    LedgerRecord,
    ValidationResultSummary,
)
from app.schemas.upload import FileMetadata
from app.schemas.validation import ValidationResponse


class VerificationService:
    """
    Service layer for verification and ledger operations.
    Orchestrates batch ID generation and ledger writes.
    """

    def __init__(self):
        self.ledger = Ledger()
        self.batch_id_generator = BatchIDGenerator()
        self.qr_generator = QRGenerator()

    async def record_verification(
        self, metadata: FileMetadata, validation: ValidationResponse
    ) -> LedgerRecord:
        """
        Record a verification event in the ledger.

        Args:
            metadata: File metadata from upload
            validation: Validation result from ML pipeline

        Returns:
            LedgerRecord that was written
        """
        # Generate batch ID
        batch_id = self.batch_id_generator.generate()

        logger.info(f"Recording verification: {batch_id}")

        # Prepare summaries for ledger
        doc_summary = DocumentMetadataSummary(
            original_filename=metadata.original_filename,
            file_size=metadata.file_size,
            document_type=metadata.document_type.value,
            mime_type=metadata.mime_type,
        )

        validation_summary = ValidationResultSummary(
            fraud_score=validation.fraud_score,
            risk_level=validation.risk_level,
            is_anomaly=validation.is_anomaly,
            rule_violation_count=len(validation.rule_violations),
        )

        # Append to ledger
        record = await self.ledger.append_record(
            batch_id=batch_id,
            file_id=metadata.file_id,
            document_metadata=doc_summary,
            validation_result=validation_summary,
        )

        # Generate QR code (ADD THIS BLOCK)
        try:
            self.qr_generator.generate(batch_id)
            logger.info(f"QR code generated for {batch_id}")
        except Exception as e:
            # Log error but don't fail the entire verification
            # QR can be generated on-demand later
            logger.error(f"QR generation failed for {batch_id}: {str(e)}")

        return record

    async def get_verification_by_batch_id(self, batch_id: str) -> LedgerRecord:
        """
        Retrieve verification record by batch ID.

        Raises:
            ValueError: If batch ID not found
        """
        record = await self.ledger.get_record_by_batch_id(batch_id)

        if record is None:
            raise ValueError(f"Batch ID not found: {batch_id}")

        return record

    async def verify_ledger_integrity(self):
        """
        Verify entire ledger integrity.

        Returns:
            LedgerIntegrityReport
        """
        return await self.ledger.verify_integrity()
