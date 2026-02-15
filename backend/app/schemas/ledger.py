from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExtractedEntityFields(BaseModel):
    """Structured entities persisted for shipment consistency analysis."""

    batch_id: str | None = None
    exporter: str | None = None
    quantity: str | None = None
    dates: list[str] = Field(default_factory=list)
    certificate_id: str | None = None


class DocumentMetadataSummary(BaseModel):
    """Subset of document metadata for ledger storage"""

    original_filename: str
    file_size: int
    document_type: str
    mime_type: str
    extracted_entities: ExtractedEntityFields = Field(default_factory=ExtractedEntityFields)


class ValidationResultSummary(BaseModel):
    """Subset of validation result for ledger storage"""

    fraud_score: float
    risk_level: str
    is_anomaly: bool
    rule_violation_count: int


class LedgerRecord(BaseModel):
    """
    Single immutable ledger entry.
    Once written, this record is permanent and cryptographically linked.
    """

    batch_id: str = Field(..., description="Unique batch identifier for traceability")
    timestamp: datetime = Field(..., description="UTC timestamp of record creation")
    file_id: str = Field(..., description="SHA-256 hash of uploaded file")
    document_metadata: DocumentMetadataSummary
    validation_result: ValidationResultSummary
    previous_hash: Optional[str] = Field(
        None, description="Hash of previous record (null for genesis)"
    )
    record_hash: str = Field(..., description="SHA-256 hash of this record")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class LedgerQuery(BaseModel):
    """Query parameters for ledger lookup"""

    batch_id: Optional[str] = None
    file_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    risk_level: Optional[str] = None
    limit: int = Field(default=100, le=1000, description="Maximum records to return")


class LedgerIntegrityReport(BaseModel):
    """Result of ledger integrity check"""

    is_valid: bool
    total_records: int
    checked_records: int
    first_invalid_record: Optional[int] = None
    error_message: Optional[str] = None
