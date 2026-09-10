"""
Real-time Security Event API endpoints.
WebSocket endpoint for live event streaming and session timeline REST endpoint.
"""
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token, get_current_user
from app.db.models import UserModel, SecurityEventModel, QDSSessionModel
from app.realtime.manager import ws_manager

router = APIRouter(prefix="/realtime", tags=["Real-Time Events"])


@router.websocket("/security-events")
async def security_events_ws(websocket: WebSocket):
    """
    WebSocket endpoint for real-time security event streaming.

    Authentication: JWT token passed as query parameter 'token'.
    Role-based filtering applied by the WebSocket manager:
    - ADMIN / SECURITY_ANALYST: receive all events
    - USER: receive only events for their own sessions
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Authentication token required")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = payload.get("user_id", "")
    role = payload.get("role", "USER")
    username = payload.get("sub", "")

    await ws_manager.connect(websocket, user_id, role)
    try:
        # Send connection acknowledgment
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "user": username,
            "role": role,
            "message": "Connected to QDS Security Event Stream"
        })

        # Keep connection alive — listen for client messages (ping/pong)
        while True:
            data = await websocket.receive_text()
            # Echo ping as pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@router.get(
    "/sessions/{session_id}/timeline",
    summary="Get chronological event timeline for a QDS session"
)
def get_session_timeline(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns chronologically ordered security events for a specific QDS session.

    RBAC:
    - USER: only own sessions
    - SECURITY_ANALYST / ADMIN: any session
    """
    # RBAC: Check session ownership for regular users
    user_role = (current_user.role or "").upper()
    if user_role not in ("ADMIN", "SECURITY_ANALYST"):
        db_session = db.query(QDSSessionModel).filter(
            QDSSessionModel.session_id == session_id
        ).first()
        if db_session and db_session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not own this session"
            )

    # Fetch events chronologically
    events = db.query(SecurityEventModel).filter(
        SecurityEventModel.session_id == session_id
    ).order_by(SecurityEventModel.created_at.asc()).limit(limit).all()

    timeline = []
    for evt in events:
        try:
            meta = json.loads(evt.metadata_json) if evt.metadata_json else {}
        except Exception:
            meta = {}

        timeline.append({
            "event_id": evt.event_id,
            "event_type": evt.event_type,
            "severity": evt.severity,
            "message": evt.message,
            "timestamp": evt.created_at.isoformat() if evt.created_at else None,
            "metadata": meta,
        })

    return {
        "session_id": session_id,
        "events": timeline,
        "count": len(timeline),
    }
