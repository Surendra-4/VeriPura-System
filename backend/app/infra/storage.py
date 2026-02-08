import hashlib
from pathlib import Path
from typing import BinaryIO

import aiofiles

from app.config import get_settings
from app.logger import logger


class StorageError(Exception):
    """Base exception for storage operations"""

    pass


class StorageService:
    """
    Abstraction layer for file storage.
    Currently uses local filesystem; designed for easy migration to S3/MinIO.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_dir = self.settings.upload_dir

    @staticmethod
    def compute_hash(file_obj: BinaryIO) -> str:
        """
        Compute SHA-256 hash of file contents.
        Reads in chunks to handle large files efficiently.
        """
        sha256 = hashlib.sha256()
        file_obj.seek(0)  # Reset to start
        while chunk := file_obj.read(8192):  # 8 KB chunks
            sha256.update(chunk)
        file_obj.seek(0)  # Reset for subsequent reads
        return sha256.hexdigest()

    def _get_storage_path(self, file_hash: str, original_filename: str) -> Path:
        """
        Generate storage path using hash-based sharding.
        Format: uploads/{first_2_chars}/{next_2_chars}/{hash}_{filename}

        Example: abc123...xyz → uploads/ab/c1/abc123...xyz_invoice.pdf

        Why sharding: Prevents single directory from having millions of files
        (filesystem performance degrades).
        """
        prefix1 = file_hash[:2]
        prefix2 = file_hash[2:4]
        suffix = Path(original_filename).suffix
        filename = f"{file_hash}{suffix}"

        storage_path = self.base_dir / prefix1 / prefix2 / filename
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        return storage_path

    async def save_file(self, file_obj: BinaryIO, original_filename: str) -> tuple[str, Path]:
        """
        Save uploaded file to storage.

        Returns:
            tuple: (file_hash, storage_path)

        Raises:
            StorageError: If save operation fails
        """
        try:
            # Compute hash first
            file_hash = self.compute_hash(file_obj)
            storage_path = self._get_storage_path(file_hash, original_filename)

            # Check if file already exists (deduplication)
            if storage_path.exists():
                logger.info(f"File already exists (deduplicated): {file_hash}")
                return file_hash, storage_path

            # Atomic write: write to temp file, then rename
            temp_path = storage_path.with_suffix(".tmp")
            async with aiofiles.open(temp_path, "wb") as out_file:
                file_obj.seek(0)
                content = file_obj.read()
                await out_file.write(content)

            # Atomic rename (POSIX guarantees atomicity)
            temp_path.rename(storage_path)

            logger.info(f"File saved: {file_hash} → {storage_path}")
            return file_hash, storage_path

        except Exception as e:
            logger.error(f"Storage error for {original_filename}: {str(e)}")
            raise StorageError(f"Failed to save file: {str(e)}") from e

    def get_file_path(self, file_hash: str, extension: str = "") -> Path:
        """
        Retrieve storage path for a given file hash.
        """
        prefix1 = file_hash[:2]
        prefix2 = file_hash[2:4]
        filename = f"{file_hash}{extension}"
        return self.base_dir / prefix1 / prefix2 / filename

    async def delete_file(self, file_hash: str, extension: str = "") -> bool:
        """
        Delete a file from storage.
        Returns True if deleted, False if file didn't exist.
        """
        path = self.get_file_path(file_hash, extension)
        if path.exists():
            path.unlink()
            logger.info(f"File deleted: {file_hash}")
            return True
        return False
