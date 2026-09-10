"""
Central Security Event Publisher.
Single entry point for publishing security events to both database and WebSocket.
Decouples event production from transport — routes call publish_security_event()
without knowing about WebSocket or database internals.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any

from app.realtime.events import SecurityEvent, SecurityEventType, SecurityEventSeverity
from app.realtime.manager import ws_manager

logger = logging.getLogger(__name__)

# Flag to control DB persistence (can be disabled during unit tests)
_persistence_enabled = True


def set_persistence_enabled(enabled: bool) -> None:
    """Toggle database persistence for testing isolation."""
    global _persistence_enabled
    _persistence_enabled = enabled


def publish_security_event(
    event_type: str,
    severity: str,
    message: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db=None,
) -> SecurityEvent:
    """
    Central event publishing function.

    1. Creates a SecurityEvent instance
    2. Persists to SecurityEventModel in database (if db session provided)
    3. Broadcasts to connected WebSocket clients (fire-and-forget async)

    Args:
        event_type: One of SecurityEventType constants
        severity: One of SecurityEventSeverity constants
        message: Human-readable event description
        session_id: Optional QDS session reference
        user_id: Optional user who triggered the event
        metadata: Optional safe metadata dict (no secrets)
        db: Optional SQLAlchemy session for persistence

    Returns:
        The created SecurityEvent instance
    """
    # Create event
    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        message=message,
        session_id=session_id,
        user_id=user_id,
        metadata=metadata or {},
    )

    # Persist to database if session provided and persistence enabled
    if db is not None and _persistence_enabled:
        try:
            _persist_event(db, event)
        except Exception as e:
            logger.error(f"Failed to persist security event {event.event_id}: {e}")

    # Broadcast to WebSocket clients (fire-and-forget)
    _schedule_broadcast(event)

    return event


def _persist_event(db, event: SecurityEvent) -> None:
    """Persist a SecurityEvent to the database via SecurityEventModel."""
    # Lazy import to avoid circular dependency at module load time
    from app.db.models import SecurityEventModel

    safe_metadata = event.metadata or {}
    # Strip sensitive keys before persistence
    for key in ("password", "token", "secret", "jwt", "password_hash", "authorization"):
        safe_metadata.pop(key, None)

    db_event = SecurityEventModel(
        id=event.event_id,
        event_id=event.event_id,
        event_type=event.event_type,
        severity=event.severity,
        session_id=event.session_id,
        user_id=event.user_id,
        message=event.message,
        metadata_json=json.dumps(safe_metadata, default=str),
    )
    db.add(db_event)
    db.commit()


def _schedule_broadcast(event: SecurityEvent) -> None:
    """
    Schedule async WebSocket broadcast without blocking the sync caller.
    Gracefully handles the case where no event loop is running (e.g., unit tests).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast(event))
    except RuntimeError:
        # No running event loop — skip broadcast (e.g., during unit tests)
        pass
