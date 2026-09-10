"""
Threat Simulation and Deterministic Threat Detection FastAPI endpoints.
Integrates with Phase 4 AttackSimulator and ThreatDecisionEngine.
"""
import uuid
import json
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, require_role
from app.core.rate_limiter import check_rate_limit
from app.monitoring.metrics import metrics_collector
from app.realtime.publisher import publish_security_event
from app.realtime.events import SecurityEventType, SecurityEventSeverity
from app.incidents.correlation import correlate_event
from app.db.models import UserModel, ThreatLogModel, QDSSessionModel
from app.db.schemas import (
    AttackSimulationRequest,
    ThreatDetectionRequest,
    ThreatDetectionResponse,
    ThreatLogResponse,
)
from app.api.qds import _get_or_restore_session, _check_session_access, global_threat_engine
from app.threats.simulator import AttackSimulator, AttackType
from app.qds.session import QDSStatus

router = APIRouter(prefix="/threats", tags=["Threat Management"])


@router.post(
    "/simulate",
    summary="Inject simulated cyber threats into a QDS session"
)
def simulate_attack(
    request: Request,
    req: AttackSimulationRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Simulates attacks against active QDS sessions:
    - FORGERY / SIGNATURE_FORGERY
    - IMPERSONATION / IMPERSONATION_ATTACK
    - REPLAY / REPLAY_ATTACK
    - CHANNEL_MANIPULATION / QUANTUM_CHANNEL_MANIPULATION
    - UNAUTHORIZED_VERIFICATION
    """
    check_rate_limit(request, "threat_simulate", settings.RATE_LIMIT_THREAT_PER_MINUTE)
    
    # Phase 9: Idempotency Key check
    from app.core.idempotency import idempotency_store
    idempotency_key = request.headers.get("Idempotency-Key")
    req_body_str = req.model_dump_json() if hasattr(req, "model_dump_json") else str(req.__dict__)
    if idempotency_key:
        cached_resp = idempotency_store.get(idempotency_key, req_body_str)
        if cached_resp:
            return cached_resp

    session = _get_or_restore_session(req.session_id, db)
    db_session = db.query(QDSSessionModel).filter(QDSSessionModel.session_id == req.session_id).first()
    if db_session:
        _check_session_access(db_session, current_user)

    if session.status == QDSStatus.ENCODED or session.status == "PENDING":
        session.run_teleportation(deterministic=True)

    attack_norm = req.attack_type.upper().strip()
    attack_details = {}

    if attack_norm in ("FORGERY", "SIGNATURE_FORGERY"):
        attack_details = AttackSimulator.inject_forgery(session, tamper_ratio=req.tamper_ratio or 0.15)
    elif attack_norm in ("IMPERSONATION", "IMPERSONATION_ATTACK"):
        attack_details = AttackSimulator.inject_impersonation(session)
    elif attack_norm in ("REPLAY", "REPLAY_ATTACK"):
        attack_details = AttackSimulator.inject_replay_attack(session)
    elif attack_norm in ("CHANNEL_MANIPULATION", "QUANTUM_CHANNEL_MANIPULATION"):
        attack_details = AttackSimulator.inject_quantum_channel_noise(session, error_rate=req.error_rate or 0.15)
    elif attack_norm in ("UNAUTHORIZED_VERIFICATION", "UNAUTHORIZED"):
        attack_details = AttackSimulator.inject_unauthorized_attempts(session)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported attack type '{req.attack_type}'. Must be one of: FORGERY, IMPERSONATION, REPLAY, CHANNEL_MANIPULATION, UNAUTHORIZED_VERIFICATION"
        )

    # Metrics
    metrics_collector.increment("threats_simulated")

    # Publish security event for simulation
    try:
        publish_security_event(
            db=db,
            event_type=SecurityEventType.THREAT_DETECTED,
            severity=SecurityEventSeverity.MEDIUM,
            session_id=session.session_id,
            user_id=current_user.id,
            message=f"Threat simulation injected: {attack_norm}",
            metadata={"attack_type": attack_norm, "details": attack_details}
        )
    except Exception:
        pass

    # Phase 9: Record Audit Event
    from app.audit.service import record_audit_event
    record_audit_event(
        db=db,
        action="THREAT_SIMULATED",
        severity="WARNING",
        outcome="SUCCESS",
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        actor_role=current_user.role,
        resource_type="QDS_SESSION",
        resource_id=session.session_id,
        details={
            "session_id": session.session_id,
            "attack_type": attack_norm,
            "details": attack_details
        }
    )

    resp_payload = {
        "success": True,
        "data": {
            "session_id": session.session_id,
            "injected_threat": attack_norm,
            "details": attack_details
        }
    }

    if idempotency_key:
        idempotency_store.set(idempotency_key, req_body_str, resp_payload)

    return resp_payload


@router.post(
    "/detect",
    response_model=ThreatDetectionResponse,
    summary="Run deterministic non-AI threat detection on a session"
)
def detect_threats(
    request: Request,
    req: ThreatDetectionRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreatDetectionResponse:
    """
    Invokes the deterministic Phase 4 ThreatDecisionEngine.
    Logs threat details to the database and runs correlation engine.
    """
    check_rate_limit(request, "threat_detect", settings.RATE_LIMIT_THREAT_PER_MINUTE)
    session = _get_or_restore_session(req.session_id, db)
    db_session = db.query(QDSSessionModel).filter(QDSSessionModel.session_id == req.session_id).first()
    if db_session:
        _check_session_access(db_session, current_user)

    if session.status == QDSStatus.ENCODED or session.status == "PENDING":
        session.run_teleportation(deterministic=True)

    authorized_sender = (db_session.sender_id if db_session and db_session.sender_id else session.sender_id)
    eval_result = global_threat_engine.evaluate_session(
        session,
        authorized_sender_id=authorized_sender
    )

    decision = eval_result["decision"]
    severity = "CRITICAL" if decision == "MALICIOUS" else ("HIGH" if decision == "SUSPICIOUS" else "LOW")
    attack_type = eval_result.get("threat_type", "NONE")
    reason = "; ".join(a.get("message", "") for a in eval_result.get("alerts", [])) or "Clean transmission"
    metrics = eval_result["metrics"]

    if decision != "LEGITIMATE":
        metrics_collector.increment("threats_detected")

    # Persist threat log
    log_entry = ThreatLogModel(
        id=f"log-{uuid.uuid4().hex[:8]}",
        qds_session_id=session.session_id,
        attack_type=attack_type,
        severity=severity,
        decision=decision,
        reason=reason,
        qber_percent=metrics.get("qber_percent", 0.0),
        state_fidelity=metrics.get("state_fidelity", 1.0),
        mismatch_rate=metrics.get("mismatch_rate", 0.0),
        details_json=json.dumps(eval_result)
    )
    db.add(log_entry)
    db.commit()

    # Determine specific SecurityEventType
    event_type_map = {
        "SIGNATURE_FORGERY": SecurityEventType.FORGERY_DETECTED,
        "IMPERSONATION_ATTACK": SecurityEventType.IMPERSONATION_DETECTED,
        "REPLAY_ATTACK": SecurityEventType.REPLAY_ATTACK_DETECTED,
        "QUANTUM_CHANNEL_MANIPULATION": SecurityEventType.CHANNEL_NOISE_DETECTED,
        "UNAUTHORIZED_VERIFICATION": SecurityEventType.UNAUTHORIZED_ACCESS,
    }
    sec_event_type = event_type_map.get(attack_type, SecurityEventType.THREAT_DETECTED if decision != "LEGITIMATE" else SecurityEventType.SIGNATURE_VERIFIED)
    sec_severity = (
        SecurityEventSeverity.CRITICAL if decision == "MALICIOUS"
        else (SecurityEventSeverity.HIGH if decision == "SUSPICIOUS" else SecurityEventSeverity.INFO)
    )

    # Publish event and run deterministic correlation
    try:
        sec_event = publish_security_event(
            db=db,
            event_type=sec_event_type,
            severity=sec_severity,
            session_id=session.session_id,
            user_id=current_user.id,
            message=f"Deterministic threat detection result: {decision} ({attack_type}) - {reason}",
            metadata={
                "attack_type": attack_type,
                "decision": decision,
                "fidelity": metrics.get("state_fidelity", 1.0),
                "qber": metrics.get("qber_percent", 0.0),
                "mismatch_rate": metrics.get("mismatch_rate", 0.0),
            }
        )
        # Trigger deterministic correlation engine on threat events
        if decision != "LEGITIMATE":
            correlate_event(db, sec_event)
    except Exception:
        pass

    # Phase 9: Record Audit Event
    from app.audit.service import record_audit_event
    record_audit_event(
        db=db,
        action="THREAT_DETECTED" if decision != "LEGITIMATE" else "THREAT_EVALUATED_CLEAN",
        severity=severity,
        outcome="SUCCESS" if decision == "LEGITIMATE" else "FAILURE",
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        actor_role=current_user.role,
        resource_type="QDS_SESSION",
        resource_id=session.session_id,
        details={
            "session_id": session.session_id,
            "attack_type": attack_type,
            "decision": decision,
            "severity": severity,
            "state_fidelity": metrics.get("state_fidelity", 1.0),
            "qber_percent": metrics.get("qber_percent", 0.0)
        }
    )

    return ThreatDetectionResponse(
        session_id=session.session_id,
        attack_type=attack_type,
        decision=decision,
        reason=reason,
        severity=severity,
        metrics=metrics,
        alerts=eval_result.get("alerts", [])
    )


@router.get(
    "/logs",
    summary="Query persisted threat logs"
)
def get_threat_logs(
    attack_type: Optional[str] = Query(None, description="Filter by attack type"),
    decision: Optional[str] = Query(None, description="Filter by decision (LEGITIMATE, SUSPICIOUS, MALICIOUS)"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieves threat audit logs.
    Role-based filtering applies: Regular users view logs for their own sessions;
    SECURITY_ANALYST and ADMIN view all system logs.
    """
    query = db.query(ThreatLogModel)

    # If regular user, restrict to sessions owned by that user
    user_role = (current_user.role or "").upper()
    if user_role not in ("ADMIN", "SECURITY_ANALYST"):
        user_session_ids = [
            s.session_id for s in db.query(QDSSessionModel.session_id).filter(QDSSessionModel.user_id == current_user.id).all()
        ]
        query = query.filter(ThreatLogModel.qds_session_id.in_(user_session_ids))

    if attack_type:
        query = query.filter(ThreatLogModel.attack_type.ilike(f"%{attack_type}%"))
    if decision:
        query = query.filter(ThreatLogModel.decision == decision.upper())
    if severity:
        query = query.filter(ThreatLogModel.severity == severity.upper())

    total = query.count()
    logs = query.order_by(ThreatLogModel.created_at.desc()).offset(skip).limit(limit).all()

    formatted_logs = []
    for log in logs:
        try:
            parsed_details = json.loads(log.details_json)
        except Exception:
            parsed_details = {}

        formatted_logs.append({
            "id": log.id,
            "qds_session_id": log.qds_session_id,
            "session_id": log.qds_session_id,
            "attack_type": log.attack_type,
            "threat_type": log.attack_type,
            "severity": log.severity,
            "decision": log.decision,
            "reason": log.reason,
            "qber_percent": log.qber_percent,
            "state_fidelity": log.state_fidelity,
            "mismatch_rate": log.mismatch_rate,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "details": parsed_details
        })

    return {
        "success": True,
        "data": {
            "logs": formatted_logs,
            "total_count": total,
            "limit": limit,
            "skip": skip
        }
    }
