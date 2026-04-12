# ReserveX

ReserveX is a portfolio reservation and payment platform built around async Python,
FastAPI, PostgreSQL, Redis, and a React dashboard. The main goal is to demonstrate
clean backend architecture, concurrency control, transactional reliability patterns,
and a usable full-stack demo.

## What It Demonstrates

- Clean Architecture layers: `domain -> use_cases -> adapters -> infrastructure`
- Ticket aggregate with reservation lifecycle and domain events
- PostgreSQL `SELECT FOR UPDATE` plus optimistic version checks
- Transactional outbox writes in the same transaction as ticket changes
- Redis Streams outbox relay for at-least-once event publishing
- Reservation expiry worker that releases expired seats through the aggregate
- SAGA orchestration with compensating transactions for payment failure
- FastAPI app with structured logging, Prometheus metrics, OpenTelemetry setup,
  rate limiting, idempotency middleware, and WebSocket fan-out
- React/Vite dashboard with typed WebSocket message parsing and scenario controls
- Unit, integration, frontend, and load-smoke test coverage

## Architecture

```text
src/domain          pure domain model, events, exceptions, protocols
src/use_cases       application workflows and SAGA orchestration
src/adapters        repository and gateway implementations
src/infrastructure  FastAPI, database, observability, workers
frontend            React dashboard
tests               unit, integration, and load-smoke tests
```

The default local API wiring uses mock/stub payment and notification gateways so
the project can run without external accounts. A Stripe adapter exists in
`src/adapters/gateways/stripe_gateway.py`, but production payment wiring is not
enabled by default.

## Local Setup

```bash
cp .env.example .env
make dev
uv run alembic upgrade head
PYTHONPATH=src uv run uvicorn infrastructure.api.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown by `npm run dev`. The frontend proxies `/api`, `/ws`,
and `/metrics` to the backend on `localhost:8000`.

For the full Docker stack:

```bash
make dev-full
```

This starts the API, PostgreSQL, Redis, Prometheus, Grafana, and Jaeger.

## Verification

Backend:

```bash
uv run ruff check .
uv run mypy src/
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest tests/load -q
```

Frontend:

```bash
cd frontend
npm run lint
npm test
npm run build
```

Manual load profile:

```bash
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```

Set `RESERVEX_LOAD_EVENT_ID` and `RESERVEX_LOAD_TICKET_IDS` when targeting seeded
ticket data.

## Current Scope

ReserveX is a strong backend/concurrency portfolio project with a frontend demo.
It is not a complete commercial ticketing product yet. Known non-goals in the
current version include user authentication, a real checkout UI, production
Stripe credential wiring, and database migrations on container startup.
