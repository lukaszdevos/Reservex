# ReserveX — Master Briefing Document

### Distributed Reservation & Payment Platform

> **How to use this document:** Paste it at the start of every Claude Code session.
> Claude Code reads it once, then implements tasks from the TODO list at the bottom.
> Work one phase at a time. Every task = one commit. Every phase = runnable system.

-----

# PART 1 — HOW CLAUDE CODE SHOULD WORK

## 1.1 Session Start Protocol

At the beginning of every session, Claude Code must:

1. Read this entire document before writing any code
1. Ask: *"Which phase and task from the TODO list are we working on?"*
1. Confirm understanding of the task in one sentence before starting
1. Never start a new task without finishing and committing the current one

## 1.2 Coding Rules

**Python style**

- Python 3.12+ — use modern syntax: `X | Y` unions, `match`, `type` aliases
- All functions and methods must have type annotations — no exceptions
- Use `from __future__ import annotations` at the top of every file
- Prefer `dataclass` over plain classes for data containers
- Use `Protocol` for interfaces, never `ABC`
- Maximum function length: 30 lines. If longer, split it.
- No commented-out code in commits — delete it

**Imports — Clean Architecture rule**

- `domain/` → imports only Python stdlib
- `use_cases/` → imports only `domain/` and stdlib
- `adapters/` → imports `domain/`, `use_cases/`, and third-party libs
- `infrastructure/` → imports everything
- Claude Code must verify this rule before every commit

**Bounded Context rule (Cosmic Python)**

- `domain/` is organised into bounded contexts: `ticketing/`, `payment/`, `shared/`, `outbox/`
- Each context owns its own model, events, exceptions, and repository Protocol
- Cross-context communication happens only through domain events — never direct imports between contexts (except `shared/`)
- One repository per aggregate root — repositories only return aggregates, never child entities
- Aggregate roots collect domain events in `self.events: list[DomainEvent]`; the Unit of Work publishes them after commit
- Repository API uses `add()` / `get()` naming (Cosmic Python convention)

**Async rules**

- Every function that touches I/O must be `async`
- Never use `time.sleep()` — always `asyncio.sleep()`
- Never call blocking code in the event loop — use `run_in_executor()`
- Always use `asyncio.timeout()` not `asyncio.wait_for()` (Python 3.11+)
- Use `asyncio.TaskGroup` not `asyncio.gather()` when tasks must all succeed

**Error handling**

- Domain exceptions live in the bounded context that owns them (e.g. `src/domain/ticketing/exceptions.py`)
- Never catch bare `Exception` in domain or use case layers
- Infrastructure layer catches and translates exceptions to HTTP responses
- Always log with `structlog` — never with `print()`

## 1.3 Commit Rules

Every commit must:

- Contain exactly one logical change (one checkbox from TODO)
- Pass `uv run ruff check .` before committing
- Pass `uv run pytest tests/unit -v` before committing (once tests exist)
- Follow this message format:

```
feat(domain): add Ticket entity with reserve/release methods
feat(usecase): implement ReserveTicketUseCase with timeout
feat(adapter): add PostgresTicketRepository with pessimistic lock
feat(infra): wire FastAPI routes and DI for reservation flow
feat(frontend): add SeatMap component with WebSocket updates
test(integration): add race condition test with 50 concurrent requests
fix(adapter): release Redis lock using Lua atomic script
docs(adr): document optimistic locking default decision
ci: add GitHub Actions workflow
```

Format: `type(scope): description` — lowercase, no period at end.

## 1.4 File Creation Rules

- Never create a file without a corresponding test (for domain and use case layers)
- Every new module gets a docstring explaining what layer it belongs to and what it does
- Every new `Protocol` gets a comment explaining which concrete class implements it
- `.env` values are never hardcoded — always read from `pydantic-settings`

## 1.5 After Every Task

Before marking a task done, Claude Code must run:

```bash
uv run ruff check .          # must pass with zero errors
uv run mypy src/             # must pass (warnings OK, errors not)
uv run pytest tests/unit -v  # must pass
git add -p                   # review every change before staging
git commit -m "..."          # one commit per task
git push origin main         # triggers CI on GitHub
```

Then confirm: *"Task complete. CI triggered. Move to next task?"*

## 1.6 What Claude Code Should Never Do

- Never skip writing tests for domain and use case code
- Never import SQLAlchemy or FastAPI in `domain/` or `use_cases/`
- Never use `asyncio.sleep(0)` as a workaround — fix the root cause
- Never hardcode ports, passwords, or URLs — use `.env`
- Never commit `uv.lock` changes without running `uv sync` first
- Never create a new file without adding it to the correct layer
- Never write a use case that knows about HTTP status codes

-----

# PART 2 — PRE-PHASE-0 SETUP

> Complete these steps **before** writing any application code.
> Everything done on phone browser + one Claude Code session.
> Estimated time: ~30 minutes.

## Step 1 — GitHub Repository (phone browser)

- [ ] Go to github.com → sign in
- [ ] Click **New repository** → name: `reservex` → **Public**
- [ ] Check **Add a README file** and **Add .gitignore → Python**
- [ ] Click **Create repository**
- [ ] Copy repo URL: `https://github.com/<your-handle>/reservex.git`

## Step 2 — Railway Account (phone browser)

- [ ] Go to railway.app → **Login with GitHub** → authorize
- [ ] Click **New Project** → **Deploy from GitHub repo** → select `reservex`
- [ ] Railway says "No config found" — that is expected at this stage
- [ ] Go to **Settings** → **Generate Domain** → copy and save the URL
- [ ] Note: free tier gives $5 credit/month (~$0.10–0.20/day for this stack)

## Step 3 — Railway Placeholder Config (Claude Code)

Railway needs a start command or it will fail looking for `start.sh`.
Ask Claude Code to create these two files:

```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "echo 'ReserveX: app not deployed yet'"
restartPolicyType = "never"
```

```
# Procfile
web: echo "ReserveX placeholder"
```

Then: `git add . && git commit -m "ci: add Railway placeholder config" && git push`

## Step 4 — CI Infrastructure (Claude Code)

Ask Claude Code to create the full CI stack with this prompt:

```
Create the following files. No application code yet — CI infrastructure only.

Files to create:
- .github/workflows/ci.yml
- .github/workflows/deploy.yml
- docker-compose.yml
- infrastructure/prometheus/prometheus.yml
- Makefile
- .env.example
- pyproject.toml
- src/.gitkeep
- tests/unit/.gitkeep
- tests/integration/.gitkeep
- tests/load/.gitkeep

ci.yml requirements:
- Triggers on every push and pull_request
- Jobs: lint, typecheck, unit-tests, integration-tests
- lint: uv run ruff check .
- typecheck: uv run mypy src/ --ignore-missing-imports
- unit-tests: uv run pytest tests/unit -v --tb=short
- integration-tests: GitHub Actions services postgres:16 and redis:7 with
  healthchecks, then uv run pytest tests/integration -v --tb=short
- Use astral-sh/setup-uv@v3 to install uv
- Cache .venv between runs

deploy.yml requirements:
- Triggers on push to main only
- Installs Railway CLI and runs: railway up --detach
- Requires RAILWAY_TOKEN secret

docker-compose.yml services:
- postgres: image postgres:16, port 5432, POSTGRES_PASSWORD=reservex,
  POSTGRES_DB=reservex, POSTGRES_USER=reservex, healthcheck pg_isready
- redis: image redis:7-alpine, port 6379,
  command redis-server --appendonly yes, healthcheck redis-cli ping
- prometheus: image prom/prometheus:latest, port 9090
- grafana: image grafana/grafana:latest, port 3000,
  GF_SECURITY_ADMIN_PASSWORD=admin, GF_AUTH_ANONYMOUS_ENABLED=true
- jaeger: image jaegertracing/all-in-one:latest, ports 16686 and 4317
- All on network: reservex-network

Makefile targets:
  make dev       → docker compose up -d postgres redis
  make dev-full  → docker compose up -d
  make test      → uv run pytest tests/unit -v
  make test-all  → uv run pytest tests/ -v
  make lint      → uv run ruff check . && uv run mypy src/
  make format    → uv run ruff format .
  make migrate   → uv run alembic upgrade head
  make down      → docker compose down

.env.example variables:
  DATABASE_URL=postgresql+asyncpg://reservex:reservex@localhost:5432/reservex
  REDIS_URL=redis://localhost:6379
  STRIPE_SECRET_KEY=sk_test_placeholder
  ENVIRONMENT=development
  LOG_LEVEL=INFO
  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

pyproject.toml:
  [project] name=reservex, version=0.1.0, requires-python>=3.12, dependencies=[]
  [tool.ruff.lint] select=["E","F","I","UP","B","SIM"]
  [tool.mypy] strict=true, ignore_missing_imports=true
  [tool.pytest.ini_options] asyncio_mode="auto", testpaths=["tests"]
```

## Step 5 — Railway Token Secret (phone browser)

- [ ] Go to railway.app → Account Settings → Tokens → **New Token** → name: `github-actions` → copy
- [ ] Go to github.com → repo → Settings → Secrets and variables → Actions
- [ ] Click **New repository secret** → Name: `RAILWAY_TOKEN` → paste token → Save

## Step 6 — Verify Full Loop

**In Claude Code:**

```bash
make dev                          # postgres + redis start
uv run pytest tests/unit -v       # "no tests ran" — exit 0 ✅
uv run ruff check .               # zero errors ✅
git push origin main              # triggers CI
```

**On phone browser:**

- [ ] github.com → Actions tab → all jobs green ✅
- [ ] railway.app → deployment succeeded ✅
- [ ] Open Railway URL → any response (even connection refused) ✅

**All 3 green = setup complete. Start Phase 0.**

-----

# PART 3 — PROJECT SPECIFICATION

## 3.1 What ReserveX Is

A production-grade distributed reservation and payment system that demonstrates:

- Advanced Python concurrency (asyncio, threading, multiprocessing)
- Distributed systems reliability (SAGA, Outbox, Idempotency, Distributed Locks)
- Clean Architecture in Python (Giordani) — domain free of all frameworks
- Three locking strategies compared side-by-side
- Interactive demo UI where every mechanism is visually triggerable

**Target audience for the portfolio:** Senior engineers and tech leads at fintech / e-commerce companies who recognise these patterns from production systems.

## 3.2 Tech Stack

| Layer | Technology |
|---|---|
| Dependency management | uv |
| Language | Python 3.12 |
| API framework | FastAPI |
| Database | PostgreSQL 16 (async via asyncpg) |
| ORM | SQLAlchemy 2.0 (async) |
| Cache / locks | Redis 7 |
| Migrations | Alembic |
| Background tasks | asyncio (native) |
| PDF generation | ReportLab (ProcessPool) |
| Email | SMTP (ThreadPool) |
| Observability | structlog + Prometheus + OpenTelemetry |
| Frontend | React 18 + TypeScript + Vite |
| Real-time | WebSocket (FastAPI native) |
| Testing | pytest-asyncio + testcontainers + hypothesis + locust |
| Linting | ruff + mypy |
| CI | GitHub Actions |
| Deployment | Railway |

-----

# PART 4 — CLEAN ARCHITECTURE

## 4.1 The Dependency Rule

Source code dependencies must point **inward only**. Inner layers know nothing about outer layers.

```
┌──────────────────────────────────────────┐
│  INFRASTRUCTURE  (FastAPI, SQLAlchemy,   │
│  Redis client, Stripe SDK, Celery)       │
│  ┌────────────────────────────────────┐  │
│  │  ADAPTERS  (Repository impls,      │  │
│  │  serializers, gateways)            │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │  USE CASES  (SAGA, business  │  │  │
│  │  │  rules, interactors)         │  │  │
│  │  │  ┌────────────────────────┐  │  │  │
│  │  │  │  DOMAIN  (Entities,    │  │  │  │
│  │  │  │  Events, Exceptions,   │  │  │  │
│  │  │  │  Repository Protocols) │  │  │  │
│  │  │  └────────────────────────┘  │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

## 4.2 Project Structure

```
reservex/
├── pyproject.toml          # uv project + all tool config
├── uv.lock                 # universal lockfile — always commit this
├── docker-compose.yml
├── railway.toml
├── Makefile
│
├── src/
│   ├── domain/             # LAYER 1 — zero external imports, DDD bounded contexts
│   │   ├── shared/         # Shared kernel (used by all contexts)
│   │   │   ├── event.py    # DomainEvent base dataclass
│   │   │   └── gateways.py # NotificationGateway, DistributedLockGateway (Protocol)
│   │   ├── ticketing/      # Ticketing bounded context
│   │   │   ├── model.py    # Ticket (aggregate root) + Reservation (child entity) + TicketStatus
│   │   │   ├── events.py   # TicketReserved, TicketReleased, TicketConfirmed
│   │   │   ├── exceptions.py  # TicketAlreadyTaken, OptimisticLockConflict, etc.
│   │   │   └── repository.py  # TicketRepository Protocol (add/get/get_for_update)
│   │   ├── payment/        # Payment bounded context
│   │   │   ├── events.py   # PaymentCompleted, PaymentFailed
│   │   │   ├── exceptions.py  # PaymentDeclinedError
│   │   │   └── gateway.py  # PaymentGateway Protocol (charge/refund)
│   │   └── outbox/         # Transactional outbox context
│   │       └── repository.py  # OutboxRepository Protocol
│   │
│   ├── use_cases/          # LAYER 2 — imports domain/ only
│   │   ├── reserve_ticket.py
│   │   ├── release_ticket.py
│   │   ├── saga.py         # TicketPurchaseSaga orchestrator
│   │   ├── validators.py   # parallel asyncio.TaskGroup validations
│   │   ├── request_objects.py
│   │   └── response_objects.py
│   │
│   ├── adapters/           # LAYER 3 — imports domain + use_cases
│   │   ├── repositories/
│   │   │   ├── postgres_ticket_repo.py
│   │   │   └── memory_ticket_repo.py   # for tests
│   │   ├── gateways/
│   │   │   ├── stripe_gateway.py       # Semaphore-guarded
│   │   │   ├── mock_payment_gateway.py # for tests
│   │   │   └── redis_gateway.py        # distributed lock
│   │   ├── serializers.py
│   │   └── presenters.py
│   │
│   └── infrastructure/     # LAYER 4 — wires everything together
│       ├── api/
│       │   ├── main.py          # FastAPI app factory + lifespan
│       │   ├── dependencies.py  # DI: inject repos + gateways
│       │   ├── middleware/
│       │   │   ├── idempotency.py
│       │   │   └── rate_limit.py
│       │   ├── routes/
│       │   │   ├── tickets.py
│       │   │   └── payments.py
│       │   └── websockets/
│       │       └── seat_map.py
│       ├── database/
│       │   ├── models.py        # SQLAlchemy ORM models
│       │   ├── session.py       # async session factory
│       │   └── migrations/      # Alembic
│       ├── workers/
│       │   ├── outbox_relay.py  # asyncio background task
│       │   ├── cpu_worker.py    # ProcessPoolExecutor
│       │   └── io_worker.py     # ThreadPoolExecutor
│       └── observability/
│           ├── logging.py
│           ├── metrics.py
│           └── tracing.py
│
└── tests/
    ├── unit/               # no DB, no Redis
    │   ├── domain/
    │   └── use_cases/
    ├── integration/        # testcontainers
    └── load/               # locust
```

## 4.3 Key Code Patterns

**Aggregate root — collects domain events, owns child entities:**

```python
# src/domain/ticketing/model.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from domain.shared.event import DomainEvent
from domain.ticketing.events import TicketReserved, TicketReleased, TicketConfirmed
from domain.ticketing.exceptions import TicketAlreadyTakenError

RESERVATION_TTL: timedelta = timedelta(minutes=5)

@dataclass
class Reservation:          # child entity — never instantiate outside Ticket
    ticket_id: int
    user_id: int
    created_at: datetime
    expires_at: datetime
    id: int = 0

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

@dataclass
class Ticket:               # aggregate root
    id: int
    event_id: int
    seat_number: str
    status: TicketStatus = field(default=TicketStatus.AVAILABLE)
    reserved_by: int | None = field(default=None)
    version: int = field(default=0)
    reservation: Reservation | None = field(default=None)
    events: list[DomainEvent] = field(default_factory=list)

    def reserve(self, user_id: int) -> Reservation:
        if self.status != TicketStatus.AVAILABLE:
            raise TicketAlreadyTakenError(self.id)
        now = datetime.now(UTC)
        self.status = TicketStatus.RESERVED
        self.reserved_by = user_id
        self.version += 1
        self.reservation = Reservation(
            ticket_id=self.id, user_id=user_id,
            created_at=now, expires_at=now + RESERVATION_TTL,
        )
        self.events.append(TicketReserved(ticket_id=self.id, user_id=user_id))
        return self.reservation
```

**Repository interface — Protocol, add/get naming (Cosmic Python):**

```python
# src/domain/ticketing/repository.py
from typing import Protocol
from domain.ticketing.model import Ticket

class TicketRepository(Protocol):
    async def add(self, ticket: Ticket) -> None: ...          # insert or update
    async def get(self, ticket_id: int) -> Ticket | None: ...
    async def get_for_update(self, ticket_id: int) -> Ticket | None: ...
```

**Use case — imports domain only:**

```python
# src/use_cases/reserve_ticket.py
from dataclasses import dataclass
from domain.ticketing.repository import TicketRepository
from domain.ticketing.exceptions import TicketAlreadyTakenError

@dataclass
class ReserveTicketRequest:
    ticket_id: int
    user_id: int
    idempotency_key: str

class ReserveTicketUseCase:
    def __init__(self, ticket_repo: TicketRepository) -> None:
        self._repo = ticket_repo

    async def execute(self, request: ReserveTicketRequest) -> UseCaseResponse:
        ticket = await self._repo.get_for_update(request.ticket_id)
        if ticket is None:
            return UseCaseResponse(success=False, message="Ticket not found")
        try:
            reservation = ticket.reserve(request.user_id)   # aggregate creates child
            await self._repo.add(ticket)                     # saves ticket + reservation
            return UseCaseResponse(success=True, message="Reserved")
        except TicketAlreadyTakenError as exc:
            return UseCaseResponse(success=False, message=str(exc))
```

**Infrastructure DI — only place that imports all layers:**

```python
# src/infrastructure/api/dependencies.py
from adapters.repositories.postgres_ticket_repo import PostgresTicketRepository
from use_cases.reserve_ticket import ReserveTicketUseCase
from infrastructure.database.session import get_session

async def get_reserve_use_case(
    session: AsyncSession = Depends(get_session),
) -> ReserveTicketUseCase:
    repo = PostgresTicketRepository(session)
    return ReserveTicketUseCase(ticket_repo=repo)
```

-----

# PART 5 — UV DEPENDENCY MANAGEMENT

## 5.1 Key Commands

```bash
# Project setup
uv init reservex --python 3.12
uv add fastapi uvicorn[standard]
uv add sqlalchemy[asyncio] asyncpg
uv add redis[hiredis] pydantic pydantic-settings
uv add structlog prometheus-client
uv add opentelemetry-sdk opentelemetry-instrumentation-fastapi
uv add reportlab slowapi alembic

uv add --dev pytest pytest-asyncio anyio[trio] ruff mypy
uv add --dev testcontainers[postgres,redis] factory-boy hypothesis locust

# Daily use — no venv activation needed
uv run uvicorn src.infrastructure.api.main:app --reload
uv run pytest tests/unit -v
uv run ruff check .
uv run mypy src/

# Lock and sync
uv lock    # regenerate uv.lock
uv sync    # install all deps from uv.lock
```

## 5.2 pyproject.toml Template

```toml
[project]
name = "reservex"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "redis[hiredis]>=5.0",
    "pydantic>=2.7",
    "pydantic-settings>=2.2",
    "structlog>=24.1",
    "prometheus-client>=0.20",
    "opentelemetry-sdk>=1.24",
    "opentelemetry-instrumentation-fastapi>=0.45",
    "reportlab>=4.1",
    "slowapi>=0.1",
    "alembic>=1.13",
]

[dependency-groups]
dev = [
    "pytest>=8.1",
    "pytest-asyncio>=0.23",
    "anyio[trio]>=4.3",
    "testcontainers[postgres,redis]>=4.4",
    "hypothesis>=6.100",
    "locust>=2.24",
    "factory-boy>=3.3",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
strict = true
ignore_missing_imports = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## 5.3 Dockerfile with uv

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
COPY src/ /app/src/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "src.infrastructure.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

-----

# PART 6 — CONCURRENCY ARCHITECTURE

## 6.1 Mechanism Map

| Problem | Mechanism | Layer | Reason |
|---|---|---|---|
| 1000 users, 1 ticket | asyncio + FOR UPDATE | Adapter | DB lock in repo; use case stays clean |
| Parallel validations | asyncio.TaskGroup | Use Cases | Fail-fast; cancels peers on first error |
| Reservation timeout | asyncio.timeout() | Use Cases | Cooperative cancel, no polling |
| WS seat map | asyncio.gather() | Infrastructure | Fan-out to all clients in parallel |
| Stripe rate limit | asyncio.Semaphore | Adapters | Cap calls in the gateway layer |
| PDF generation | ProcessPoolExecutor | Infrastructure | CPU-bound, bypasses GIL |
| SMTP / sync SDK | ThreadPoolExecutor | Infrastructure | Blocking lib, keeps event loop free |
| Outbox relay | asyncio background task | Infrastructure | Long-running coroutine in lifespan |

## 6.2 Pattern Examples

**asyncio.gather() — parallel DB queries:**

```python
async def prepare_checkout(self, ticket_id: int, user_id: UUID) -> CheckoutContext:
    ticket, user, history = await asyncio.gather(
        self._ticket_repo.get(ticket_id),
        self._user_repo.get(user_id),
        self._purchase_repo.get_history(user_id),
    )
    return CheckoutContext(ticket, user, history)
```

**asyncio.TaskGroup — fail-fast validation:**

```python
async def run_validations(self, ctx: SagaContext) -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(self._validate_ticket_available(ctx.ticket_id))
        tg.create_task(self._validate_user_not_blacklisted(ctx.user_id))
        tg.create_task(self._validate_payment_method(ctx.payment_method_id))
    # Raises ExceptionGroup on first failure; remaining tasks cancelled
```

**asyncio.timeout() — reservation expiry:**

```python
async def execute_with_timeout(self, request: ReserveTicketRequest) -> None:
    try:
        async with asyncio.timeout(300):
            await self._saga.execute(request)
    except TimeoutError:
        await self._ticket_repo.release(request.ticket_id)
        await self._notifier.send_expiry(request.user_id)
```

**asyncio.Semaphore — Stripe rate guard:**

```python
class StripeGateway:
    _semaphore = asyncio.Semaphore(10)

    async def charge(self, amount_cents: int, payment_method: str) -> ChargeResult:
        async with self._semaphore:
            return await self._client.charge(amount_cents, payment_method)
```

**ProcessPoolExecutor — PDF generation:**

```python
_process_pool = ProcessPoolExecutor(max_workers=4)

async def generate_ticket_pdf(ticket_dict: dict) -> bytes:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_process_pool, _render_pdf_sync, ticket_dict)

def _render_pdf_sync(ticket_dict: dict) -> bytes:
    # Top-level function — must be pickle-able
    from reportlab.pdfgen import canvas
    ...
```

**ThreadPoolExecutor — SMTP:**

```python
_thread_pool = ThreadPoolExecutor(max_workers=10)

async def send_email(to: str, subject: str, body: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_thread_pool, _send_smtp_blocking, to, subject, body)
```

-----

# PART 7 — LOCKING STRATEGIES

All three strategies live in the **adapter layer**. The use case selects a strategy via an injected Protocol — it never calls SQLAlchemy or Redis directly.

## 7.1 Pessimistic — SELECT FOR UPDATE

Use when: conflict rate is high, critical section is short, single DB instance.

```python
# src/adapters/repositories/postgres_ticket_repo.py
async def get_for_update(self, ticket_id: int) -> Ticket | None:
    result = await self._session.execute(
        select(TicketModel)
        .where(TicketModel.id == ticket_id)
        .where(TicketModel.status == "available")
        .with_for_update()       # row-level lock until commit
    )
    model = result.scalar_one_or_none()
    return _to_entity(model) if model else None
```

## 7.2 Optimistic — Version Column

Use when: conflict rate is low, read-heavy workload, multiple app instances.

```python
async def save(self, ticket: Ticket) -> None:
    result = await self._session.execute(
        update(TicketModel)
        .where(TicketModel.id == ticket.id)
        .where(TicketModel.version == ticket.version - 1)
        .values(status=ticket.status.value, version=ticket.version)
        .returning(TicketModel.id)
    )
    if not result.scalar():
        raise OptimisticLockConflict(ticket.id)
```

## 7.3 Distributed — Redis Redlock

Use when: multiple application instances (Kubernetes, Railway replicas).

```python
# src/adapters/gateways/redis_gateway.py
@asynccontextmanager
async def distributed_lock(self, resource: str, ttl_ms: int = 5000):
    key   = f"lock:ticket:{resource}"
    token = str(uuid4())
    acquired = await self._redis.set(key, token, nx=True, px=ttl_ms)
    if not acquired:
        raise LockNotAcquiredError(resource)
    try:
        yield
    finally:
        # Lua script: atomic check-and-delete — never releases another owner's lock
        await self._redis.eval(
            "if redis.call('get',KEYS[1])==ARGV[1] then"
            " return redis.call('del',KEYS[1]) else return 0 end",
            1, key, token,
        )
```

-----

# PART 8 — SAGA PATTERN

SAGA orchestrator lives in `use_cases/`. It depends only on domain Protocols — no SQLAlchemy, no Redis, no HTTP.

```
HAPPY PATH:
  1. validate_user      ✓ → proceed
  2. reserve_ticket     ✓ → proceed
  3. charge_payment     ✓ → proceed
  4. send_confirmation  ✓ → DONE

FAILURE AT STEP 3 (card declined):
  3. charge_payment     ✗ → trigger compensations in reverse
     compensate step 2: release_ticket   (ticket → AVAILABLE)
     compensate step 1: no compensation
  → System in consistent state
```

```python
# src/use_cases/saga.py
@dataclass
class SagaStep:
    name:         str
    action:       Callable[[SagaContext], Awaitable[None]]
    compensation: Callable[[SagaContext], Awaitable[None]] | None

class TicketPurchaseSaga:
    def __init__(
        self,
        ticket_repo:     TicketRepository,
        payment_gateway: PaymentGateway,
        notifier:        NotificationGateway,
    ) -> None:
        self._steps = [
            SagaStep("validate",  self._validate,  None),
            SagaStep("reserve",   self._reserve,   self._release),
            SagaStep("charge",    self._charge,    self._refund),
            SagaStep("notify",    self._notify,    None),
        ]

    async def execute(self, ctx: SagaContext) -> SagaResult:
        executed: list[SagaStep] = []
        for step in self._steps:
            try:
                await step.action(ctx)
                executed.append(step)
            except Exception as exc:
                await self._compensate(ctx, executed)
                return SagaResult.failed(step.name, str(exc))
        return SagaResult.success()

    async def _compensate(
        self, ctx: SagaContext, executed: list[SagaStep]
    ) -> None:
        for step in reversed(executed):
            if step.compensation:
                try:
                    await step.compensation(ctx)
                except Exception as exc:
                    # Best-effort — log critical but continue rollback
                    logger.critical("compensation_failed", step=step.name, error=str(exc))
```

-----

# PART 9 — RELIABILITY PATTERNS

## 9.1 Idempotency Middleware

```python
# src/infrastructure/api/middleware/idempotency.py
class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        key = request.headers.get("Idempotency-Key")
        if key:
            cached = await self._redis.get(f"idempotency:{key}")
            if cached:
                return JSONResponse(json.loads(cached))
        response = await call_next(request)
        if key and response.status_code == 200:
            body = b"".join([chunk async for chunk in response.body_iterator])
            await self._redis.setex(f"idempotency:{key}", 86400, body)
            return Response(content=body, media_type=response.media_type)
        return response
```

## 9.2 Transactional Outbox

```python
# Same DB transaction: state change + outbox record
async def confirm_ticket(ticket_id: int, session: AsyncSession) -> None:
    async with session.begin():
        ticket.status = "confirmed"
        session.add(OutboxMessage(
            event_type="ticket.confirmed",
            payload={"ticket_id": ticket_id},
            published=False,
        ))
        # commit: both writes or neither

# Background relay worker
async def outbox_relay_worker(session_factory, event_bus) -> None:
    while True:
        async with session_factory() as session:
            msgs = (await session.execute(
                select(OutboxMessage)
                .where(OutboxMessage.published == False)
                .limit(100)
                .with_for_update(skip_locked=True),  # safe for multiple instances
            )).scalars().all()
            if not msgs:
                await asyncio.sleep(0.1)
                continue
            await asyncio.gather(*[event_bus.publish(m) for m in msgs])
            for m in msgs:
                m.published = True
            await session.commit()
```

## 9.3 WebSocket Broadcaster

```python
# src/infrastructure/api/websockets/seat_map.py
class SeatMapBroadcaster:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, ws: WebSocket, event_id: int) -> None:
        await ws.accept()
        self._connections[event_id].add(ws)

    async def broadcast(self, event_id: int, seat_id: int, status: str) -> None:
        conns   = list(self._connections[event_id])
        payload = {"seat_id": seat_id, "status": status}
        results = await asyncio.gather(
            *[ws.send_json(payload) for ws in conns],
            return_exceptions=True,     # one dead client never crashes broadcast
        )
        dead = [ws for ws, r in zip(conns, results) if isinstance(r, Exception)]
        for ws in dead:
            self._connections[event_id].discard(ws)
```

-----

# PART 10 — FRONTEND DEMO UI

## 10.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER  ReserveX | requests  conflicts  WS-clients  Stripe  ●  │
├────────────────┬────────────────────────────┬───────────────────┤
│  SCENARIOS     │  SEAT MAP (live WebSocket)  │  EVENT LOG        │
│                │  [Stage row]                │                   │
│  ⚡ Race       │  □□□□□□□□□□□□              │  10:42:01 ✓ ...   │
│  ↩  SAGA       │  □□■■□□□□□□□□              │  10:42:02 ✗ ...   │
│  ⏱  Timeout   │  □□□□□□□□□□□□              │  10:42:03 ⚠ ...   │
│  🛡  Semaphore │  □□□□□□■□□□□□              │                   │
│  📡  Broadcast │                             │  legend:          │
│  📬  Outbox    │  success  fail  conflict ms  │  success/error/   │
│                │                             │  warn/db/saga     │
│  [SAGA steps]  │  [Concurrency Layers]        │                   │
│  [timeout bar] │  asyncio ThreadPool Proc    │                   │
│  [semaphore]   │  (highlights active layer)   │                   │
└────────────────┴────────────────────────────┴───────────────────┘
```

## 10.2 Six Demo Scenarios

Each button calls `POST /api/demo/scenarios/{name}` on the real backend.

| Button | Mechanism | What you see |
|---|---|---|
| ⚡ Race Condition | SELECT FOR UPDATE | Seat #42 red; 999/1000 get TicketAlreadyTakenError; counters live |
| ↩ SAGA Rollback | SAGA + compensation | Step tracker; card decline triggers reverse; seat returns to available |
| ⏱ Timeout Expiry | asyncio.timeout() | Progress bar counts down; seat auto-releases on expiry |
| 🛡 Semaphore Guard | asyncio.Semaphore | 10-slot gauge fills; queue depth shown; Stripe never >10 concurrent |
| 📡 WS Broadcast | asyncio.gather() | 500 simulated clients; changes propagate <10ms |
| 📬 Outbox Relay | Transactional Outbox | Step-by-step: DB write + outbox (atomic) → relay → Redis Streams |

## 10.3 Frontend Stack

```
React 18 + TypeScript + Vite
TanStack Query — server state, refetch every 1s for metrics
Recharts — throughput/min LineChart (last 60 points)
react-spring — seat transition animations
Tailwind CSS — dark theme
WebSocket (native hook) — auto-reconnect with exponential backoff
```

-----

# PART 11 — TESTING STRATEGY

## 11.1 Test Types

| Type | Location | Tools | No external deps |
|---|---|---|---|
| Unit | tests/unit/ | pytest-asyncio | in-memory repo |
| Integration | tests/integration/ | testcontainers | real PG + Redis |
| Race condition | tests/integration/ | asyncio.gather() | real PG |
| Property-based | tests/unit/ | hypothesis | yes |
| Load | tests/load/ | locust | live server |

## 11.2 Race Condition Test Pattern

```python
@pytest.mark.asyncio
async def test_only_one_reservation_wins(db_session, redis_client):
    ticket_id = await create_available_ticket(db_session)

    results = await asyncio.gather(
        *[reserve_ticket(ticket_id, user_id=i) for i in range(50)],
        return_exceptions=True,
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 1

    ticket = await ticket_repo.get(ticket_id)
    assert ticket.status == TicketStatus.RESERVED
```

-----

# PART 12 — ARCHITECTURE DECISION RECORDS

| ADR | Decision | Key Reason |
|---|---|---|
| 001 | uv over Poetry | 10-100x faster, universal lockfile, no activation |
| 002 | Clean Architecture layers | Dependency rule enforced at import level |
| 003 | Optimistic lock as default | Most reservations succeed; no DB lock during Stripe call |
| 004 | Transactional Outbox | Eliminates dual-write: event never silently lost |
| 005 | asyncio over Celery | Native coroutines; Celery is not truly async |

Full ADR files live in `docs/adr/` — one markdown file per decision.

-----

# PART 13 — TODO LIST

> One task = one commit. One phase = independently runnable system.
> Check off tasks as you complete them.

-----

## PHASE 0 — Project Bootstrap ✅ COMPLETE

See `PHASE0_COMPLETE.md` for full summary of what was built.

-----

## PHASE 1 — Domain Layer ✅ COMPLETE

> Rule: zero external imports in `src/domain/`. Python stdlib only.
> Structure: DDD bounded contexts — ticketing/, payment/, shared/, outbox/
> Pattern: Cosmic Python aggregate + repository conventions.

### P1.1 — Shared kernel

- [x] `src/domain/shared/event.py` — `DomainEvent` dataclass: `event_id`, `occurred_at`, `correlation_id`
- [x] `src/domain/shared/gateways.py` — `NotificationGateway(Protocol)`: `send_confirmation`, `send_expiry`
- [x] `src/domain/shared/gateways.py` — `DistributedLockGateway(Protocol)`: async context manager `lock(resource, ttl_ms)`

### P1.2 — Ticketing bounded context

- [x] `src/domain/ticketing/model.py` — `TicketStatus` enum: `AVAILABLE`, `RESERVED`, `CONFIRMED`, `RELEASED`
- [x] `src/domain/ticketing/model.py` — `Reservation` child entity: `id`, `ticket_id`, `user_id`, `created_at`, `expires_at`
- [x] `src/domain/ticketing/model.py` — `Reservation.is_expired() -> bool`
- [x] `src/domain/ticketing/model.py` — `Ticket` aggregate root: `id`, `event_id`, `seat_number`, `status`, `reserved_by`, `version`, `reservation`, `events`
- [x] `src/domain/ticketing/model.py` — `Ticket.reserve(user_id)` creates Reservation (TTL=5min), bumps version, emits `TicketReserved`
- [x] `src/domain/ticketing/model.py` — `Ticket.release(reason)` resets status, clears reservation, emits `TicketReleased`
- [x] `src/domain/ticketing/model.py` — `Ticket.confirm()` sets CONFIRMED, emits `TicketConfirmed`
- [x] `src/domain/ticketing/events.py` — `TicketReserved`, `TicketReleased`, `TicketConfirmed`
- [x] `src/domain/ticketing/exceptions.py` — `TicketAlreadyTakenError`, `TicketNotFoundError`, `OptimisticLockConflict`, `LockNotAcquiredError`
- [x] `src/domain/ticketing/repository.py` — `TicketRepository(Protocol)`: `add`, `get`, `get_for_update`

### P1.3 — Payment bounded context

- [x] `src/domain/payment/events.py` — `PaymentCompleted`, `PaymentFailed`
- [x] `src/domain/payment/exceptions.py` — `PaymentDeclinedError`
- [x] `src/domain/payment/gateway.py` — `PaymentGateway(Protocol)`: `charge`, `refund`

### P1.4 — Outbox context

- [x] `src/domain/outbox/repository.py` — `OutboxRepository(Protocol)`: `save_message`, `get_unpublished`, `mark_published`

### P1.5 — Unit tests: domain layer

- [x] `tests/unit/domain/test_ticket.py` — `Ticket.reserve()` changes status to RESERVED
- [x] `tests/unit/domain/test_ticket.py` — `Ticket.reserve()` raises `TicketAlreadyTakenError` when status != AVAILABLE
- [x] `tests/unit/domain/test_ticket.py` — `Ticket.reserve()` creates Reservation as child entity
- [x] `tests/unit/domain/test_ticket.py` — `Ticket.release()` restores AVAILABLE and clears reservation
- [x] `tests/unit/domain/test_ticket.py` — `version` increments on every state change
- [x] `tests/unit/domain/test_ticket.py` — `Ticket.reserve()` appends `TicketReserved` event
- [x] `tests/unit/domain/test_ticket.py` — `Ticket.release()` appends `TicketReleased` event
- [x] `tests/unit/domain/test_ticket.py` — `Ticket.confirm()` appends `TicketConfirmed` event
- [x] `tests/unit/domain/test_reservation.py` — `Reservation.is_expired()` returns True/False correctly

-----

## PHASE 2 — Use Cases Layer

### P2.1 — Request / Response objects

- [ ] `src/use_cases/request_objects.py` — `ReserveTicketRequest`: `ticket_id`, `user_id`, `idempotency_key`
- [ ] `src/use_cases/request_objects.py` — `ReleaseTicketRequest`: `ticket_id`, `reason`
- [ ] `src/use_cases/request_objects.py` — `ProcessPaymentRequest`: `reservation_id`, `amount_cents`, `payment_method`
- [ ] `src/use_cases/response_objects.py` — `UseCaseResponse`: `success`, `message`, `data: dict | None`

### P2.2 — ReserveTicketUseCase

- [ ] `src/use_cases/reserve_ticket.py` — `ReserveTicketUseCase` class with DI: `ticket_repo`
- [ ] `execute(request)` — call `ticket_repo.get_for_update()`
- [ ] Call `ticket.reserve(user_id)` — aggregate creates Reservation internally (TTL=5min)
- [ ] Persist ticket via `ticket_repo.add()` — Reservation is saved as part of the aggregate
- [ ] Return `UseCaseResponse(success=True, data={...})`
- [ ] Handle `TicketAlreadyTakenError` → `UseCaseResponse(success=False, ...)`

### P2.3 — ReleaseTicketUseCase

- [ ] `src/use_cases/release_ticket.py` — `ReleaseTicketUseCase` with DI: `ticket_repo`
- [ ] `execute(request)` — load ticket, call `ticket.release(reason)`, persist via `ticket_repo.add()`
- [ ] Return `UseCaseResponse(success=True)`

### P2.4 — SAGA Orchestrator

- [ ] `src/use_cases/saga.py` — `SagaStep` dataclass: `name`, `action`, `compensation`
- [ ] `src/use_cases/saga.py` — `SagaContext` dataclass: `ticket_id`, `user_id`, `reservation_id`, `correlation_id`
- [ ] `src/use_cases/saga.py` — `SagaResult` dataclass: `success`, `failed_step`, `reason`
- [ ] `src/use_cases/saga.py` — `TicketPurchaseSaga` class with DI: `ticket_repo`, `payment_gateway`, `notifier`
- [ ] Define `_steps` list: validate, reserve, charge, notify
- [ ] Implement `execute(ctx)` — iterate steps, collect `executed[]`
- [ ] Implement `_compensate(ctx, executed)` — iterate `reversed(executed)`
- [ ] Each compensation in `try/except` — log CRITICAL, do not stop rollback
- [ ] Return `SagaResult.success()` or `SagaResult.failed(step, reason)`

### P2.5 — asyncio timeout wrapper

- [ ] `execute_with_timeout(request, timeout_seconds=300)` on `ReserveTicketUseCase`
- [ ] `async with asyncio.timeout(timeout_seconds)`
- [ ] In `except TimeoutError`: call `ReleaseTicketUseCase` + `NotificationGateway.send_expiry()`

### P2.6 — Parallel validations

- [ ] `src/use_cases/validators.py` — `validate_ticket_available(ticket_id, repo)`
- [ ] `src/use_cases/validators.py` — `validate_user_not_blacklisted(user_id, repo)`
- [ ] `src/use_cases/validators.py` — `validate_payment_method(method_id, gateway)`
- [ ] In SAGA `_validate` step: run all 3 via `asyncio.TaskGroup`

### P2.7 — Unit tests: use cases

- [ ] `tests/unit/use_cases/test_reserve_ticket.py` — happy path with in-memory repo
- [ ] Test: `Ticket.reserve()` called once, `ticket_repo.save()` called once
- [ ] Test: `get_for_update()` returns `None` → `UseCaseResponse(success=False)`
- [ ] Test: `TicketAlreadyTakenError` → `success=False`
- [ ] `tests/unit/use_cases/test_saga.py` — happy path: all 4 steps called in order
- [ ] Test: failure at step 3 → `_compensate` called for steps 1 and 2 in reverse
- [ ] Test: failure at step 1 → no compensation called
- [ ] Test: compensation failure does not interrupt rollback of remaining steps

-----

## PHASE 3 — Adapters Layer

### P3.1 — In-memory repository (for tests)

- [ ] `src/adapters/repositories/memory_ticket_repo.py` — `MemoryTicketRepository`
- [ ] `_store: dict[int, Ticket]` and `_locks: dict[int, asyncio.Lock]`
- [ ] `get(ticket_id)` → copy from `_store`
- [ ] `get_for_update(ticket_id)` → acquire lock, return ticket
- [ ] `save(ticket)` → write to `_store`, release lock
- [ ] `release(ticket_id)` → set `status=AVAILABLE`
- [ ] `src/adapters/repositories/memory_reservation_repo.py` — same pattern

### P3.2 — PostgreSQL repository

- [ ] `src/infrastructure/database/models.py` — `TicketModel(Base)` with `version` column
- [ ] `src/infrastructure/database/models.py` — `ReservationModel(Base)` with `expires_at`
- [ ] `src/infrastructure/database/models.py` — `OutboxMessageModel(Base)` with `published`
- [ ] `src/infrastructure/database/session.py` — `async_session_factory`
- [ ] `src/infrastructure/database/session.py` — `get_session()` async generator
- [ ] `src/adapters/repositories/postgres_ticket_repo.py` — `PostgresTicketRepository`
- [ ] Implement `get(ticket_id)` — SELECT + map model → entity
- [ ] Implement `get_for_update(ticket_id)` — SELECT with `.with_for_update()`
- [ ] Implement `save(ticket)` — UPDATE with version check
- [ ] Implement `release(ticket_id)` — UPDATE status=AVAILABLE

### P3.3 — Alembic migrations

- [ ] `uv add alembic` and `alembic init src/infrastructure/database/migrations`
- [ ] Migration `001_create_tickets.py` — `tickets` table with `version`
- [ ] Migration `002_create_reservations.py` — `reservations` with `expires_at`
- [ ] Migration `003_create_outbox.py` — `outbox_messages` with `published`
- [ ] Migration `004_create_ticket_events.py` — `ticket_events` (event sourcing)
- [ ] Verify: `uv run alembic upgrade head` → all tables green

### P3.4 — Redis distributed lock gateway

- [ ] `src/adapters/gateways/redis_gateway.py` — `RedisDistributedLockGateway`
- [ ] `distributed_lock(resource, ttl_ms)` as `asynccontextmanager`
- [ ] `redis.set(key, token, nx=True, px=ttl_ms)` — acquire
- [ ] Lua script: atomic check-and-delete on release
- [ ] Raise `LockNotAcquiredError` when `set` returns `None`

### P3.5 — Stripe gateway

- [ ] `src/adapters/gateways/stripe_gateway.py` — `StripeGateway` with `asyncio.Semaphore(10)`
- [ ] `charge(amount_cents, payment_method)` — `async with self._semaphore`
- [ ] `refund(charge_id)` — guarded by semaphore
- [ ] `src/adapters/gateways/mock_payment_gateway.py` — configurable `should_fail: bool`

### P3.6 — Serializers & presenters

- [ ] `src/adapters/serializers.py` — `ticket_to_dict(ticket: Ticket) -> dict`
- [ ] `src/adapters/serializers.py` — `reservation_to_dict(res: Reservation) -> dict`
- [ ] `src/adapters/presenters.py` — `present_reserve_response(uc_response) -> dict`

### P3.7 — Unit tests: adapters

- [ ] `tests/unit/adapters/test_memory_ticket_repo.py` — `get_for_update` blocks second concurrent access
- [ ] `tests/unit/adapters/test_serializers.py` — round-trip: entity → dict → compare fields

-----

## PHASE 4 — Infrastructure Layer

### P4.1 — FastAPI app factory

- [ ] `src/infrastructure/api/main.py` — `create_app() -> FastAPI` with lifespan
- [ ] Lifespan: create engine, start `outbox_relay_worker` as `asyncio.create_task()`
- [ ] Lifespan: initialise `ProcessPoolExecutor` and `ThreadPoolExecutor`
- [ ] Lifespan: graceful shutdown — `.cancel()` + `gather(return_exceptions=True)`

### P4.2 — Dependency injection

- [ ] `src/infrastructure/api/dependencies.py` — `get_session()` async generator
- [ ] `get_ticket_repo(session)` → `PostgresTicketRepository(session)`
- [ ] `get_reserve_use_case(ticket_repo, reservation_repo)` → `ReserveTicketUseCase(...)`
- [ ] `get_saga(ticket_repo, payment_gateway, notifier)` → `TicketPurchaseSaga(...)`
- [ ] `get_redis()` → singleton redis client

### P4.3 — API routes: tickets

- [ ] `GET /tickets/{event_id}` — list seats for event
- [ ] `POST /tickets/{ticket_id}/reserve` — call `execute_with_timeout()`
- [ ] `POST /tickets/{ticket_id}/release` — call `ReleaseTicketUseCase.execute()`
- [ ] `GET /tickets/{ticket_id}/status` — return current status

### P4.4 — API routes: payments

- [ ] `POST /payments/charge` — call `ProcessPaymentUseCase`
- [ ] `POST /payments/refund/{charge_id}` — call `payment_gateway.refund()`

### P4.5 — Idempotency middleware

- [ ] `IdempotencyMiddleware(BaseHTTPMiddleware)` — check `Idempotency-Key` header
- [ ] Cache hit → return cached response immediately
- [ ] Cache miss → execute, cache response for 24h
- [ ] Register in `create_app()` via `app.add_middleware(...)`

### P4.6 — Rate limiting

- [ ] `uv add slowapi`
- [ ] `slowapi` limiter with Redis backend
- [ ] `@limiter.limit("100/minute")` on reservation endpoints

### P4.7 — WebSocket broadcaster

- [ ] `SeatMapBroadcaster` singleton: `connect`, `disconnect`, `broadcast`
- [ ] `broadcast` uses `asyncio.gather()` with `return_exceptions=True`
- [ ] Remove dead connections after each broadcast
- [ ] `GET /ws/seat-map/{event_id}` — WebSocket endpoint

### P4.8 — Outbox relay worker

- [ ] `outbox_relay_worker(session_factory, event_bus)`
- [ ] SELECT with `.with_for_update(skip_locked=True)`
- [ ] `asyncio.gather()` to publish all messages in parallel
- [ ] UPDATE `published=True`, commit
- [ ] `asyncio.sleep(0.1)` when queue empty
- [ ] Register in lifespan as `create_task()`

### P4.9 — CPU worker (ProcessPool)

- [ ] `generate_ticket_pdf(ticket_dict) -> bytes`
- [ ] `loop.run_in_executor(process_pool, _render_pdf_sync, ticket_dict)`
- [ ] `_render_pdf_sync` — top-level function, pickle-able

### P4.10 — IO worker (ThreadPool)

- [ ] `send_email(to, subject, body) -> None`
- [ ] `loop.run_in_executor(thread_pool, _send_smtp_blocking, to, subject, body)`

### P4.11 — Observability wiring

- [ ] `configure_structlog()` with JSON renderer
- [ ] Prometheus Counter, Histogram, Gauge definitions
- [ ] `configure_otel(service_name)` with OTLP exporter
- [ ] `GET /metrics` — Prometheus endpoint
- [ ] Call all `configure_*()` in `create_app()` before routers

-----

## PHASE 5 — Integration Tests

### P5.1 — Test fixtures

- [ ] `tests/conftest.py` — `postgres_container` fixture (testcontainers, scope=session)
- [ ] `tests/conftest.py` — `redis_container` fixture (testcontainers, scope=session)
- [ ] `tests/conftest.py` — `db_session` fixture — async session with rollback after each test
- [ ] `tests/conftest.py` — `redis_client` fixture
- [ ] `tests/conftest.py` — `ticket_factory` (factory-boy)

### P5.2 — Integration: reservation happy path

- [ ] Reserve available ticket → status RESERVED in DB
- [ ] `version` increments after each operation
- [ ] `reservation.expires_at` set to `now + 5min`

### P5.3 — Integration: race condition

- [ ] 50 concurrent `asyncio.gather()` on 1 ticket
- [ ] Assert: exactly 1 success, 49 `TicketAlreadyTakenError`
- [ ] Assert: DB contains exactly 1 reservation for that ticket_id
- [ ] Repeat for optimistic strategy

### P5.4 — Integration: SAGA rollback

- [ ] Happy path: ticket CONFIRMED, email sent
- [ ] Mock payment fails → ticket AVAILABLE, reservation removed
- [ ] Mock SMTP fails → ticket still CONFIRMED (non-critical)

### P5.5 — Integration: outbox relay

- [ ] Commit ticket reservation → outbox message created
- [ ] Start relay worker as `asyncio.create_task()` in test
- [ ] Assert: message published to Redis Streams, marked `published=True`

### P5.6 — Property-based tests

- [ ] `@given(saga_events)` — random sequences of step successes/failures
- [ ] Assert: after any `failed_step`, ticket always returns to AVAILABLE

-----

## PHASE 6 — Frontend Demo

### P6.1 — Vite + React setup

- [ ] `npm create vite@latest frontend -- --template react-ts`
- [ ] `npm install @tanstack/react-query recharts zustand react-spring`
- [ ] Configure `vite.config.ts` proxy: `/api` → `http://localhost:8000`
- [ ] Set up Tailwind CSS

### P6.2 — WebSocket hook

- [ ] `src/hooks/useWebSocket.ts` — auto-reconnect with exponential backoff
- [ ] Fields: `connected`, `messages: Message[]`, `send(data)`

### P6.3 — Seat Map component

- [ ] 12×4 grid (48 seats), colour by status
- [ ] Updates on WebSocket message
- [ ] Status transition animation (react-spring)

### P6.4 — Scenario Panel (6 buttons)

- [ ] 6 buttons → `POST /api/demo/scenarios/{name}`
- [ ] Backend demo endpoints for: race, saga, timeout, semaphore, broadcast, outbox

### P6.5 — SAGA Visualizer

- [ ] 4 steps with icons: pending / running / success / failed
- [ ] Updates via WebSocket events
- [ ] Active step pulses (CSS keyframes)

### P6.6 — Timeout Progress Bar

- [ ] Progress bar 0→100% over `duration_ms`
- [ ] Colour shifts to red above 80%

### P6.7 — Semaphore Gauge

- [ ] 10 squares (highlighted = active slot)
- [ ] Shows `queued` counter

### P6.8 — Event Log

- [ ] Scrolling feed, max 60 entries, colour by type
- [ ] `fadeIn` animation, auto-scroll

### P6.9 — Metrics Dashboard

- [ ] 4 tiles: requests, conflicts, WS clients, avg latency
- [ ] TanStack Query refetch every 1s
- [ ] Recharts LineChart — throughput/min (last 60 points)

### P6.10 — Concurrency Layers Panel

- [ ] 3 cards: asyncio, ThreadPool, ProcessPool
- [ ] Highlights on WS event `{type: "layer_active", layer: "asyncio"}`

-----

## PHASE 7 — Observability & Load Tests

### P7.1 — Prometheus metrics

- [ ] `reservations_total{status="success|conflict|timeout"}`
- [ ] `reservation_duration_seconds` histogram
- [ ] `outbox_queue_depth` gauge
- [ ] `stripe_concurrent_requests` gauge
- [ ] `websocket_connections_total` gauge

### P7.2 — Grafana dashboard

- [ ] `grafana/dashboards/reservex.json` — provisioned
- [ ] Panel: Reservations/min, Latency p50/p95/p99, Error rate, Queue depth

### P7.3 — Locust load tests

- [ ] `ReservationUser` — `wait_time = between(0.1, 0.5)`
- [ ] Tasks: `reserve_random_ticket`, `check_ticket_status`
- [ ] `SpikeUser` — `wait_time = constant(0)`
- [ ] `locust.conf` with `users=500`, `spawn-rate=50`

### P7.4 — README & ADRs

- [ ] `README.md` — Mermaid architecture diagram
- [ ] Quick Start in 5 steps
- [ ] Concurrency Design Decisions section
- [ ] Locking Strategy Comparison table
- [ ] Benchmark Results (Locust screenshots)
- [ ] `docs/adr/001` through `docs/adr/005`
- [ ] CI badge + coverage badge

-----

## Progress Tracker

| Phase | Tasks | Done | Status |
|---|---|---|---|
| Pre-Phase-0 Setup | 15 | 15 | ✅ |
| P0 — Bootstrap | 22 | 22 | ✅ |
| P1 — Domain | 24 | 0 | ⬜ |
| P2 — Use Cases | 24 | 0 | ⬜ |
| P3 — Adapters | 20 | 0 | ⬜ |
| P4 — Infrastructure | 28 | 0 | ⬜ |
| P5 — Integration Tests | 16 | 0 | ⬜ |
| P6 — Frontend | 28 | 0 | ⬜ |
| P7 — Observability | 18 | 0 | ⬜ |
| **Total** | **195** | **37** | 19% |

-----

*Paste this document at the start of every Claude Code session.*
*Tell Claude Code which phase and task to work on.*
*One task = one commit. Push after every task.*
