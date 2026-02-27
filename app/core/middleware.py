import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import http_request_duration_seconds, http_requests_total

logger: structlog.BoundLogger = structlog.get_logger()

# Paths that bypass logging and metrics recording.
# Health probes are called frequently by orchestrators; /metrics is read by Prometheus.
# Recording them would pollute logs and skew latency histograms.
EXCLUDED_PATHS = {"/health/live", "/health/ready", "/metrics"}


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Honour a caller-supplied request ID (useful for distributed tracing),
        # or generate a fresh UUID when none is provided.
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        duration_ms = round(duration * 1000, 2)

        response.headers["x-request-id"] = request_id

        await logger.ainfo(
            "Request completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Record Prometheus metrics
        http_requests_total.labels(
            method=request.method,
            path=request.url.path,
            status_code=str(response.status_code),
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            path=request.url.path,
        ).observe(duration)

        return response
