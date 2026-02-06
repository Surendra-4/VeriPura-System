import io
from pathlib import Path

import pytest

from app.infra.storage import StorageService, StorageError


@pytest.fixture
def storage_service(tmp_path, monkeypatch):
    """Fixture with temporary upload directory"""
    from app.config import Settings

    settings = Settings(upload_dir=tmp_path / "uploads")
    monkeypatch.setattr("app.infra.storage.get_settings", lambda: settings)
    return StorageService()


@pytest.mark.asyncio
async def test_save_file_success(storage_service):
    """Test successful file save"""
    content = b"test content"
    file_obj = io.BytesIO(content)

    file_hash, storage_path = await storage_service.save_file(file_obj, "test.pdf")

    assert len(file_hash) == 64  # SHA-256 hex length
    assert storage_path.exists()
    assert storage_path.read_bytes() == content


@pytest.mark.asyncio
async def test_deduplication(storage_service):
    """Test that identical files are deduplicated"""
    content = b"duplicate content"
    file_obj1 = io.BytesIO(content)
    file_obj2 = io.BytesIO(content)

    hash1, path1 = await storage_service.save_file(file_obj1, "file1.pdf")
    hash2, path2 = await storage_service.save_file(file_obj2, "file2.pdf")

    assert hash1 == hash2
    assert path1 == path2


def test_compute_hash(storage_service):
    """Test hash computation"""
    content = b"hash test"
    file_obj = io.BytesIO(content)

    hash_value = storage_service.compute_hash(file_obj)

    assert len(hash_value) == 64
    assert hash_value == storage_service.compute_hash(file_obj)  # Deterministic
