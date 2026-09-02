"""
In-memory SSE notification and event broadcasting service.
Broadcasts events like ticket_created, ticket_updated, ticket_assigned in real time.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Set

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> AsyncGenerator[dict[str, Any], None]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            self._subscribers.remove(queue)

    async def broadcast(self, event_type: str, payload: dict[str, Any]):
        message = {
            "event": event_type,
            "data": json.dumps(payload),
        }
        for queue in list(self._subscribers):
            try:
                await queue.put(message)
            except Exception as e:
                logger.warning("Failed to dispatch SSE event to subscriber: %s", e)


notification_service = NotificationService()

