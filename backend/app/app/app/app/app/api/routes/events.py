"""
Server-Sent Events (SSE) stream endpoint for real-time dashboard events.
"""

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.services.notification_service import notification_service

router = APIRouter(prefix="/events", tags=["Real-time Events"])


@router.get("/stream")
async def events_stream(request: Request):
    async def event_generator():
        async for event_data in notification_service.subscribe():
            if await request.is_disconnected():
                break
            yield event_data

    return EventSourceResponse(event_generator())

