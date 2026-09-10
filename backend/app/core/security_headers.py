"""
Phase 9: Security Headers Middleware.
Injects standard production HTTP security headers onto all outgoing responses
to mitigate MIME-sniffing, clickjacking, and cross-site framing attacks.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting hardened production security headers on all HTTP responses.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Standard defense-in-depth security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enable HSTS on responses
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
