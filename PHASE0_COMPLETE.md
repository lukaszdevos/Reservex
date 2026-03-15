# Reservex — Phase 0 Complete: Project Bootstrap

**Date completed:** 2026-03-15
**Branch:** `claude/bootstrap-reservex-pUTNZ` → merged to `main`
**Repo:** `lukaszdevos/Reservex`

---

## What is Reservex

A distributed reservation and payment platform. Built with async Python, Clean Architecture, and production-grade observability from day one.

---

## Phase 0 Summary — What Was Done

Phase 0 was purely infrastructure and tooling. **No business logic was written.** Everything below is scaffolding that all future phases build on.

### 1. Project Structure — Clean Architecture (4 layers)

```
src/
├── domain/              # Layer 1 — entities, domain events, exceptions, repo protocols
│                        #           NO external imports allowed
├── use_cases/           # Layer 2 — business logic, SAGA orchestration, request/response
│                        #           imports: domain + stdlib only
├── adapters/
│   ├── repositories/    # Layer 3 — SQLAlchemy repo implementations
│   └── gateways/        # Layer 3 — Stripe, email, external service clients
└── infrastructure/
    ├── api/
    │   ├── routes/      # Layer 4 — FastAPI route definitions
    │   ├── middleware/  # Layer 4 — rate limiting, auth, logging middleware
    │   └── websockets/  # Layer 4 — WebSocket handlers
    ├── database/        # Layer 4 — SQLAlchemy engine, session factory
    ├── observability/   # Layer 4 — OpenTelemetry, Prometheus, structlog setup
    └── workers/         # Layer 4 — background jobs
tests/
├── unit/
├── integration/
└── load/
```

All layer `__init__.py` files exist but are empty — ready for implementation.

### 2. Dependency Stack

**Package manager:** `uv` (fast, lock-file based)
**Python:** 3.12
**Lock file:** `uv.lock` (frozen, committed)

| Category | Library |
|---|---|
| Web framework | FastAPI 0.111+, Uvicorn 0.29+ |
| Database | SQLAlchemy 2.0+ (asyncio), asyncpg 0.29+, Alembic 1.13+ |
| Cache | Redis 5.0+ (hiredis) |
| Validation | Pydantic 2.7+, pydantic-settings 2.2+ |
| Payments | Stripe (key in .env) |
| Logging | structlog 24.1+ |
| Metrics | prometheus-client 0.20+ |
| Tracing | opentelemetry-sdk 1.24+, opentelemetry-instrumentation-fastapi 0.45+ |
| Rate limiting | slowapi 0.1+ |
| PDF | reportlab 4.1+ |
| Testing | pytest 8.1+, pytest-asyncio 0.23+, testcontainers 4.4+, hypothesis 6.100+, factory-boy 3.3+, locust 2.24+ |
| Quality | ruff 0.4+, mypy 1.10+ (strict) |

### 3. Local Dev Stack — Docker Compose

`make dev` → starts Postgres + Redis only (fast iteration)
`make dev-full` → starts full observability stack

| Service | Image | Port |
|---|---|---|
| PostgreSQL | postgres:16 | 5432 |
| Redis | redis:7-alpine (AOF persistence) | 6379 |
| Prometheus | prom/prometheus:latest | 9090 |
| Grafana | grafana/grafana:latest | 3000 (admin/admin) |
| Jaeger | jaegertracing/all-in-one:latest | 16686 (UI), 4317 (OTLP) |

### 4. CI Pipeline — GitHub Actions (`ci.yml`)

Runs on every push and PR. Four parallel jobs:

| Job | Command | Notes |
|---|---|---|
| lint | `uv run ruff check .` | Rules: E, F, I, UP, B, SIM |
| typecheck | `uv run mypy src/` | Strict mode |
| unit-tests | `uv run pytest tests/unit` | Exits cleanly if no tests yet |
| integration-tests | `uv run pytest tests/integration` | Spins up Postgres 16 + Redis 7 as services |

All jobs pass green (unit/integration skip gracefully when empty).

### 5. Deploy Pipeline — GitHub Actions (`deploy.yml`)

Runs on push to `main` only. Deploys via Railway CLI.

**Status:** Deploy job fails — Railway project token not yet configured.
**This is not blocking.** Nothing real to deploy yet. Fix in Phase 1 when first endpoint exists:
- Create a project on Railway
- Generate a **project-scoped** token (Project Settings → Tokens)
- Set `RAILWAY_TOKEN` secret in GitHub with that token

### 6. Makefile Commands

```
make dev        # docker compose up postgres + redis
make dev-full   # docker compose up all services
make test       # uv run pytest tests/unit
make test-all   # uv run pytest tests/
make lint       # ruff check + mypy
make format     # ruff format
make migrate    # alembic upgrade head
make down       # docker compose down
```

### 7. Environment Variables

Copy `.env.example` to `.env` for local development:

```
DATABASE_URL=postgresql+asyncpg://reservex:reservex@localhost:5432/reservex
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=sk_test_placeholder
ENVIRONMENT=development
LOG_LEVEL=INFO
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 8. Docker Image

Multi-stage build in `Dockerfile`:
- **Builder stage:** installs deps via `uv sync --frozen --no-dev`
- **Runtime stage:** copies `.venv` + `src/`, runs `uvicorn src.infrastructure.api.main:app`

Entry point: `src/infrastructure/api/main:app` — **this file does not exist yet**, create it in Phase 1.

---

## What Does NOT Exist Yet

- No domain entities
- No database models
- No Alembic migrations (alembic initialized but empty)
- No API routes
- No `src/infrastructure/api/main.py` (FastAPI app entry point)
- No repository implementations
- No tests
- No Railway project linked

---

## Starting Phase 1

When you open a new chat, provide this file as context and tell Claude:

> "Phase 0 is complete. See PHASE0_COMPLETE.md for full context. Now implement Phase 1: [describe what you want built first — e.g. user auth, reservation entity, first API endpoint, etc.]"

The architecture is ready. Start with:
1. `src/infrastructure/api/main.py` — FastAPI app factory
2. `src/infrastructure/database/` — SQLAlchemy engine + session
3. First domain entity in `src/domain/`
4. First Alembic migration
5. First API route and matching test
