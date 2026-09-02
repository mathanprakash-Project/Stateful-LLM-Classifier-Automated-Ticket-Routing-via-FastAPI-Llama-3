"""
Structured request/response logging middleware.
"""

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        req_id = getattr(request.state, "request_id", "unknown")
        
        response = await call_next(request)
        
        process_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            "%s %s %d - %.2fms [req_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
            req_id,
        )
        return response

