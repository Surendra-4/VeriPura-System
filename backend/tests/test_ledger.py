import pytest

from app.infra.batch_id import BatchIDGenerator
from app.infra.ledger import Ledger
from app.schemas.ledger import DocumentMetadataSummary, ValidationResultSummary


@pytest.fixture
async def ledger(tmp_path, monkeypatch):
    """Fixture with temporary ledger"""
    from app.config import Settings

    settings = Settings(ledger_path=tmp_path / "test_ledger.jsonl")
    monkeypatch.setattr("app.infra.ledger.get_settings", lambda: settings)
    return Ledger()


@pytest.mark.asyncio
async def test_append_record(ledger):
    """Test appending a record to ledger"""
    batch_id = BatchIDGenerator.generate()

    doc_meta = DocumentMetadataSummary(
        original_filename="test.pdf",
        file_size=100,
        document_type="pdf",
        mime_type="application/pdf",
    )

    val_result = ValidationResultSummary(
        fraud_score=25.0, risk_level="low", is_anomaly=False, rule_violation_count=0
    )

    record = await ledger.append_record(
        batch_id=batch_id,
        file_id="test_hash_123",
        document_metadata=doc_meta,
        validation_result=val_result,
    )

    assert record.batch_id == batch_id
    assert record.file_id == "test_hash_123"
    assert record.previous_hash is None  # First record (genesis)
    assert len(record.record_hash) == 64  # SHA-256 hex


@pytest.mark.asyncio
async def test_hash_chaining(ledger):
    """Test that records are cryptographically chained"""
    doc_meta = DocumentMetadataSummary(
        original_filename="test.pdf",
        file_size=100,
        document_type="pdf",
        mime_type="application/pdf",
    )

    val_result = ValidationResultSummary(
        fraud_score=25.0, risk_level="low", is_anomaly=False, rule_violation_count=0
    )

    # Add first record
    record1 = await ledger.append_record(
        batch_id="BATCH-1",
        file_id="file1",
        document_metadata=doc_meta,
        validation_result=val_result,
    )

    # Add second record
    record2 = await ledger.append_record(
        batch_id="BATCH-2",
        file_id="file2",
        document_metadata=doc_meta,
        validation_result=val_result,
    )

    # Verify chain
    assert record1.previous_hash is None
    assert record2.previous_hash == record1.record_hash


@pytest.mark.asyncio
async def test_integrity_verification(ledger):
    """Test ledger integrity check"""
    doc_meta = DocumentMetadataSummary(
        original_filename="test.pdf",
        file_size=100,
        document_type="pdf",
        mime_type="application/pdf",
    )

    val_result = ValidationResultSummary(
        fraud_score=25.0, risk_level="low", is_anomaly=False, rule_violation_count=0
    )

    # Add multiple records
    for i in range(3):
        await ledger.append_record(
            batch_id=f"BATCH-{i}",
            file_id=f"file{i}",
            document_metadata=doc_meta,
            validation_result=val_result,
        )

    # Verify integrity
    report = await ledger.verify_integrity()

    assert report.is_valid is True
    assert report.total_records == 3
    assert report.checked_records == 3


@pytest.mark.asyncio
async def test_batch_id_format():
    """Test batch ID generation and validation"""
    batch_id = BatchIDGenerator.generate()

    # Check format
    assert batch_id.startswith("BATCH-")
    assert len(batch_id) == 21  # BATCH-YYYYMMDD-XXXXXX

    # Validate
    assert BatchIDGenerator.validate_format(batch_id) is True
    assert BatchIDGenerator.validate_format("INVALID-ID") is False
