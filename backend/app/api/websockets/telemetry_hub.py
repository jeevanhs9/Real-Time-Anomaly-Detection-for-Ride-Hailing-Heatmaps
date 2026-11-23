"""
WebSocket connection manager.

Manages active browser connections and broadcasts tick payloads to all of
them concurrently, silently dropping dead connections.
"""
from __future__ import annotations
import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._active: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._active.append(ws)
        logger.info("WS connected — total: %d", len(self._active))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self._active:
                self._active.remove(ws)
        logger.info("WS disconnected — total: %d", len(self._active))

    async def broadcast(self, payload: dict[str, Any]) -> None:
        if not self._active:
            return
        message = json.dumps(payload, default=str)
        async with self._lock:
            live = list(self._active)
        dead: list[WebSocket] = []
        await asyncio.gather(*[_send_safe(ws, message, dead) for ws in live])
        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self._active:
                        self._active.remove(ws)
            logger.info("Removed %d dead connections.", len(dead))

    @property
    def connection_count(self) -> int:
        return len(self._active)


async def _send_safe(
    ws: WebSocket, message: str, dead: list[WebSocket]
) -> None:
    try:
        await ws.send_text(message)
    except Exception:
        dead.append(ws)
