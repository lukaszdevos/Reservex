"""Idempotency middleware — returns cached responses for repeated requests.

Layer: infrastructure/api/middleware
Checks the ``Idempotency-Key`` request header. Cache hits return the stored
response immediately. Successful (HTTP 200) responses are cached for 24 h.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Cache responses by Idempotency-Key header using Redis."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)

        redis_client = request.app.state.redis
        cache_key = f"idempotency:{key}"

        cached: bytes | None = await redis_client.get(cache_key)
        if cached is not None:
            return Response(
                content=cached, status_code=200, media_type="application/json"
            )

        response = await call_next(request)

        if response.status_code == 200:
            body = b"".join(
                [chunk async for chunk in response.body_iterator]  # type: ignore[attr-defined]
            )
            await redis_client.setex(cache_key, 86400, body)
            return Response(
                content=body,
                status_code=200,
                media_type=response.media_type,
            )

        return response
