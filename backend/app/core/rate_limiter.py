"""
Phase 8: Fixed-Window In-Memory Rate Limiter.
Provides thread-safe request rate limiting with configurable limits per minute.
Supports reset() for test isolation and determinism.
"""
import threading
import time
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status


class RateLimiter:
    """Thread-safe fixed-window in-memory rate limiter."""

    def __init__(self):
        self._lock = threading.Lock()
        # Key: (key_str, endpoint) -> (window_start_timestamp, count)
        self._store: Dict[Tuple[str, str], Tuple[float, int]] = {}

    def is_allowed(
        self, key: str, endpoint: str, limit: int, window_seconds: int = 60
    ) -> bool:
        """
        Check if request under key and endpoint is within the allowed limit.
        Returns True if allowed, False if exceeded.
        """
        if limit <= 0:
            return True

        now = time.time()
        store_key = (key, endpoint)

        with self._lock:
            if store_key in self._store:
                window_start, count = self._store[store_key]
                if now - window_start < window_seconds:
                    if count >= limit:
                        return False
                    self._store[store_key] = (window_start, count + 1)
                    return True
                else:
                    # Window expired, start new window
                    self._store[store_key] = (now, 1)
                    return True
            else:
                self._store[store_key] = (now, 1)
                return True

    def reset(self) -> None:
        """Reset all rate limiter state for tests."""
        with self._lock:
            self._store.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(
    request: Request,
    endpoint: str,
    limit: int,
    window_seconds: int = 60,
) -> None:
    """
    Helper function to check rate limit for a FastAPI request.
    Raises HTTPException 429 if limit is exceeded.
    """
    client_ip = (
        request.client.host
        if request.client and request.client.host
        else "127.0.0.1"
    )
    # Check forwarded-for header if present
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    if not rate_limiter.is_allowed(client_ip, endpoint, limit, window_seconds):
        from app.monitoring.metrics import metrics_collector

        metrics_collector.increment("rate_limit_exceeded_total")

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for endpoint '{endpoint}'. Maximum {limit} requests per {window_seconds}s.",
        )
