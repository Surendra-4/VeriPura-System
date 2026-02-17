# VeriPura System

AI-powered food compliance verification platform with tamper-evident records, shipment consistency graphing, and modern authentication.

VeriPura is built to address one hard problem: **trust in global food trade documentation**.

Instead of relying only on manual review or only on ledger storage, this system combines:
- machine-learning document risk scoring,
- structured entity extraction,
- immutable hash-chained verification records,
- QR-based public verification,
- and authenticated workflow access (email/password + Google OAuth).

---

## Why This Project Exists

Food supply chains are paperwork-heavy and fragmented. A single shipment can involve invoices, certificates, and compliance documents created by different parties and reviewed under time pressure.

That creates three recurring problems:
1. **Fraud and inconsistency risk** in submitted documents.
2. **Slow traceability** when incidents happen.
3. **Low confidence audit trails** across stakeholders.

VeriPura is a practical product prototype that demonstrates how AI validation plus tamper-evident records can reduce those risks in a real workflow.

---

## Current Product Scope (What Is Implemented)

### Core Verification Workflow
- Upload PDF / image / CSV compliance documents.
- Parse and extract text (including OCR fallback).
- Run ML anomaly scoring + rule checks.
- Generate risk output (`fraud_score`, `risk_level`, `is_anomaly`).
- Write verification into hash-chained ledger records.
- Generate QR code for public lookup.

### Shipment Consistency Graph
- Builds a graph from stored extracted entities.
- Graph includes document nodes + entity nodes (`batch_id`, `exporter`, `quantity`, `dates`, `certificate_id`).
- Edge type is `MATCH` or `MISMATCH`, with explicit mismatch explanation.

### Authentication
- Local auth: register/login with bcrypt password hashing.
- JWT access tokens for session auth.
- Google OAuth login:
  - secure code exchange,
  - `id_token` verification against Google JWKS,
  - issuer/audience validation,
  - cached keys for performance.

### Frontend Experience
- Modern auth page (login + signup + Continue with Google).
- Google callback route handling.
- Dashboard showing authenticated user email + role.
- Upload and verification pages integrated with backend APIs.

---

## Live Deployment (Current)

- Frontend (Vercel): `https://veripura-system.vercel.app`
- Backend (Render): `https://veripura-system.onrender.com`

---

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy 2.0 (async)
- Alembic migrations
- PostgreSQL (Render)
- Scikit-learn / NumPy / Pandas
- PyMuPDF + Tesseract OCR
- python-jose (JWT)
- passlib + bcrypt (passwords)
- httpx (Google OAuth/JWKS requests)

### Frontend
- React (Vite)
- React Router
- Axios
- CSS Modules

### Infrastructure
- Render (backend + Postgres)
- Vercel (frontend)

---

## Architecture Overview

```text
User (Web App)
   |
   v
React Frontend (Vercel)
   |
   | REST API
   v
FastAPI Backend (Render)
   |                     \
   |                      \
   v                       v
PostgreSQL (users/auth)   File + Ledger storage (uploads, qr, jsonl ledger)
   |
   v
Auth, user identity, role
```

### Trust Model (Current)
- **Document ingestion + ML scoring** for suspicious patterns.
- **Hash-chained ledger records** for tamper evidence.
- **Public verification endpoint** for external validation by batch ID.

> Note: current ledger is blockchain-inspired and tamper-evident. It is not yet writing to an external public L1 chain in this repository.

---

## API Endpoints

### Health
- `GET /health` - service health check.

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me` (Bearer token)
- `GET /auth/google/login`
- `GET /auth/google/callback?code=...&state=...`

### Verification Flow
- `POST /api/v1/upload`
- `GET /api/v1/verify/{batch_id}`
- `GET /api/v1/verify/integrity/check`
- `GET /api/v1/qr/{batch_id}`
- `GET /api/v1/qr/{batch_id}/base64`
- `GET /api/v1/shipments/{shipment_id}/consistency-graph`

Swagger docs: `http://localhost:8000/docs` (local)

---

## Repository Structure

```text
veripura-system/
├── backend/
│   ├── app/
│   │   ├── auth/         # JWT + Google OAuth helpers
│   │   ├── db/           # SQLAlchemy models/session
│   │   ├── routes/       # FastAPI endpoints
│   │   ├── services/     # business logic
│   │   ├── ml/           # parser/features/pipeline
│   │   └── infra/        # storage, ledger, qr
│   ├── alembic/          # DB migrations
│   ├── scripts/          # model training/export scripts
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── api/
    │   ├── auth/
    │   ├── pages/
    │   └── components/
    └── vercel.json
```

---

## Local Setup

## 1) Backend

```bash
cd backend
poetry install
```

Create `.env` in `backend/` with at least:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<db>?sslmode=require
JWT_SECRET=<long-random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
GOOGLE_CLIENT_ID=<google-client-id>
GOOGLE_CLIENT_SECRET=<google-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback
```

Run migrations:

```bash
poetry run alembic upgrade head
```

Train/load model assets (if needed):

```bash
poetry run python scripts/train_model.py
```

Start API:

```bash
poetry run uvicorn app.main:app --reload
```

---

## 2) Frontend

```bash
cd frontend
npm install
```

Create `.env` in `frontend/`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Start frontend:

```bash
npm run dev
```

---

## Environment Variables (Backend)

### Required
- `DATABASE_URL`
- `JWT_SECRET`

### Recommended
- `JWT_ALGORITHM` (default `HS256`)
- `JWT_EXPIRE_MINUTES` (default `1440`)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

### Operational
- `CORS_ORIGINS`
- `ENVIRONMENT`
- `DEBUG`
- `QR_BASE_URL`
- `TESSERACT_CMD`

---

## Deployment Notes

### Render (Backend)
- Docker-based deployment (`backend/Dockerfile`).
- App binds dynamically to `${PORT}` (Render requirement).
- Ensure Render env vars include DB, JWT, and Google OAuth keys.

### Vercel (Frontend)
- Uses `frontend/vercel.json` rewrites for:
  - API proxy (`/api/*` -> backend)
  - health proxy
  - SPA fallback (`/(.*)` -> `/`) to support routes like `/auth/google/callback`.

---

## Google OAuth Setup (Quick Checklist)

In Google Cloud Console:
1. Create OAuth Web Client credentials.
2. Set authorized redirect URI(s):
   - `https://veripura-system.vercel.app/auth/google/callback`
   - `http://localhost:5173/auth/google/callback` (local)
3. Put credentials in backend env vars:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`

---

## Data, Security, and Integrity

- Passwords are stored as bcrypt hashes (never plaintext).
- JWT tokens are signed using a required server secret.
- Google login uses signed token verification (JWKS + issuer/audience checks).
- Verification records are hash-chained for tamper evidence.
- Public verification endpoint is intentionally unauthenticated for traceability by batch ID.

---

## Testing & Quality

Backend:
```bash
cd backend
poetry run pytest
poetry run ruff check app tests
```

Frontend:
```bash
cd frontend
npm run lint
npm run build
```

---

## Product Status

This repository represents an advanced MVP / pre-production system suitable for demos, pilot onboarding, and investor conversations.

High-value next steps for production hardening:
- stricter RBAC policy and protected admin endpoints,
- stronger observability and alerting,
- ledger anchoring to external chain/network,
- model evaluation dashboard with drift monitoring,
- SLA-aware background job orchestration.

---

## Disclaimer

This software supports compliance workflows and fraud risk triage. It is not legal advice and should not be the sole source of regulatory decision-making.

---

## Contact

If you're evaluating VeriPura for pilot or collaboration, open an issue or reach out through the project owner’s preferred channel.
