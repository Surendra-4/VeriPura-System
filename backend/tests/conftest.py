"""
Shared pytest fixtures for all tests.
"""

import asyncio

import pytest

from app.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings(tmp_path):
    """Test settings with temporary directories"""
    upload_dir = tmp_path / "uploads"
    model_dir = tmp_path / "models"
    ledger_path = tmp_path / "ledger.jsonl"

    upload_dir.mkdir()
    model_dir.mkdir()

    return Settings(
        upload_dir=upload_dir,
        model_dir=model_dir,
        ledger_path=ledger_path,
        debug=True,
        environment="testing",
    )


@pytest.fixture
def sample_pdf_content():
    """Generate a real in-memory PDF for testing"""
    from io import BytesIO

    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    c.drawString(100, 750, "Sample Invoice")
    c.drawString(100, 730, "Date: 2024-01-15")
    c.drawString(100, 710, "Amount: $500")
    c.drawString(100, 690, "Invoice #: INV-001")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def sample_image_content():
    """Sample image content (1x1 white PNG)"""
    import base64

    # 1x1 white PNG
    png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    return base64.b64decode(png_data)
