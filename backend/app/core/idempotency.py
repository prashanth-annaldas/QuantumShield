"""
Phase 9: Idempotency Protection.
Protects security-sensitive POST operations against duplicate execution
when the client supplies an Idempotency-Key header.
Supports payload hash validation, TTL expiration, and conflict detection.
"""
import hashlib
import json
import threading
import time
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, HTTPException, status


class IdempotencyRecord:
    """Stores metadata and cached response for an idempotency key."""
    __slots__ = ("key", "user_id", "payload_hash", "status_code", "response_data", "created_at", "ttl_seconds")

    def __init__(self, key: str, user_id: Optional[str], payload_hash: str,
                 status_code: int, response_data: Any, ttl_seconds: int = 300):
        self.key = key
        self.user_id = user_id
        self.payload_hash = payload_hash
        self.status_code = status_code
        self.response_data = response_data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds


class IdempotencyManager:
    """Thread-safe in-memory idempotency cache."""

    def __init__(self, default_ttl_seconds: int = 300):
        self._lock = threading.Lock()
        self._store: Dict[str, IdempotencyRecord] = {}
        self._default_ttl = default_ttl_seconds

    def compute_payload_hash(self, payload: Any) -> str:
        """Deterministically hashes request payload (string or dict)."""
        if isinstance(payload, dict):
            serialized = json.dumps(payload, sort_keys=True)
        else:
            serialized = str(payload or "")
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def check_key(self, key: str, user_id: Optional[str], payload_hash: str) -> Optional[Tuple[int, Any]]:
        """
        Validates idempotency key state:
        - If key does not exist or expired: returns None (caller proceeds with execution)
        - If key exists with SAME user & payload: returns (status_code, cached_response_data)
        - If key exists with DIFFERENT payload or user: raises HTTPException 409 Conflict
        """
        with self._lock:
            record = self._store.get(key)
            if record is None:
                return None

            if record.is_expired:
                del self._store[key]
                return None

            # Conflict detection
            if record.payload_hash != payload_hash or record.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Idempotency-Key '{key}' was already used with a different request payload or user.",
                )

            return record.status_code, record.response_data

    def record_response(self, key: str, user_id: Optional[str], payload_hash: str,
                        status_code: int, response_data: Any, ttl_seconds: Optional[int] = None) -> None:
        """Cache the successful response for the idempotency key."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        with self._lock:
            self._store[key] = IdempotencyRecord(
                key=key,
                user_id=user_id,
                payload_hash=payload_hash,
                status_code=status_code,
                response_data=response_data,
                ttl_seconds=ttl,
            )

    def get(self, key: str, payload: Any, user_id: Optional[str] = None) -> Optional[Any]:
        """Convenience helper to check and retrieve cached response."""
        p_hash = self.compute_payload_hash(payload)
        res = self.check_key(key, user_id, p_hash)
        return res[1] if res else None

    def set(self, key: str, payload: Any, response_data: Any,
            status_code: int = 200, user_id: Optional[str] = None, ttl_seconds: Optional[int] = None) -> None:
        """Convenience helper to record response."""
        p_hash = self.compute_payload_hash(payload)
        self.record_response(key, user_id, p_hash, status_code, response_data, ttl_seconds)

    def reset(self) -> None:
        """Reset all idempotency records for test isolation."""
        with self._lock:
            self._store.clear()


# Global singleton instance and alias
idempotency_manager = IdempotencyManager()
idempotency_store = idempotency_manager
