"""
Phase 9: Security Audit REST API Endpoints.
Provides queryable audit logs with RBAC:
- ADMIN: inspects all system audit records
- SECURITY_ANALYST: inspects all security/audit logs
- USER: restricted strictly to own actor records
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models import UserModel
from app.db.schemas import AuditLogListResponse
from app.audit import service as audit_service

router = APIRouter(prefix="/audit", tags=["Security Audit"])


@router.get(
    "/logs",
    summary="Query security audit trail",
    description="Retrieve structured security audit logs. RBAC enforced based on user role."
)
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by audit action"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, LOW, MEDIUM, HIGH, CRITICAL)"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (SUCCESS, FAILURE, DENIED)"),
    request_id: Optional[str] = Query(None, description="Filter by correlation request ID"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Query audit logs. Regular users only see their own audit events;
    Analyst and Admin users view full security audit trail.
    """
    user_role = (current_user.role or "").upper()
    actor_filter = None

    if user_role not in ("ADMIN", "SECURITY_ANALYST"):
        actor_filter = current_user.id

    result = audit_service.get_audit_logs(
        db=db,
        action=action,
        severity=severity,
        outcome=outcome,
        actor_user_id=actor_filter,
        request_id=request_id,
        limit=limit,
        skip=skip,
    )

    return {
        "success": True,
        "data": result,
        "audit_logs": result["audit_logs"],
        "total_count": result["total_count"],
        "limit": result["limit"],
        "skip": result["skip"],
    }
