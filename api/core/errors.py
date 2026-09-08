# =============================================================
# errors.py - Domain error type + global exception handlers
# =============================================================
# We separate DOMAIN errors (business rules) from HTTP errors.
# The service layer raises AppError with a machine-readable code
# and an HTTP status; the handler turns it into a consistent JSON
# body: {"code": "...", "message": "..."}.
# =============================================================

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base error for all domain / business rule failures."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Normalise FastAPI/Pydantic 422 errors into the same shape."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    msg = first.get("msg", "Invalid request data")
    message = f"{loc}: {msg}" if loc else msg
    # exc.errors() may carry non-serializable objects in "ctx" (e.g. ValueError).
    safe_detail = [
        {k: v for k, v in e.items() if k in ("type", "loc", "msg")} for e in errors
    ]
    return JSONResponse(
        status_code=422,
        content={"code": "validation_error", "message": message, "detail": safe_detail},
    )


async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": "Internal server error"},
    )
