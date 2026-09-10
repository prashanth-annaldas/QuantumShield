"""
Phase 8: Real-time Security Event System.
Provides WebSocket event streaming, connection management, and centralized event publishing.
"""
from app.realtime.events import SecurityEvent, SecurityEventType, SecurityEventSeverity
from app.realtime.manager import ws_manager
from app.realtime.publisher import publish_security_event

__all__ = [
    "SecurityEvent",
    "SecurityEventType",
    "SecurityEventSeverity",
    "ws_manager",
    "publish_security_event",
]
