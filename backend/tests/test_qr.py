import pytest

from app.infra.qr_generator import QRGenerator


@pytest.fixture
def qr_generator(tmp_path, monkeypatch):
    """Fixture with temporary QR directory"""
    from app.config import Settings

    #   qr_dir = tmp_path / "qr_codes"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    settings = Settings(upload_dir=upload_dir)
    monkeypatch.setattr("app.infra.qr_generator.get_settings", lambda: settings)

    return QRGenerator()


def test_qr_generation(qr_generator):
    """Test QR code generation"""
    batch_id = "BATCH-20260207-A3F5E8"

    qr_path = qr_generator.generate(batch_id)

    assert qr_path.exists()
    assert qr_path.suffix == ".png"
    assert qr_path.stat().st_size > 0  # Non-empty file


def test_qr_deduplication(qr_generator):
    """Test that QR codes are not regenerated"""
    batch_id = "BATCH-20260207-ABC123"

    # Generate first time
    qr_path1 = qr_generator.generate(batch_id)
    mtime1 = qr_path1.stat().st_mtime

    # Generate again
    qr_path2 = qr_generator.generate(batch_id)
    mtime2 = qr_path2.stat().st_mtime

    assert qr_path1 == qr_path2
    assert mtime1 == mtime2  # File not modified (reused)


def test_qr_base64_encoding(qr_generator):
    """Test base64 encoding of QR code"""
    batch_id = "BATCH-20260207-TEST01"

    qr_generator.generate(batch_id)
    base64_str = qr_generator.get_qr_as_base64(batch_id)

    assert len(base64_str) > 0
    assert isinstance(base64_str, str)
    # Base64 should only contain valid characters
    import string

    valid_chars = string.ascii_letters + string.digits + "+/="
    assert all(c in valid_chars for c in base64_str)


def test_verification_url_format(qr_generator):
    """Test verification URL construction"""
    batch_id = "BATCH-20260207-XYZ789"

    url = qr_generator._get_verification_url(batch_id)

    assert batch_id in url
    assert url.startswith("http")
    assert "/api/v1/verify/" in url
