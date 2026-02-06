import secrets
from datetime import datetime


class BatchIDGenerator:
    """
    Generates unique, human-readable batch IDs for supply chain traceability.

    Format: BATCH-YYYYMMDD-XXXXXX
    - YYYYMMDD: Date of creation
    - XXXXXX: 6-character random alphanumeric (case-insensitive for QR readability)

    Example: BATCH-20260207-A3F5E8
    """

    @staticmethod
    def generate() -> str:
        """Generate a new batch ID"""
        date_part = datetime.utcnow().strftime("%Y%m%d")
        random_part = secrets.token_hex(3).upper()  # 3 bytes = 6 hex chars
        return f"BATCH-{date_part}-{random_part}"

    @staticmethod
    def validate_format(batch_id: str) -> bool:
        """
        Validate batch ID format.

        Args:
            batch_id: Batch ID string to validate

        Returns:
            True if valid format, False otherwise
        """
        import re

        pattern = r"^BATCH-\d{8}-[A-F0-9]{6}$"
        return bool(re.match(pattern, batch_id))
