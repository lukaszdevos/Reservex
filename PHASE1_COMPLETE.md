# Reservex — Phase 1 Complete: Domain Layer

**Date completed:** 2026-03-16
**Branch:** `claude/phase-1-master-briefing-tKHsu`
**Repo:** `lukaszdevos/Reservex`

---

## What Was Built

Phase 1 is the pure domain layer — **zero external imports**, Python stdlib only.
It follows Domain-Driven Design bounded contexts as described in *Cosmic Python* (Architecture Patterns with Python).

---

## Domain Structure — Bounded Contexts

```
src/domain/
├── shared/             # Shared kernel — used by all bounded contexts
│   ├── event.py        # DomainEvent base dataclass
│   └── gateways.py     # NotificationGateway, DistributedLockGateway (Protocol)
├── ticketing/          # Ticketing bounded context
│   ├── model.py        # Ticket (aggregate root) + Reservation (child entity) + TicketStatus
│   ├── events.py       # TicketReserved, TicketReleased, TicketConfirmed
│   ├── exceptions.py   # TicketAlreadyTakenError, TicketNotFoundError,
│   │                   # OptimisticLockConflict, LockNotAcquiredError
│   └── repository.py   # TicketRepository Protocol (add / get / get_for_update)
├── payment/            # Payment bounded context
│   ├── events.py       # PaymentCompleted, PaymentFailed
│   ├── exceptions.py   # PaymentDeclinedError
│   └── gateway.py      # PaymentGateway Protocol (charge / refund)
└── outbox/             # Transactional outbox context
    └── repository.py   # OutboxRepository Protocol
```

---

## Key Design Decisions

### 1. Ticket as Aggregate Root (Cosmic Python)

`Ticket` is the sole aggregate root for the ticketing context. All state changes flow through it:

```python
reservation = ticket.reserve(user_id=42)   # creates Reservation child internally
ticket.release(reason="expired")            # resets state, clears reservation
ticket.confirm()                            # marks CONFIRMED after payment
```

**Consequence:** `Reservation` is never instantiated directly by application code. It is accessed only via `ticket.reservation`.

### 2. One Repository Per Aggregate

There is **no** `ReservationRepository`. Reservations are saved atomically as part of the `Ticket` aggregate via `TicketRepository.add(ticket)`.

This enforces the Cosmic Python rule: *"repositories only return aggregates, never child entities."*

### 3. Domain Events Collected on the Aggregate

Each state-changing method appends to `ticket.events: list[DomainEvent]`:

| Method | Event emitted |
|--------|--------------|
| `reserve()` | `TicketReserved(ticket_id, user_id)` |
| `release()` | `TicketReleased(ticket_id, reason)` |
| `confirm()` | `TicketConfirmed(ticket_id)` |

The Unit of Work (Phase 3) will publish these after a successful commit.

### 4. Repository API: `add()` / `get()`

Following Cosmic Python convention:
- `add(ticket)` — insert or update the full aggregate (ticket + reservation)
- `get(ticket_id)` — load aggregate by ID
- `get_for_update(ticket_id)` — load with pessimistic lock (for use in transactions)

### 5. Bounded Context Isolation

Cross-context imports are only allowed through `domain/shared/`. Direct imports between `ticketing/` and `payment/` are forbidden — they communicate only via domain events.

---

## Quality Checks

```
uv run ruff check .    → ✅ 0 errors
uv run mypy src/       → ✅ 0 errors (28 files, strict mode)
uv run pytest tests/unit -v  → ✅ 10/10 passed
```

### Tests

| Test | Status |
|------|--------|
| `Ticket.reserve()` changes status to RESERVED | ✅ |
| `Ticket.reserve()` raises `TicketAlreadyTakenError` when not AVAILABLE | ✅ |
| `Ticket.reserve()` creates `Reservation` as child entity | ✅ |
| `Ticket.release()` restores AVAILABLE, clears reservation | ✅ |
| `version` increments on every state change | ✅ |
| `Ticket.reserve()` appends `TicketReserved` to events | ✅ |
| `Ticket.release()` appends `TicketReleased` to events | ✅ |
| `Ticket.confirm()` appends `TicketConfirmed` to events | ✅ |
| `Reservation.is_expired()` returns True past `expires_at` | ✅ |
| `Reservation.is_expired()` returns False before `expires_at` | ✅ |

---

## What Does NOT Exist Yet

- No use cases (`ReserveTicketUseCase`, SAGA orchestrator) — Phase 2
- No repository implementations — only Protocols — Phase 3
- No database models or Alembic migrations — Phase 3
- No FastAPI app factory or routes — Phase 4
- No integration tests — Phase 5

---

## Starting Phase 2

```
Phase 1 is complete. See PHASE1_COMPLETE.md for context.
Now implement Phase 2: Use Cases Layer.
Start with P2.1 — Request/Response objects.
```
