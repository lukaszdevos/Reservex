"""Redis-backed distributed lock gateway.

Layer: adapters
Implements: DistributedLockGateway (domain.shared.gateways)
"""

import secrets
from collections.abc import AsyncGenerator
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import redis.asyncio as aioredis

from domain.ticketing.exceptions import LockNotAcquiredError

# Atomic Lua script: only delete the key if its value matches our token.
_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""


class RedisDistributedLockGateway:
    """Distributed lock via Redis SET NX + Lua CAS release.

    Implements: DistributedLockGateway
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    @asynccontextmanager
    async def _lock_ctx(
        self, resource: str, ttl_ms: int
    ) -> AsyncGenerator[None, None]:
        token = secrets.token_hex(16)
        key = f"lock:{resource}"
        acquired = await self._redis.set(key, token, nx=True, px=ttl_ms)
        if acquired is None:
            raise LockNotAcquiredError(resource)
        try:
            yield
        finally:
            await self._redis.eval(_RELEASE_SCRIPT, 1, key, token)  # type: ignore[misc]

    def lock(self, resource: str, ttl_ms: int) -> AbstractAsyncContextManager[None]:
        return self._lock_ctx(resource, ttl_ms)
