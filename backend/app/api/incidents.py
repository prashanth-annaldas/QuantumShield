"""
Security Incident Management API endpoints.
Provides CRUD for incidents with RBAC enforcement.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.db.models import UserModel, IncidentModel
from app.db.schemas import IncidentUpdateRequest
from app.incidents import service as incident_service

router = APIRouter(prefix="/incidents", tags=["Incident Management"])


@router.get(
    "",
    summary="List security incidents"
)
def list_incidents(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_role("SECURITY_ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Retrieves incidents with optional severity/status filters.
    RBAC: SECURITY_ANALYST and ADMIN only.
    """
    result = incident_service.get_incidents(
        db=db,
        severity=severity,
        status=status_filter,
        limit=limit,
        skip=skip,
    )
    return {
        "success": True,
        "data": result,
    }


@router.get(
    "/{incident_id}",
    summary="Get incident details"
)
def get_incident_detail(
    incident_id: str,
    current_user: UserModel = Depends(require_role("SECURITY_ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Retrieves a single incident by incident_id.
    RBAC: SECURITY_ANALYST and ADMIN only.
    """
    incident = incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found"
        )

    return {
        "success": True,
        "data": incident_service._incident_to_dict(incident),
    }


@router.patch(
    "/{incident_id}",
    summary="Update incident status or assignment"
)
def update_incident(
    incident_id: str,
    req: IncidentUpdateRequest,
    current_user: UserModel = Depends(require_role("SECURITY_ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Updates an incident's status, assignment, or description.
    Validates status transitions against the deterministic state machine.
    RBAC: SECURITY_ANALYST and ADMIN only.
    """
    try:
        incident = incident_service.update_incident(
            db=db,
            incident_id=incident_id,
            status=req.status,
            assigned_to_user_id=req.assigned_to_user_id,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found"
        )

    return {
        "success": True,
        "data": incident_service._incident_to_dict(incident),
    }
