"""
Security Event Model and Type Constants.
Defines typed event structures for the real-time security event system.
All event types are explicit string constants — no AI/ML classification.
"""
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class SecurityEventType:
    """Explicit string constants for all security event types."""
    # QDS Protocol Events
    SIGNATURE_CREATED = "SIGNATURE_CREATED"
    SIGNATURE_ENCODED = "SIGNATURE_ENCODED"
    BELL_PAIR_CREATED = "BELL_PAIR_CREATED"
    TELEPORTATION_STARTED = "TELEPORTATION_STARTED"
    TELEPORTATION_COMPLETED = "TELEPORTATION_COMPLETED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_ACCEPTED = "VERIFICATION_ACCEPTED"
    VERIFICATION_REJECTED = "VERIFICATION_REJECTED"
    SIGNATURE_VERIFIED = "VERIFICATION_ACCEPTED"
    SIGNATURE_REJECTED = "VERIFICATION_REJECTED"

    # Threat Events
    THREAT_SIMULATION_STARTED = "THREAT_SIMULATION_STARTED"
    THREAT_DETECTED = "THREAT_DETECTED"
    FORGERY_DETECTED = "FORGERY_DETECTED"
    IMPERSONATION_DETECTED = "IMPERSONATION_DETECTED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    REPLAY_ATTACK_DETECTED = "REPLAY_DETECTED"
    CHANNEL_NOISE_DETECTED = "CHANNEL_NOISE_DETECTED"
    UNAUTHORIZED_ACCESS_DETECTED = "UNAUTHORIZED_ACCESS_DETECTED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS_DETECTED"

    # Incident Lifecycle Events
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_ESCALATED = "INCIDENT_ESCALATED"
    INCIDENT_UPDATED = "INCIDENT_UPDATED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"

    # System Events
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SYSTEM_HEALTH_CHANGED = "SYSTEM_HEALTH_CHANGED"

    # All event types for validation
    ALL_TYPES = {
        SIGNATURE_CREATED, SIGNATURE_ENCODED, BELL_PAIR_CREATED,
        TELEPORTATION_STARTED, TELEPORTATION_COMPLETED,
        VERIFICATION_STARTED, VERIFICATION_ACCEPTED, VERIFICATION_REJECTED,
        THREAT_SIMULATION_STARTED, THREAT_DETECTED,
        FORGERY_DETECTED, IMPERSONATION_DETECTED, REPLAY_DETECTED, CHANNEL_NOISE_DETECTED,
        UNAUTHORIZED_ACCESS_DETECTED,
        INCIDENT_CREATED, INCIDENT_ESCALATED, INCIDENT_UPDATED, INCIDENT_RESOLVED,
        RATE_LIMIT_EXCEEDED, SYSTEM_HEALTH_CHANGED,
    }

    # Threat-category event types (used by correlation engine)
    THREAT_TYPES = {
        THREAT_DETECTED, FORGERY_DETECTED, IMPERSONATION_DETECTED, REPLAY_DETECTED,
        CHANNEL_NOISE_DETECTED, UNAUTHORIZED_ACCESS_DETECTED,
    }


class SecurityEventSeverity:
    """Explicit severity levels for security events."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    ALL_SEVERITIES = {INFO, LOW, MEDIUM, HIGH, CRITICAL}

    # Numeric ranking for deterministic comparison
    _RANK = {INFO: 0, LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4}

    @classmethod
    def rank(cls, severity: str) -> int:
        """Returns numeric rank for deterministic severity comparison."""
        return cls._RANK.get(severity, 0)

    @classmethod
    def is_higher(cls, a: str, b: str) -> bool:
        """Returns True if severity 'a' is strictly higher than 'b'."""
        return cls.rank(a) > cls.rank(b)


@dataclass
class SecurityEvent:
    """
    Typed security event structure for the real-time event system.
    Safe for serialization — never contains JWT tokens, passwords, or secrets.
    """
    event_type: str
    severity: str
    message: str
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes event to a safe dictionary.
        Explicitly excludes any sensitive fields.
        """
        d = asdict(self)
        # Safety: strip any accidentally included sensitive keys from metadata
        if d.get("metadata"):
            for sensitive_key in ("password", "token", "secret", "jwt", "password_hash", "authorization"):
                d["metadata"].pop(sensitive_key, None)
        return d

    def to_json(self) -> str:
        """Serializes event to a safe JSON string."""
        import json
        return json.dumps(self.to_dict())

    def to_json_safe(self) -> Dict[str, Any]:
        """Alias for to_dict() — returns JSON-safe dictionary."""
        return self.to_dict()
