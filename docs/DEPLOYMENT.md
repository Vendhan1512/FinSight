# FinSight Deployment Guide

## 1. Environment Setup
1. Clone the repository.
2. Initialize the Python virtual environment (`python -m venv .venv`).
3. Install dependencies (`pip install -r requirements.txt` or equivalent).

## 2. Configuration
1. Copy `.env.template` to `.env`.
2. Populate `.env` with production database credentials, JWT secrets, and provider API keys.

## 3. Database Initialization
1. Ensure the PostgreSQL cluster is running.
2. Run Alembic migrations: `alembic upgrade head`.

## 4. Execution
- **API**: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4`
- **Frontend**: Run `npm run build` in `frontend/` and serve via Nginx or equivalent.
- **Cron Jobs**: Map `cli.py` commands (`ingest all`, `monitor all`, `pipeline run`) to the production job scheduler.
