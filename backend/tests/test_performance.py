"""
Performance benchmarks for API endpoints.
"""

import io
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Test client"""
    return TestClient(create_app())


@pytest.fixture
def sample_pdf():
    """Generate real in-memory PDF for performance tests"""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    c.drawString(100, 750, "Performance Test Invoice")
    c.drawString(100, 730, "Date: 2024-01-15")
    c.drawString(100, 710, "Amount: $500")
    c.drawString(100, 690, "Batch: PERF-001")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()


def test_upload_performance(client, sample_pdf):
    """Benchmark upload endpoint"""
    times = []

    for _ in range(10):
        start = time.time()

        files = {"file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")}
        response = client.post("/api/v1/upload", files=files)

        elapsed = time.time() - start
        times.append(elapsed)

        assert response.status_code == 201

    avg_time = sum(times) / len(times)
    print(f"\nUpload average time: {avg_time:.2f}s")
    print(f"Min: {min(times):.2f}s, Max: {max(times):.2f}s")

    # Performance threshold: should complete within 10 seconds
    assert avg_time < 10.0, f"Upload too slow: {avg_time:.2f}s"


def test_verification_lookup_performance(client, sample_pdf):
    """Benchmark verification lookup"""
    # Create a batch first
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")}
    upload_response = client.post("/api/v1/upload", files=files)
    batch_id = upload_response.json()["verification"]["batch_id"]

    # Benchmark lookups
    times = []

    for _ in range(100):
        start = time.time()

        response = client.get(f"/api/v1/verify/{batch_id}")

        elapsed = time.time() - start
        times.append(elapsed)

        assert response.status_code == 200

    avg_time = sum(times) / len(times)
    print(f"\nVerification lookup average time: {avg_time:.4f}s")
    print(f"Min: {min(times):.4f}s, Max: {max(times):.4f}s")

    # Should be fast (< 100ms)
    assert avg_time < 0.1, f"Verification lookup too slow: {avg_time:.4f}s"
