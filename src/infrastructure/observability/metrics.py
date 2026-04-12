"""Prometheus metric definitions.

Layer: infrastructure/observability
Metrics are registered at module import time.
Call configure_metrics() at startup to ensure registration before first scrape.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

RESERVATIONS_TOTAL: Counter = Counter(
    "reservations_total",
    "Total reservation attempts",
    ["status"],  # success | conflict | timeout
)

RESERVATION_DURATION: Histogram = Histogram(
    "reservation_duration_seconds",
    "Time spent processing a reservation request",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

OUTBOX_QUEUE_DEPTH: Gauge = Gauge(
    "outbox_queue_depth",
    "Number of unpublished outbox messages",
)

STRIPE_CONCURRENT_REQUESTS: Gauge = Gauge(
    "stripe_concurrent_requests",
    "Current number of in-flight Stripe API calls",
)

WEBSOCKET_CONNECTIONS: Gauge = Gauge(
    "websocket_connections_total",
    "Current number of active WebSocket connections",
)


def configure_metrics() -> None:
    """Ensure metrics module is imported and counters are registered."""
