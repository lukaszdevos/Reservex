"""structlog configuration with JSON renderer.

Layer: infrastructure/observability
Call configure_structlog() once at application startup before any logging occurs.
"""

from __future__ import annotations

import logging

import structlog


def configure_structlog(log_level: str = "INFO") -> None:
    """Configure structlog processors and JSON output format."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", level=level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
