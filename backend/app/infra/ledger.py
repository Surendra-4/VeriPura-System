import hashlib
import json
from datetime import datetime
from typing import Optional

import aiofiles
import aiofiles.os

from app.config import get_settings
from app.logger import logger
from app.schemas.ledger import (
    DocumentMetadataSummary,
    LedgerIntegrityReport,
    LedgerRecord,
    ValidationResultSummary,
)


class LedgerError(Exception):
    """Base exception for ledger operations"""

    pass


class Ledger:
    """
    Append-only ledger with cryptographic hash chaining.
    """

    def __init__(self):
        self.settings = get_settings()
        self.ledger_path = self.settings.ledger_path
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self):
        """Create ledger file if it doesn't exist"""
        if not self.ledger_path.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            self.ledger_path.touch()
            logger.info(f"Ledger initialized at {self.ledger_path}")

    @staticmethod
    def _compute_record_hash(record_data: dict) -> str:
        """Compute SHA-256 hash of record"""

        hashable_data = {k: v for k, v in record_data.items() if k != "record_hash"}

        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        canonical_json = json.dumps(
            hashable_data,
            sort_keys=True,
            separators=(",", ":"),
            default=json_serializer,
        )

        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    async def _get_last_record_hash(self) -> Optional[str]:
        """Retrieve hash of last record"""

        if self.ledger_path.stat().st_size == 0:
            return None

        async with aiofiles.open(self.ledger_path, "r", encoding="utf-8") as f:
            lines = await f.readlines()

        if not lines:
            return None

        last_line = lines[-1].strip()
        if not last_line:
            return None

        try:
            last_record = json.loads(last_line)
            return last_record["record_hash"]

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse last record: {e}")
            raise LedgerError("Ledger corrupted") from e

    async def append_record(
        self,
        batch_id: str,
        file_id: str,
        document_metadata: DocumentMetadataSummary,
        validation_result: ValidationResultSummary,
    ) -> LedgerRecord:
        """Append new record"""

        try:
            previous_hash = await self._get_last_record_hash()

            record_data = {
                "batch_id": batch_id,
                "timestamp": datetime.utcnow(),
                "file_id": file_id,
                "document_metadata": document_metadata.model_dump(),
                "validation_result": validation_result.model_dump(),
                "previous_hash": previous_hash,
            }

            record_hash = self._compute_record_hash(record_data)
            record_data["record_hash"] = record_hash

            record = LedgerRecord(**record_data)

            temp_path = self.ledger_path.with_suffix(".tmp")

            async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
                await f.write(record.model_dump_json() + "\n")

            async with aiofiles.open(self.ledger_path, "a", encoding="utf-8") as ledger_file:
                async with aiofiles.open(temp_path, "r", encoding="utf-8") as temp_file:
                    content = await temp_file.read()
                    await ledger_file.write(content)

            await aiofiles.os.remove(temp_path)

            logger.info(f"Ledger record appended: {batch_id}")
            return record

        except Exception as e:
            logger.error(f"Ledger append failed: {str(e)}", exc_info=True)
            raise LedgerError("Failed to append record") from e

    async def get_record_by_batch_id(self, batch_id: str) -> Optional[LedgerRecord]:
        """Get record by batch ID"""

        async with aiofiles.open(self.ledger_path, "r", encoding="utf-8") as f:
            async for line in f:
                line = line.strip()

                if not line:
                    continue

                try:
                    record_data = json.loads(line)

                    if record_data.get("batch_id") == batch_id:
                        return LedgerRecord(**record_data)

                except json.JSONDecodeError:
                    continue

        return None

    async def get_record_by_file_id(self, file_id: str) -> Optional[LedgerRecord]:
        """Get record by file ID"""

        async with aiofiles.open(self.ledger_path, "r", encoding="utf-8") as f:
            async for line in f:
                line = line.strip()

                if not line:
                    continue

                try:
                    record_data = json.loads(line)

                    if record_data.get("file_id") == file_id:
                        return LedgerRecord(**record_data)

                except json.JSONDecodeError:
                    continue

        return None

    async def verify_integrity(self) -> LedgerIntegrityReport:
        """Verify ledger integrity"""

        logger.info("Starting ledger integrity check")

        total_records = 0
        previous_hash = None

        async with aiofiles.open(self.ledger_path, "r", encoding="utf-8") as f:
            line_num = 0

            async for line in f:
                line_num += 1

                line = line.strip()

                if not line:
                    continue

                try:
                    record_data = json.loads(line)
                    total_records += 1

                    # Verify record hash
                    claimed_hash = record_data["record_hash"]
                    computed_hash = self._compute_record_hash(record_data)

                    if claimed_hash != computed_hash:
                        return LedgerIntegrityReport(
                            is_valid=False,
                            total_records=total_records,
                            checked_records=total_records,
                            first_invalid_record=line_num,
                            error_message=f"Record hash mismatch at line {line_num}",
                        )

                    # Verify hash chain
                    if record_data["previous_hash"] != previous_hash:
                        return LedgerIntegrityReport(
                            is_valid=False,
                            total_records=total_records,
                            checked_records=total_records,
                            first_invalid_record=line_num,
                            error_message=f"Hash chain broken at line {line_num}",
                        )

                    previous_hash = claimed_hash

                except json.JSONDecodeError:
                    return LedgerIntegrityReport(
                        is_valid=False,
                        total_records=total_records,
                        checked_records=total_records,
                        first_invalid_record=line_num,
                        error_message=f"Malformed JSON at line {line_num}",
                    )

        logger.info(f"Ledger integrity check passed: {total_records} records verified")

        return LedgerIntegrityReport(
            is_valid=True,
            total_records=total_records,
            checked_records=total_records,
        )

    async def get_all_records(self, limit: int = 100) -> list[LedgerRecord]:
        """Get recent records"""

        records = []

        async with aiofiles.open(self.ledger_path, "r", encoding="utf-8") as f:
            lines = await f.readlines()

        for line in reversed(lines[-limit:]):
            line = line.strip()

            if not line:
                continue

            try:
                record_data = json.loads(line)
                records.append(LedgerRecord(**record_data))

            except json.JSONDecodeError:
                continue

        return records
