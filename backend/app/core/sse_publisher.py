"""
Module 4B: Redis Pub/Sub SSE Publisher — Multi-Pod Event Notification.

Replaces the in-memory asyncio.Queue with Redis Pub/Sub so SSE notifications
work across multiple API pods in a horizontally scaled deployment.

Falls back gracefully to in-memory queue if Redis is unavailable.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import redis — falls back gracefully if not installed
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False
    logger.info("redis package not installed — falling back to in-memory SSE queue")


SSE_CHANNEL = "supporthub:sse:events"


class SSEPublisher:
    """
    Publishes SSE events via Redis Pub/Sub for multi-pod delivery.
    Falls back to an in-memory asyncio.Queue if Redis is unavailable.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self._redis_url = redis_url
        self._redis_client: Optional[Any] = None
        self._fallback_queue: asyncio.Queue = asyncio.Queue()
        self._use_redis = False

    async def connect(self):
        """Attempt to connect to Redis. Falls back to in-memory if unavailable."""
        if not REDIS_AVAILABLE or not self._redis_url:
            logger.info("SSE Publisher: using in-memory queue (Redis unavailable)")
            return

        try:
            self._redis_client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._redis_client.ping()
            self._use_redis = True
            logger.info("SSE Publisher: connected to Redis at %s", self._redis_url)
        except Exception as exc:
            logger.warning("SSE Publisher: Redis connection failed (%s), using in-memory fallback", exc)
            self._redis_client = None
            self._use_redis = False

    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish an SSE event to all connected clients."""
        event = {
            "type": event_type,
            "data": data,
        }

        if self._use_redis and self._redis_client:
            try:
                await self._redis_client.publish(SSE_CHANNEL, json.dumps(event))
                logger.debug("SSE event published to Redis: %s", event_type)
                return
            except Exception as exc:
                logger.warning("Redis publish failed: %s — falling back to in-memory", exc)

        # Fallback: in-memory queue
        await self._fallback_queue.put(event)

    async def subscribe(self):
        """
        Subscribe to SSE events. Yields events as they arrive.
        Uses Redis Pub/Sub if available, otherwise polls in-memory queue.
        """
        if self._use_redis and self._redis_client:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe(SSE_CHANNEL)
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield json.loads(message["data"])
            finally:
                await pubsub.unsubscribe(SSE_CHANNEL)
        else:
            # In-memory fallback
            while True:
                event = await self._fallback_queue.get()
                yield event

    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("SSE Publisher: Redis connection closed")

    # Common event helpers
    async def ticket_created(self, ticket_id: str, title: str, user_id: str):
        await self.publish_event("ticket.created", {
            "ticket_id": ticket_id,
            "title": title,
            "user_id": user_id,
        })

    async def ticket_resolved(self, ticket_id: str, title: str, resolved_by: str):
        await self.publish_event("ticket.resolved", {
            "ticket_id": ticket_id,
            "title": title,
            "resolved_by": resolved_by,
        })

    async def ticket_status_changed(self, ticket_id: str, old_status: str, new_status: str):
        await self.publish_event("ticket.status_changed", {
            "ticket_id": ticket_id,
            "old_status": old_status,
            "new_status": new_status,
        })

    async def draft_approved(self, draft_id: str, ticket_id: str, user_id: str):
        await self.publish_event("draft.approved", {
            "draft_id": draft_id,
            "ticket_id": ticket_id,
            "user_id": user_id,
        })


# Global publisher instance
sse_publisher = SSEPublisher()
