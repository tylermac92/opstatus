import structlog
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.models.schemas.errors import ErrorDetail, ErrorResponse

logger: structlog.BoundLogger = structlog.get_logger()


def _get_request_id(request: Request) -> str:
    # Falls back to "unknown" if the request reached this handler before
    # RequestMiddleware had a chance to attach a request_id (e.g. very early errors).
    return str(getattr(request.state, "request_id", "unknown"))


def _make_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
    )


async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, NotFoundError)
    return _make_error_response(
        status_code=404,
        code="NOT_FOUND",
        message=exc.message,
        request_id=_get_request_id(request),
    )


async def conflict_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ConflictError)
    return _make_error_response(
        status_code=409,
        code="CONFLICT",
        message=exc.message,
        request_id=_get_request_id(request),
    )


async def service_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ServiceUnavailableError)
    return _make_error_response(
        status_code=503,
        code="SERVICE_UNAVAILABLE",
        message=exc.message,
        request_id=_get_request_id(request),
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Flatten all Pydantic validation errors into a single human-readable string.
    # Each error: "field -> subfield: message"; multiple errors joined with "; ".
    message = "; ".join(
        f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}"
        for err in exc.errors()
    )
    return _make_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message=message,
        request_id=_get_request_id(request),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    await logger.aerror(
        "Unhandled exception",
        exc_info=exc,
    )
    return _make_error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
        request_id=_get_request_id(request),
    )
