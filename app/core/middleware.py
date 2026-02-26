import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

EXCLUDED_PATHS = {"/health/live", "/health/ready", "/metrics"}


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Request ID — use incoming header if present, otherwise generate one
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind request_id to structlog context for all downstream log calls
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # Time the request
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Attach request ID to response header
        response.headers["x-request-id"] = request_id

        # Emit structured completion log
        await logger.ainfo(
            "Request completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response
