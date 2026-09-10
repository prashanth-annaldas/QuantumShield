"""
SQLAlchemy ORM models for Users, QDS Sessions, Verification Results, and Threat Logs.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, synonym
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), default="USER", nullable=False)  # USER, SECURITY_ANALYST, ADMIN
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)

    # Relationships
    sessions = relationship("QDSSessionModel", back_populates="user", cascade="all, delete-orphan")


class QDSSessionModel(Base):
    __tablename__ = "qds_sessions"

    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    sender_id = Column(String(64), nullable=True)
    message = Column(Text, nullable=True)
    message_hash = Column(String(64), nullable=False)
    nonce = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, ENCODED, TELEPORTED, VERIFIED, REJECTED
    verification_attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="sessions")
    verification_results = relationship("VerificationResultModel", back_populates="session", cascade="all, delete-orphan")
    threat_logs = relationship("ThreatLogModel", back_populates="session", cascade="all, delete-orphan")


class VerificationResultModel(Base):
    __tablename__ = "verification_results"

    id = Column(String(36), primary_key=True, index=True)
    qds_session_id = Column(String(64), ForeignKey("qds_sessions.session_id"), nullable=False, index=True)
    fidelity = Column(Float, nullable=False)
    qber = Column(Float, nullable=False)
    mismatch_rate = Column(Float, nullable=False)
    statistical_deviation = Column(Float, default=0.0, nullable=False)
    forgery_probability = Column(Float, default=0.0, nullable=False)
    verification_accuracy = Column(Float, default=1.0, nullable=False)
    decision = Column(String(32), nullable=False)  # LEGITIMATE, SUSPICIOUS, MALICIOUS
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)

    # Relationships
    session = relationship("QDSSessionModel", back_populates="verification_results")


class ThreatLogModel(Base):
    __tablename__ = "threat_logs"

    id = Column(String(36), primary_key=True, index=True)
    qds_session_id = Column(String(64), ForeignKey("qds_sessions.session_id"), nullable=False, index=True)
    attack_type = Column(String(64), nullable=False, index=True)  # FORGERY, IMPERSONATION, REPLAY, CHANNEL_MANIPULATION, UNAUTHORIZED_VERIFICATION, NONE
    severity = Column(String(32), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    decision = Column(String(32), nullable=False)                 # LEGITIMATE, SUSPICIOUS, MALICIOUS
    reason = Column(Text, nullable=True)
    
    # Detailed telemetry columns
    qber_percent = Column(Float, default=0.0, nullable=False)
    state_fidelity = Column(Float, default=1.0, nullable=False)
    mismatch_rate = Column(Float, default=0.0, nullable=False)
    details_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)

    # Synonyms for backward compatibility
    session_id = synonym("qds_session_id")
    threat_type = synonym("attack_type")

    # Relationships
    session = relationship("QDSSessionModel", back_populates="threat_logs")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8: Security Event & Incident Models
# ─────────────────────────────────────────────────────────────────────────────

class SecurityEventModel(Base):
    """Persisted security event for audit trail and session timeline reconstruction."""
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, index=True)
    event_id = Column(String(36), unique=True, index=True, nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    message = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)


class IncidentModel(Base):
    """Security incident created by deterministic correlation rules."""
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, index=True)
    incident_id = Column(String(36), unique=True, index=True, nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(16), nullable=False, index=True)   # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), default="OPEN", nullable=False, index=True)  # OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    source_session_id = Column(String(64), nullable=True, index=True)
    source_user_id = Column(String(36), nullable=True)
    event_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to_user_id = Column(String(36), nullable=True)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9: Structured Security Audit Log Model
# ─────────────────────────────────────────────────────────────────────────────

class AuditLogModel(Base):
    """
    Persistent audit trail for all security-sensitive operations.
    Captures actor, action, resource, outcome, and request correlation IDs.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, index=True)
    event_id = Column(String(36), unique=True, index=True, nullable=False)
    request_id = Column(String(64), index=True, nullable=False)
    actor_user_id = Column(String(36), index=True, nullable=True)
    actor_role = Column(String(32), nullable=True)
    action = Column(String(64), index=True, nullable=False)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(64), nullable=True)
    outcome = Column(String(16), default="SUCCESS", nullable=False)
    severity = Column(String(16), default="INFO", index=True, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)
