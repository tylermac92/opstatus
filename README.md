# opstatus

Service Health & Incident Tracking API — a production-grade FastAPI backend.

## Local Setup

1. Create and activate a virtual environment: `python -m venv .venv && source .venv/bin/activate`
2. Install dependencies: `pip install -e ".[dev]"`
3. Copy config: `cp .env.example .env`
4. Run migrations: `alembic upgrade head`
5. Start the server: `uvicorn app.main:app --reload`

## Architecture

The app is structured in four layers: Router → Service → Repository → Models.
No layer imports from a layer above it. See the requirements spec for full detail.
