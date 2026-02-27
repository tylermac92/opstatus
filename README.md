# OpStatus

A service health and incident tracking API built with FastAPI. Track operational incidents across your services, manage their lifecycle from investigation to resolution, and derive real-time service health status.

## Features

- **Service management** — Create and manage services with automatically derived health status
- **Incident tracking** — Full CRUD with enforced status lifecycle transitions
- **Incident updates** — Append immutable status updates to build a timeline
- **Service health derivation** — Operational status derived from active incidents and their severity
- **Prometheus metrics** — HTTP request metrics and incident/service gauges exported at `/metrics`
- **Structured logging** — Request-scoped structured logs with correlation IDs
- **Health probes** — Liveness and readiness endpoints for container orchestration

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.133+ |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Database (prod) | PostgreSQL 16 |
| Database (dev/test) | SQLite (aiosqlite) |
| Validation | Pydantic v2 |
| Observability | Prometheus-client, Structlog |
| Testing | pytest, pytest-asyncio, httpx |

## Quick Start

### Docker (recommended)

```bash
docker-compose up --build
```

This starts a PostgreSQL instance, runs migrations, and starts the API server at `http://localhost:8000`.

### Local development

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env       # then edit as needed

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.

## Configuration

All configuration is via environment variables (or a `.env` file).

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./opstatus.db` | Database connection string |
| `LOG_LEVEL` | `INFO` | Logging level |
| `APP_ENV` | `development` | Environment name (`development` or `production`) |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Bind port |

> **Note:** In `production` environment, the interactive API docs (`/docs`, `/redoc`) are disabled.

**PostgreSQL connection string:**
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/opstatus
```

**SQLite connection string (local dev):**
```
DATABASE_URL=sqlite+aiosqlite:///./opstatus.db
```

## API Reference

Interactive documentation is available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`.

### Services

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/services` | List all services |
| `POST` | `/api/v1/services` | Create a service |
| `GET` | `/api/v1/services/{id}` | Get a service with derived health status |
| `PATCH` | `/api/v1/services/{id}` | Update a service |
| `DELETE` | `/api/v1/services/{id}` | Delete a service (blocked if active incidents exist) |

### Incidents

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/incidents` | List incidents (filterable by `status`, `severity`, `service_id`) |
| `POST` | `/api/v1/incidents` | Create an incident (initial status: `investigating`) |
| `GET` | `/api/v1/incidents/{id}` | Get an incident with its full update timeline |
| `PATCH` | `/api/v1/incidents/{id}` | Update incident fields or advance its status |
| `POST` | `/api/v1/incidents/{id}/updates` | Append an immutable status update |
| `POST` | `/api/v1/incidents/{id}/resolve` | Resolve an incident with a final update message |

### Operational

| Method | Path | Description |
|---|---|---|
| `GET` | `/health/live` | Liveness probe — returns 200 if the process is running |
| `GET` | `/health/ready` | Readiness probe — checks database connectivity |
| `GET` | `/metrics` | Prometheus metrics |

## Data Model

### Enums

**`IncidentStatus`** (enforced forward-only lifecycle):
```
investigating → identified → monitoring → resolved
```
Backwards transitions and transitions from `resolved` are rejected with a `409 Conflict`.

**`IncidentSeverity`:** `critical` | `high` | `medium` | `low`

**`ServiceStatus`** (derived, not stored):
```
operational  — no active incidents
degraded     — active incidents with medium or low severity
outage       — any active incident with critical or high severity
```

### Schema

```
services
  id            UUID (PK)
  name          string (unique)
  description   text
  created_at    timestamptz
  updated_at    timestamptz

incidents
  id            UUID (PK)
  title         string
  body          text (Markdown supported)
  severity      enum (critical | high | medium | low)
  status        enum (investigating | identified | monitoring | resolved)
  created_at    timestamptz
  updated_at    timestamptz
  resolved_at   timestamptz

incident_updates
  id            UUID (PK)
  incident_id   UUID (FK → incidents, CASCADE DELETE)
  message       text
  status        enum (same as incidents)
  created_at    timestamptz

service_incidents       — many-to-many join table
  service_id    UUID (FK → services)
  incident_id   UUID (FK → incidents)
```

## Development

### Running tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Verbose output
pytest -v
```

Tests use an in-memory SQLite database and do not require a running PostgreSQL instance.

### Code quality

```bash
# Lint and format
ruff check .
ruff format .

# Type checking (strict mode)
mypy app/
```

### Database migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after changing ORM models
alembic revision --autogenerate -m "description of change"

# Roll back one migration
alembic downgrade -1
```

## Project Structure

```
opstatus/
├── app/
│   ├── main.py               # FastAPI app factory
│   ├── api/
│   │   ├── router.py         # Route aggregation
│   │   └── v1/
│   │       ├── services.py   # Service endpoints
│   │       ├── incidents.py  # Incident endpoints
│   │       ├── health.py     # Health probes
│   │       └── metrics.py    # Prometheus metrics endpoint
│   ├── core/
│   │   ├── config.py         # Environment-based settings
│   │   ├── exceptions.py     # Domain exceptions
│   │   ├── error_handlers.py # Global error handlers
│   │   ├── logging.py        # Structured logging setup
│   │   ├── metrics.py        # Prometheus metric definitions
│   │   └── middleware.py     # Request ID and metrics middleware
│   ├── db/
│   │   ├── session.py        # SQLAlchemy engine and session factory
│   │   └── repositories/     # Data access layer
│   │       ├── base.py
│   │       ├── services.py
│   │       ├── incidents.py
│   │       └── incident_updates.py
│   ├── models/
│   │   ├── enums.py          # Shared enumerations
│   │   ├── orm/              # SQLAlchemy ORM models
│   │   └── schemas/          # Pydantic request/response schemas
│   └── services/             # Business logic layer
│       ├── services.py       # Service operations and status derivation
│       └── incidents.py      # Incident operations and transition validation
├── alembic/                  # Migration scripts
├── tests/
│   ├── unit/                 # Pure business logic tests
│   └── integration/          # API-level tests with real DB
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```
