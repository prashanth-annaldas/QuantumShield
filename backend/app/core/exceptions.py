"""
Phase 9: Centralized Exception Hierarchy & Sanitized Error Handlers.
Guarantees consistent, structured error responses across all API endpoints
while strictly preventing exposure of stack traces, database credentials, or secrets.
"""
import logging
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.request_context import get_request_id

logger = logging.getLogger("qds.security.errors")


# ─────────────────────────────────────────────────────────────────────────────
# Application Domain Exception Hierarchy
# ─────────────────────────────────────────────────────────────────────────────

class QDSBaseException(Exception):
    """Base exception for all domain-specific QDS errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str = "An unexpected server error occurred.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(QDSBaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"

    def __init__(self, message: str = "Invalid credentials or expired session token."):
        super().__init__(message)


class AuthorizationError(QDSBaseException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "ACCESS_FORBIDDEN"

    def __init__(self, message: str = "You do not have permission to perform this operation."):
        super().__init__(message)


class ResourceNotFoundError(QDSBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"

    def __init__(self, message: str = "The requested resource was not found."):
        super().__init__(message)


class ValidationError(QDSBaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Invalid request payload or parameters."):
        super().__init__(message)


class RateLimitError(QDSBaseException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message: str = "Request rate limit exceeded. Please retry later."):
        super().__init__(message)


class IdempotencyConflictError(QDSBaseException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "IDEMPOTENCY_CONFLICT"

    def __init__(self, message: str = "Idempotency key reused with conflicting request payload."):
        super().__init__(message)


class DatabaseUnavailableError(QDSBaseException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "DATABASE_UNAVAILABLE"

    def __init__(self, message: str = "Database service is temporarily unavailable."):
        super().__init__(message)


class ServiceUnavailableError(QDSBaseException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"

    def __init__(self, message: str = "Subsystem is currently unavailable."):
        super().__init__(message)


# ─────────────────────────────────────────────────────────────────────────────
# Global FastAPI Exception Handlers
# ─────────────────────────────────────────────────────────────────────────────

def format_error_response(code: str, message: str, request_id: str, status_code: int) -> JSONResponse:
    """Standardized JSON error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            },
        },
        headers={"X-Request-ID": request_id},
    )


async def qds_exception_handler(request: Request, exc: QDSBaseException) -> JSONResponse:
    """Handler for all domain QDS exceptions."""
    req_id = get_request_id()
    logger.warning(f"[{req_id}] {exc.error_code}: {exc.message}")
    return format_error_response(
        code=exc.error_code,
        message=exc.message,
        request_id=req_id,
        status_code=exc.status_code,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for standard FastAPI/Starlette HTTPExceptions."""
    req_id = get_request_id()
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    message = str(exc.detail) if exc.detail else "An HTTP error occurred."
    logger.info(f"[{req_id}] HTTP {exc.status_code} ({code}): {message}")

    headers = dict(exc.headers or {})
    headers["X-Request-ID"] = req_id

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "request_id": req_id,
            },
            # Backward compatibility for endpoints returning detail string
            "detail": message,
        },
        headers=headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for Pydantic schema validation failures."""
    req_id = get_request_id()
    err_msgs = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors() if err.get("loc")]
    message = "; ".join(err_msgs) if err_msgs else "Validation error in request parameters."
    logger.info(f"[{req_id}] VALIDATION_ERROR: {message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "request_id": req_id,
            },
            "detail": exc.errors(),
        },
        headers={"X-Request-ID": req_id},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled server errors.
    Gives a generic sanitized error message — never exposes tracebacks, SQL statements, or secrets.
    """
    req_id = get_request_id()
    logger.error(f"[{req_id}] Unhandled Exception: {type(exc).__name__}: {exc}", exc_info=True)

    return format_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred. Please contact the administrator with the correlation request_id.",
        request_id=req_id,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
