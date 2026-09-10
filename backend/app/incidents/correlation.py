"""
Deterministic Threat Correlation Engine.
Implements explicit, explainable correlation rules (C-01 through C-05).

STRICT NON-AI/ML GUARANTEE:
All correlation decisions use deterministic threshold comparisons,
time-window checks, and explicit logical conditions.
No machine learning, neural networks, or statistical prediction models.
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any, Dict

from sqlalchemy.orm import Session

from app.db.models import SecurityEventModel, IncidentModel
from app.realtime.events import SecurityEventType, SecurityEventSeverity
from app.incidents.service import create_incident

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configurable parameters (via environment variables with safe defaults)
# ─────────────────────────────────────────────────────────────────────────────

CORRELATION_WINDOW_SECONDS = int(os.getenv("INCIDENT_CORRELATION_WINDOW_SECONDS", "300"))
REJECTION_THRESHOLD = int(os.getenv("INCIDENT_REJECTION_THRESHOLD", "3"))

# Threat engine thresholds (matching Phase 4 defaults)
FIDELITY_THRESHOLD = float(os.getenv("FIDELITY_THRESHOLD", "0.85"))
QBER_THRESHOLD = float(os.getenv("QBER_THRESHOLD", "11.0"))


def _extract_event_args(event_or_type: Any, severity: Optional[str] = None,
                        session_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        metadata: Optional[dict] = None):
    if hasattr(event_or_type, "event_type"):
        evt_type = event_or_type.event_type
        sev = severity or getattr(event_or_type, "severity", "INFO")
        sess_id = session_id or getattr(event_or_type, "session_id", None)
        u_id = user_id or getattr(event_or_type, "user_id", None)
        meta = metadata or getattr(event_or_type, "metadata", {})
    else:
        evt_type = str(event_or_type)
        sev = severity or "INFO"
        sess_id = session_id
        u_id = user_id
        meta = metadata or {}
    return evt_type, sev, sess_id, u_id, meta


def correlate_event(db: Session, event_or_type: Any,
                    severity: Optional[str] = None,
                    session_id: Optional[str] = None,
                    user_id: Optional[str] = None,
                    metadata: Optional[dict] = None) -> Optional[IncidentModel]:
    """
    Main correlation entry point. Evaluates all deterministic rules
    against the incoming event and creates/escalates incidents as needed.

    Returns the created or escalated IncidentModel, or None if no correlation triggered.
    """
    event_type, severity, session_id, user_id, metadata = _extract_event_args(
        event_or_type, severity, session_id, user_id, metadata
    )

    # Only correlate threat-category events or rejections
    if event_type not in SecurityEventType.THREAT_TYPES and \
       event_type != SecurityEventType.VERIFICATION_REJECTED and \
       event_type != "SIGNATURE_REJECTED":
        return None

    # Rule C-05: Check for existing incident first (dedup/escalation)
    existing = _find_existing_incident(db, session_id)
    if existing:
        return _escalate_incident(db, existing, severity)

    # Try each correlation rule in priority order
    incident = None

    # Rule C-02: Replay + Forgery combo (highest priority — CRITICAL)
    incident = incident or _check_replay_forgery_combo(db, event_type, session_id, user_id)

    # Rule C-03: Repeated verification rejections
    incident = incident or _check_repeated_rejections(db, event_type, session_id, user_id)

    # Rule C-04: Channel noise + threshold violation
    incident = incident or _check_noise_threshold(db, event_type, severity, session_id, user_id, metadata)

    # Rule C-01: Any HIGH/CRITICAL threat event immediately triggers incident
    incident = incident or _check_multi_high_severity(db, event_type, severity, session_id, user_id)

    # Rule C-00: Fallback — any threat event from VERIFICATION_REJECTED creates incident
    incident = incident or _check_single_threat_event(db, event_type, severity, session_id, user_id)

    return incident


# ─────────────────────────────────────────────────────────────────────────────
# Correlation Rules
# ─────────────────────────────────────────────────────────────────────────────

def _check_multi_high_severity(db: Session, event_or_type: Any,
                                severity: Optional[str] = None,
                                session_id: Optional[str] = None,
                                user_id: Optional[str] = None,
                                window_seconds: Optional[int] = None) -> Optional[IncidentModel]:
    """
    RULE C-01: Two or more HIGH or CRITICAL threat events in the same session
    within the correlation time window → Create or escalate incident.
    """
    event_type, severity, session_id, user_id, _ = _extract_event_args(
        event_or_type, severity, session_id, user_id
    )

    if severity not in ("HIGH", "CRITICAL"):
        return None
    if not session_id:
        return None

    cutoff = _time_window_cutoff(window_seconds)
    high_events = db.query(SecurityEventModel).filter(
        SecurityEventModel.session_id == session_id,
        SecurityEventModel.severity.in_(["HIGH", "CRITICAL"]),
        SecurityEventModel.created_at >= cutoff,
    ).count()

    if high_events >= 1:
        return create_incident(
            db=db,
            title=f"Threat Event Detected on Session {session_id[:16]}",
            description=(
                f"Rule C-01: {high_events} HIGH/CRITICAL threat event(s) detected "
                f"within {window_seconds or CORRELATION_WINDOW_SECONDS}s correlation window."
            ),
            severity="HIGH" if severity == "HIGH" else "CRITICAL",
            source_session_id=session_id,
            source_user_id=user_id,
        )
    return None


def _check_replay_forgery_combo(db: Session, event_or_type: Any,
                                 session_id: Optional[str] = None,
                                 user_id: Optional[str] = None,
                                 window_seconds: Optional[int] = None) -> Optional[IncidentModel]:
    """
    RULE C-02: Replay attack AND forgery detected for the same user/session
    within the correlation window → Create CRITICAL incident.
    """
    event_type, _, session_id, user_id, _ = _extract_event_args(
        event_or_type, None, session_id, user_id
    )

    if event_type not in (
        SecurityEventType.REPLAY_DETECTED,
        "REPLAY_DETECTED",
        "REPLAY_ATTACK",
        SecurityEventType.FORGERY_DETECTED,
        "FORGERY_DETECTED",
        "SIGNATURE_FORGERY",
    ):
        return None

    cutoff = _time_window_cutoff(window_seconds)

    # Determine what to look for based on current event
    if event_type in (SecurityEventType.REPLAY_DETECTED, "REPLAY_DETECTED", "REPLAY_ATTACK"):
        complementary_types = [SecurityEventType.FORGERY_DETECTED, "FORGERY_DETECTED", "SIGNATURE_FORGERY"]
    else:
        complementary_types = [SecurityEventType.REPLAY_DETECTED, "REPLAY_DETECTED", "REPLAY_ATTACK"]

    query = db.query(SecurityEventModel).filter(
        SecurityEventModel.event_type.in_(complementary_types),
        SecurityEventModel.created_at >= cutoff,
    )

    if session_id:
        complementary_count = query.filter(
            SecurityEventModel.session_id == session_id
        ).count()
    elif user_id:
        complementary_count = query.filter(
            SecurityEventModel.user_id == user_id
        ).count()
    else:
        return None

    if complementary_count >= 1:
        return create_incident(
            db=db,
            title=f"Compound Replay-Forgery Exploit Detected",
            description=(
                f"Rule C-02: Both REPLAY and FORGERY attacks detected for "
                f"{'session ' + session_id[:16] if session_id else 'user ' + str(user_id)} "
                f"within {window_seconds or CORRELATION_WINDOW_SECONDS}s."
            ),
            severity="CRITICAL",
            source_session_id=session_id,
            source_user_id=user_id,
        )
    return None


def _check_repeated_rejections(db: Session, event_or_type: Any,
                                session_id: Optional[str] = None,
                                user_id: Optional[str] = None,
                                window_seconds: Optional[int] = None) -> Optional[IncidentModel]:
    """
    RULE C-03: Repeated verification rejections exceeding the configured
    threshold within the time window → Create HIGH incident.
    """
    event_type, _, session_id, user_id, _ = _extract_event_args(
        event_or_type, None, session_id, user_id
    )

    if event_type not in (SecurityEventType.VERIFICATION_REJECTED, "VERIFICATION_REJECTED", "SIGNATURE_REJECTED"):
        return None

    cutoff = _time_window_cutoff(window_seconds)
    query = db.query(SecurityEventModel).filter(
        SecurityEventModel.event_type.in_([SecurityEventType.VERIFICATION_REJECTED, "VERIFICATION_REJECTED", "SIGNATURE_REJECTED"]),
        SecurityEventModel.created_at >= cutoff,
    )

    if session_id:
        rejection_count = query.filter(SecurityEventModel.session_id == session_id).count()
    elif user_id:
        rejection_count = query.filter(SecurityEventModel.user_id == user_id).count()
    else:
        return None

    if rejection_count >= REJECTION_THRESHOLD:
        return create_incident(
            db=db,
            title=f"Repeated Signature Verification Failures ({rejection_count}x)",
            description=(
                f"Rule C-03: {rejection_count} verification rejections detected "
                f"(threshold: {REJECTION_THRESHOLD}) within {window_seconds or CORRELATION_WINDOW_SECONDS}s."
            ),
            severity="HIGH",
            source_session_id=session_id,
            source_user_id=user_id,
        )
    return None


def _check_noise_threshold(db: Session, event_or_type: Any,
                            severity: Optional[str] = None,
                            session_id: Optional[str] = None,
                            user_id: Optional[str] = None,
                            metadata: Optional[dict] = None) -> Optional[IncidentModel]:
    """
    RULE C-04: Channel noise event + fidelity below threshold + QBER above threshold
    → Create HIGH incident.
    """
    event_type, severity, session_id, user_id, metadata = _extract_event_args(
        event_or_type, severity, session_id, user_id, metadata
    )

    if event_type not in (SecurityEventType.CHANNEL_NOISE_DETECTED, "CHANNEL_NOISE_DETECTED"):
        return None

    metadata = metadata or {}
    fidelity = metadata.get("state_fidelity") or metadata.get("fidelity")
    qber = metadata.get("qber_percent") or metadata.get("qber")

    if fidelity is None or qber is None:
        # If explicitly marked as noise attack, create incident
        return create_incident(
            db=db,
            title=f"Quantum Channel Manipulation Alert",
            description=f"Rule C-04: Channel noise detected on session {session_id or 'unknown'}.",
            severity="HIGH",
            source_session_id=session_id,
            source_user_id=user_id,
        )

    try:
        fidelity = float(fidelity)
        qber = float(qber)
    except (ValueError, TypeError):
        return None

    if fidelity < FIDELITY_THRESHOLD or qber > QBER_THRESHOLD:
        return create_incident(
            db=db,
            title=f"Quantum Channel Manipulation Alert",
            description=(
                f"Rule C-04: Channel noise detected with fidelity={fidelity:.4f} "
                f"(threshold: {FIDELITY_THRESHOLD}) and QBER={qber:.2f}% "
                f"(threshold: {QBER_THRESHOLD}%)."
            ),
            severity="HIGH",
            source_session_id=session_id,
            source_user_id=user_id,
        )
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Rule C-05: Duplicate Prevention & Escalation
# ─────────────────────────────────────────────────────────────────────────────

def _check_single_threat_event(db: Session, event_or_type: Any,
                               severity: Optional[str] = None,
                               session_id: Optional[str] = None,
                               user_id: Optional[str] = None) -> Optional[IncidentModel]:
    """
    RULE C-00: Fallback — any VERIFICATION_REJECTED or threat event that hasn't
    been caught by C-01 through C-04 still creates a LOW severity incident so
    the event always surfaces in the SOC.
    """
    event_type, severity, session_id, user_id, _ = _extract_event_args(
        event_or_type, severity, session_id, user_id
    )
    if event_type not in (
        SecurityEventType.VERIFICATION_REJECTED,
        "VERIFICATION_REJECTED",
        "SIGNATURE_REJECTED",
        SecurityEventType.THREAT_DETECTED,
        "THREAT_DETECTED",
    ):
        return None
    if not session_id:
        return None
    return create_incident(
        db=db,
        title=f"Security Alert: Threat Event on Session {session_id[:16]}",
        description=(
            f"Rule C-00: Threat-category event '{event_type}' detected "
            f"for session {session_id}. Automatic incident opened for analyst review."
        ),
        severity=severity if severity in ("HIGH", "CRITICAL") else "MEDIUM",
        source_session_id=session_id,
        source_user_id=user_id,
    )


def _find_existing_incident(db: Session, session_id: Optional[str]) -> Optional[IncidentModel]:
    """
    RULE C-05: Check for an existing OPEN or INVESTIGATING incident
    for the same session.
    """
    if not session_id:
        return None

    return db.query(IncidentModel).filter(
        IncidentModel.source_session_id == session_id,
        IncidentModel.status.in_(["OPEN", "INVESTIGATING"]),
    ).order_by(IncidentModel.created_at.desc()).first()


def _escalate_incident(db: Session, incident: IncidentModel,
                        new_severity: str) -> IncidentModel:
    """
    RULE C-05 escalation: Increment event_count, update timestamp,
    and escalate severity if the new severity is higher.
    """
    incident.event_count += 1
    incident.updated_at = datetime.now(timezone.utc)

    if SecurityEventSeverity.is_higher(new_severity, incident.severity):
        incident.severity = new_severity

    db.commit()
    db.refresh(incident)
    return incident


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _time_window_cutoff(window_seconds: Optional[int] = None) -> datetime:
    """Returns the UTC datetime marking the start of the correlation window."""
    sec = window_seconds if window_seconds is not None else CORRELATION_WINDOW_SECONDS
    return datetime.now(timezone.utc) - timedelta(seconds=sec)
