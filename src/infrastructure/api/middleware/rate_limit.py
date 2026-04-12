"""Rate limiting via slowapi with Redis backend.

Layer: infrastructure/api/middleware
Module-level ``limiter`` is imported by routes for the @limiter.limit() decorator.
configure_limiter() wires exception handling into the FastAPI app.
"""

from __future__ import annotations

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from infrastructure.settings import settings

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
)


def configure_limiter(app: FastAPI) -> None:
    """Attach the rate-limit state and 429 exception handler to the app."""
    app.state.limiter = limiter
    # cast needed: slowapi handler is typed (Request, RateLimitExceeded) but
    # add_exception_handler expects (Request, Exception)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
