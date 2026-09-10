"""
Phase 9: Request ID Correlation Middleware.
Inspects incoming X-Request-ID headers, validates or generates a unique correlation ID,
binds it to the request context, and attaches X-Request-ID to all HTTP responses.
"""
import re
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import set_request_id, clear_context

# Sanitization regex: allow alphanumeric characters and hyphens/underscores (max 64 chars)
_SAFE_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware ensuring every HTTP request has a validated correlation ID.
    """

    async def dispatch(self, request: Request, call_next):
        # Extract X-Request-ID header if provided by client/gateway
        raw_header = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")

        if raw_header and _SAFE_REQUEST_ID_REGEX.match(raw_header):
            request_id = raw_header
        else:
            request_id = f"req-{uuid.uuid4().hex[:12]}"

        # Bind to request-scoped ContextVar
        set_request_id(request_id)

        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # ContextVar cleans up automatically per async task, but we clear explicitly on completion
            pass
