"""
Incident CRUD Service.
Provides creation, retrieval, update, and status transition for security incidents.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.db.models import IncidentModel


# Valid status values and allowed transitions
VALID_STATUSES = {"OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

# Allowed status transitions (deterministic state machine)
STATUS_TRANSITIONS = {
    "OPEN": {"INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"},
    "INVESTIGATING": {"RESOLVED", "FALSE_POSITIVE", "OPEN"},
    "RESOLVED": {"OPEN"},  # Can reopen
    "FALSE_POSITIVE": {"OPEN"},  # Can reopen
}


def create_incident(
    db: Session,
    title: str,
    description: str,
    severity: str,
    source_session_id: Optional[str] = None,
    source_user_id: Optional[str] = None,
    status: str = "OPEN",
) -> IncidentModel:
    """
    Creates a new security incident.
    Validates severity and status against allowed values.
    """
    severity = severity.upper() if severity else "MEDIUM"
    if severity not in VALID_SEVERITIES:
        severity = "MEDIUM"

    status = status.upper() if status else "OPEN"
    if status not in VALID_STATUSES:
        status = "OPEN"

    incident_id = f"inc-{uuid.uuid4().hex[:12]}"
    incident = IncidentModel(
        id=f"db-inc-{uuid.uuid4().hex[:8]}",
        incident_id=incident_id,
        title=title,
        description=description,
        severity=severity,
        status=status,
        source_session_id=source_session_id,
        source_user_id=source_user_id,
        event_count=1,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_incidents(
    db: Session,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> Dict[str, Any]:
    """
    Retrieves incidents with optional severity/status filters.
    Returns dict with incidents list and total_count.
    """
    query = db.query(IncidentModel)

    if severity:
        query = query.filter(IncidentModel.severity == severity.upper())
    if status:
        query = query.filter(IncidentModel.status == status.upper())

    total = query.count()
    incidents = query.order_by(IncidentModel.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "incidents": [_incident_to_dict(inc) for inc in incidents],
        "total_count": total,
    }


def get_incident(db: Session, incident_id: str) -> Optional[IncidentModel]:
    """Retrieves a single incident by incident_id."""
    return db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()


def update_incident(
    db: Session,
    incident_id: str,
    status: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[IncidentModel]:
    """
    Updates an incident's status, assignment, or description.
    Validates status transitions against the deterministic state machine.
    """
    incident = get_incident(db, incident_id)
    if not incident:
        return None

    if status:
        status = status.upper()
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        current_status = incident.status.upper()
        allowed = STATUS_TRANSITIONS.get(current_status, set())
        if status not in allowed and status != current_status:
            raise ValueError(
                f"Invalid status transition: {current_status} → {status}. "
                f"Allowed: {', '.join(sorted(allowed))}"
            )

        incident.status = status
        if status in ("RESOLVED", "FALSE_POSITIVE"):
            incident.resolved_at = datetime.now(timezone.utc)

    if assigned_to_user_id is not None:
        incident.assigned_to_user_id = assigned_to_user_id

    if description is not None:
        incident.description = description

    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    return incident


def _incident_to_dict(incident: IncidentModel) -> Dict[str, Any]:
    """Converts IncidentModel to a safe dictionary."""
    return {
        "id": incident.id,
        "incident_id": incident.incident_id,
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity,
        "status": incident.status,
        "source_session_id": incident.source_session_id,
        "source_user_id": incident.source_user_id,
        "event_count": incident.event_count,
        "created_at": incident.created_at.isoformat() if incident.created_at else None,
        "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "assigned_to_user_id": incident.assigned_to_user_id,
    }


def get_session_events(db: Session, session_id: str) -> List[Dict[str, Any]]:
    """Retrieves chronological security events for a given session_id."""
    import json
    from app.db.models import SecurityEventModel
    events = (
        db.query(SecurityEventModel)
        .filter(SecurityEventModel.session_id == session_id)
        .order_by(SecurityEventModel.created_at.asc())
        .all()
    )
    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "event_type": e.event_type,
            "severity": e.severity,
            "timestamp": e.created_at.isoformat() if e.created_at else None,
            "session_id": e.session_id,
            "user_id": e.user_id,
            "message": e.message,
            "metadata": json.loads(e.metadata_json) if e.metadata_json else {},
        }
        for e in events
    ]
