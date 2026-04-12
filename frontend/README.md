# ReserveX Dashboard

React/Vite dashboard for the ReserveX backend. It visualizes reservation
contention, SAGA compensation, reservation expiry, WebSocket fan-out, semaphore
limits, and outbox relay activity.

## Stack

- React 19
- TypeScript
- Vite
- Zustand for client state
- TanStack Query for polling dashboard metrics
- Recharts for the throughput chart
- Vitest for frontend tests

## Development

```bash
npm install
npm run dev
```

The Vite dev server proxies these paths to the backend on `localhost:8000`:

- `/api`
- `/ws`
- `/metrics`

Start the backend from the repository root before running scenarios:

```bash
make dev
uv run alembic upgrade head
PYTHONPATH=src uv run uvicorn infrastructure.api.main:app --reload
```

## Verification

```bash
npm run lint
npm test
npm run build
```

The WebSocket parser is tested in `src/hooks/wsMessages.test.ts`. Production
build output is served by the FastAPI app when the Docker image copies
`frontend/dist` to `/app/static`.
