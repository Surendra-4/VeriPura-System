"""
Integration tests for API endpoints.
"""

import io

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Test client for API"""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test /health endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data


def test_upload_valid_pdf(client, sample_pdf_content):
    """Test uploading valid PDF"""
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}

    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 201
    data = response.json()

    # Check response structure
    assert "upload" in data
    assert "validation" in data
    assert "verification" in data

    # Check upload data
    assert data["upload"]["success"] is True
    assert "metadata" in data["upload"]

    # Check validation data
    assert "fraud_score" in data["validation"]
    assert 0 <= data["validation"]["fraud_score"] <= 100

    # Check verification data
    assert "batch_id" in data["verification"]
    assert data["verification"]["batch_id"].startswith("BATCH-")


def test_upload_invalid_file_type(client):
    """Test uploading invalid file type"""
    files = {"file": ("test.exe", io.BytesIO(b"MZ executable"), "application/x-executable")}

    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 400
    assert "error" in response.json()["detail"]


def test_upload_empty_file(client):
    """Test uploading empty file"""
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}

    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 400


def test_verify_existing_batch(client, sample_pdf_content):
    """Test verification lookup for existing batch"""
    # First upload a file
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/v1/upload", files=files)
    batch_id = upload_response.json()["verification"]["batch_id"]

    # Then verify it
    response = client.get(f"/api/v1/verify/{batch_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["batch_id"] == batch_id
    assert "validation_result" in data
    assert "document_metadata" in data


def test_verify_nonexistent_batch(client):
    """Test verification lookup for non-existent batch"""
    response = client.get("/api/v1/verify/BATCH-99999999-FAKE01")

    assert response.status_code == 404


def test_qr_code_generation(client, sample_pdf_content):
    """Test QR code generation"""
    # Upload file
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/v1/upload", files=files)
    batch_id = upload_response.json()["verification"]["batch_id"]

    # Get QR code
    response = client.get(f"/api/v1/qr/{batch_id}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_qr_code_base64(client, sample_pdf_content):
    """Test QR code base64 endpoint"""
    # Upload file
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/v1/upload", files=files)
    batch_id = upload_response.json()["verification"]["batch_id"]

    # Get QR as base64
    response = client.get(f"/api/v1/qr/{batch_id}/base64")

    assert response.status_code == 200
    data = response.json()
    assert "qr_code_base64" in data
    assert len(data["qr_code_base64"]) > 0


def test_ledger_integrity_check(client):
    """Test ledger integrity verification"""
    response = client.get("/api/v1/verify/integrity/check")

    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "total_records" in data


def test_shipment_consistency_graph(client, sample_pdf_content):
    """Test shipment consistency graph endpoint."""
    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    upload_response = client.post("/api/v1/upload", files=files)
    shipment_id = upload_response.json()["verification"]["batch_id"]

    response = client.get(f"/api/v1/shipments/{shipment_id}/consistency-graph")

    assert response.status_code == 200
    data = response.json()
    assert data["shipment_id"] == shipment_id
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
    assert {"field_name", "type", "explanation"}.issubset(data["edges"][0].keys())


def test_shipment_consistency_graph_not_found(client):
    """Test consistency graph lookup for unknown shipment."""
    response = client.get("/api/v1/shipments/SHIPMENT-DOES-NOT-EXIST/consistency-graph")

    assert response.status_code == 404
