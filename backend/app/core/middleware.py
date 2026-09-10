"""
Phase 8: Request Latency & Observability Middleware.
Measures HTTP request execution duration, records metrics, and tracks error rates.
Strictly non-logging of sensitive payloads or credentials.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics import metrics_collector


class LatencyMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records HTTP request counts and execution latency.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        metrics_collector.increment("http_requests_total")

        try:
            response: Response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000.0
            metrics_collector.record_latency(duration_ms)

            if response.status_code >= 400:
                metrics_collector.increment("http_requests_failed")

            return response
        except Exception:
            duration_ms = (time.time() - start_time) * 1000.0
            metrics_collector.record_latency(duration_ms)
            metrics_collector.increment("http_requests_failed")
            raise
