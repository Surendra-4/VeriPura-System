
# VeriPura Backend

Production-grade supply chain document verification system with AI-based fraud detection and a blockchain-inspired immutable ledger.

---

## Overview

**VeriPura** is a backend service designed to verify supply chain documents, detect fraud patterns using ML-based anomaly detection, and ensure auditability through cryptographic hash chaining. It also provides QR-based traceability for physical product tracking.

---

## Features

- **AI Validation** — ML-based anomaly detection with explainability
- **Immutable Ledger** — Cryptographic hash chaining for tamper detection
- **QR Traceability** — Generate QR codes for physical product tracking
- **High Performance** — Async processing, model pre-loading, caching
- **Fully Tested** — Unit + integration + performance tests
- **API Documentation** — Auto-generated OpenAPI/Swagger docs

---

## Quick Start

### Prerequisites

- Python **3.11+**
- Poetry
- Tesseract OCR (for image processing)

### Installation & Run

Install dependencies:

```bash
poetry install
````

Train the initial model:

```bash
poetry run python scripts/train_model.py
```

Start the server:

```bash
poetry run uvicorn app.main:app --reload
```

---

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/v1/upload` | Upload and validate document |
| GET | `/api/v1/verify/{batch_id}` | Retrieve verification record |
| GET | `/api/v1/qr/{batch_id}` | Download QR code |
| GET | `/health` | Health check |

### API Docs

-   [http://localhost:8000/docs](http://localhost:8000/docs)


---

## Development

### Run Tests

```bash
poetry run pytest tests/ -v
```

### Format Code

```bash
poetry run black app/ scripts/ tests/
```

### Lint Code

```bash
poetry run ruff check app/ scripts/ tests/
```

---

## Retrain Model

Export training data:

```bash
poetry run python scripts/export_training_data.py
```

Train a new model version:

```bash
poetry run python scripts/retrain_model.py --version v2
```

Update your `.env` file:

```bash
MODEL_VERSION=v2
```

---

## Architecture

```text
app/
├── routes/        # API endpoints
├── services/      # Business logic
├── ml/            # ML pipeline (parser, features, models)
├── infra/         # Infrastructure (ledger, storage, QR)
└── schemas/       # Pydantic models
```

---

## Configuration

Environment variables (`.env`):

```bash
# ML
MODEL_VERSION=v1
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Storage
MAX_UPLOAD_SIZE=10485760

# QR
QR_BASE_URL=http://localhost:8000
```

---

## Performance

-   Upload + validation: **< 5s**

-   Verification lookup: **< 100ms**

-   Model loading: **Lazy + pre-loaded at startup**


---

## License

MIT

---