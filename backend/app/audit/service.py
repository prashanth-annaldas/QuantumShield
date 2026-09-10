"""
Phase 9: Security Audit Persistence & Query Service.
Handles safe database persistence of audit events and provides filtered querying.
Guarantees audit failure NEVER crashes application API execution.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.db.models import AuditLogModel
from app.audit.logger import log_security_audit, sanitize_audit_metadata
from app.core.request_context import get_request_id, get_actor_user_id, get_actor_role

logger = logging.getLogger(__name__)


def record_audit_event(
    db: Session,
    action: str,
    outcome: str = "SUCCESS",
    severity: str = "INFO",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    actor_username: Optional[str] = None,
    **kwargs: Any,
) -> Optional[AuditLogModel]:
    """
    Persists an audit event to the database and emits a structured JSON log.
    Wrapped in safe error handling: failure to record an audit log will never
    abort the business transaction.
    """
    req_id = request_id or get_request_id()
    user_id = actor_user_id or get_actor_user_id()
    role = actor_role or get_actor_role()
    
    combined_meta = dict(metadata or {})
    if details:
        combined_meta.update(details)
    if actor_username:
        combined_meta["actor_username"] = actor_username
    if kwargs:
        combined_meta.update(kwargs)

    clean_meta = sanitize_audit_metadata(combined_meta)

    # 1. Emit structured log
    log_security_audit(
        action=action,
        outcome=outcome,
        severity=severity,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_user_id=user_id,
        actor_role=role,
        metadata=clean_meta,
        request_id=req_id,
    )

    # 2. Persist to database safely
    try:
        event_id = f"aud-{uuid.uuid4().hex[:12]}"
        audit_entry = AuditLogModel(
            id=f"rec-{uuid.uuid4().hex[:8]}",
            event_id=event_id,
            request_id=req_id,
            actor_user_id=user_id,
            actor_role=role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            severity=severity,
            metadata_json=json.dumps(clean_meta),
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception as exc:
        logger.error(f"Failed to persist audit log entry for action '{action}': {exc}", exc_info=False)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def get_audit_logs(
    db: Session,
    action: Optional[str] = None,
    severity: Optional[str] = None,
    outcome: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 50,
    skip: int = 0,
) -> Dict[str, Any]:
    """
    Queries audit logs with pagination and filters.
    """
    query = db.query(AuditLogModel)

    if action:
        query = query.filter(AuditLogModel.action == action.upper())
    if severity:
        query = query.filter(AuditLogModel.severity == severity.upper())
    if outcome:
        query = query.filter(AuditLogModel.outcome == outcome.upper())
    if actor_user_id:
        query = query.filter(AuditLogModel.actor_user_id == actor_user_id)
    if request_id:
        query = query.filter(AuditLogModel.request_id == request_id)
    if start_time:
        query = query.filter(AuditLogModel.created_at >= start_time)
    if end_time:
        query = query.filter(AuditLogModel.created_at <= end_time)

    total_count = query.count()
    records = query.order_by(AuditLogModel.created_at.desc()).offset(skip).limit(limit).all()

    formatted_logs = []
    for r in records:
        try:
            meta = json.loads(r.metadata_json) if r.metadata_json else {}
        except Exception:
            meta = {}

        formatted_logs.append({
            "id": r.id,
            "event_id": r.event_id,
            "request_id": r.request_id,
            "actor_user_id": r.actor_user_id,
            "actor_role": r.actor_role,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "outcome": r.outcome,
            "severity": r.severity,
            "metadata": meta,
            "created_at": r.created_at,
        })

    return {
        "audit_logs": formatted_logs,
        "logs": formatted_logs,
        "total_count": total_count,
        "limit": limit,
        "skip": skip,
    }
