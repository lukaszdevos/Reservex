"""WebSocket seat map broadcaster and endpoint.

Layer: infrastructure/api/websockets
SeatMapBroadcaster is a singleton stored in app.state during lifespan.
broadcast() fans out seat-status updates to all connected clients via asyncio.gather().
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from infrastructure.observability.metrics import WEBSOCKET_CONNECTIONS

logger = structlog.get_logger(__name__)

ws_router = APIRouter()


class SeatMapBroadcaster:
    """Tracks active WebSocket connections per event_id and fans out updates.

    Singleton - stored in app.state.broadcaster during lifespan.
    """

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, ws: WebSocket, event_id: int) -> None:
        await ws.accept()
        self._connections[event_id].add(ws)
        WEBSOCKET_CONNECTIONS.inc()
        logger.info("ws_connected", event_id=event_id)

    def disconnect(self, ws: WebSocket, event_id: int) -> None:
        self._connections[event_id].discard(ws)
        WEBSOCKET_CONNECTIONS.dec()
        logger.info("ws_disconnected", event_id=event_id)

    async def broadcast(self, event_id: int, seat_id: int, status: str) -> None:
        """Fan out a seat-status update; silently prune dead connections."""
        conns = list(self._connections[event_id])
        if not conns:
            return
        payload = {"seat_id": seat_id, "status": status}
        results = await asyncio.gather(
            *[ws.send_json(payload) for ws in conns],
            return_exceptions=True,
        )
        for ws, result in zip(conns, results, strict=False):
            if isinstance(result, Exception):
                self._connections[event_id].discard(ws)
                WEBSOCKET_CONNECTIONS.dec()


@ws_router.websocket("/seat-map/{event_id}")
async def ws_seat_map(ws: WebSocket, event_id: int) -> None:
    """Accept a WebSocket connection and keep it alive until the client disconnects."""
    broadcaster: SeatMapBroadcaster = ws.app.state.broadcaster
    await broadcaster.connect(ws, event_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(ws, event_id)
    except Exception:
        broadcaster.disconnect(ws, event_id)
