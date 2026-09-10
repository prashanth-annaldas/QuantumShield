"""
Quantum Digital Signature (QDS) FastAPI endpoints.
Integrates with Phase 3 Teleportation Protocol and Phase 4 Threat Engine.
"""
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.core.rate_limiter import check_rate_limit
from app.monitoring.metrics import metrics_collector
from app.realtime.publisher import publish_security_event
from app.realtime.events import SecurityEventType, SecurityEventSeverity
from app.db.models import (
    UserModel,
    QDSSessionModel,
    VerificationResultModel,
    ThreatLogModel,
)
from app.db.schemas import (
    CreateSignatureRequest,
    TeleportRequest,
    VerifySignatureRequest,
    QDSSessionResponse,
    VerificationResultResponse,
)
from app.qds.session import QDSSession, QDSStatus
from app.qds.encoder import SignatureStateEncoder
from app.qds.hasher import QDSMessageHasher
from app.threats.engine import ThreatDecisionEngine

router = APIRouter(prefix="/qds", tags=["Quantum Digital Signature"])

# In-memory session registry for active quantum simulation states
active_sessions: Dict[str, QDSSession] = {}
global_threat_engine = ThreatDecisionEngine()


def _get_or_restore_session(session_id: str, db: Session) -> QDSSession:
    """Retrieves active session from memory or reconstructs state from database."""
    if session_id in active_sessions:
        return active_sessions[session_id]

    db_session = db.query(QDSSessionModel).filter(QDSSessionModel.session_id == session_id).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QDS session '{session_id}' not found"
        )

    # Reconstruct session from persisted message
    session = QDSSession(
        message=db_session.message or "Default Payload",
        sender_id=db_session.sender_id or "usr-sender",
        nonce=db_session.nonce
    )
    session.session_id = db_session.session_id
    active_sessions[session_id] = session
    return session


def _check_session_access(db_session: QDSSessionModel, current_user: UserModel) -> None:
    """Verifies that the current user is authorized to access the session."""
    user_role = (current_user.role or "").upper()
    if user_role in ("ADMIN", "SECURITY_ANALYST"):
        return
    if db_session.user_id and db_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not have permission to view or modify this session"
        )


@router.post(
    "/create-signature",
    response_model=QDSSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and encode quantum digital signature"
)
def create_signature(
    request: Request,
    req: CreateSignatureRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QDSSessionResponse:
    """
    Workflow:
    1. Validate message
    2. Check Idempotency-Key if present
    3. Compute SHA-256 message hash using existing QDSMessageHasher
    4. Encode hash into quantum states via SignatureStateEncoder
    5. Create QDSSession
    6. Persist metadata to database
    7. Record audit log
    8. Return session information
    """
    if not req.message or not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message payload cannot be empty"
        )

    # Phase 9: Idempotency Key check
    from app.core.idempotency import idempotency_store
    idempotency_key = request.headers.get("Idempotency-Key")
    req_body_str = req.model_dump_json() if hasattr(req, "model_dump_json") else str(req.__dict__)
    if idempotency_key:
        cached_resp = idempotency_store.get(idempotency_key, req_body_str)
        if cached_resp:
            return QDSSessionResponse(**cached_resp)

    sender_id = req.sender_id or current_user.username

    # Instantiate QDS session (encodes hash into 256 quantum states)
    session = QDSSession(message=req.message, sender_id=sender_id)
    active_sessions[session.session_id] = session

    # Persist session metadata
    db_session = QDSSessionModel(
        id=f"db-sess-{uuid.uuid4().hex[:8]}",
        session_id=session.session_id,
        user_id=current_user.id,
        sender_id=session.sender_id,
        message=session.message,
        message_hash=session.message_hash,
        nonce=session.nonce,
        status="PENDING",
        verification_attempts=0
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    # Observability & Real-Time Event
    metrics_collector.increment("qds_signatures_created")
    try:
        publish_security_event(
            db=db,
            event_type=SecurityEventType.SIGNATURE_CREATED,
            severity=SecurityEventSeverity.INFO,
            session_id=session.session_id,
            user_id=current_user.id,
            message=f"Quantum digital signature created for message hash {session.message_hash[:16]}...",
            metadata={"sender_id": session.sender_id, "nonce": session.nonce}
        )
    except Exception:
        pass

    # Phase 9: Record Audit Event
    from app.audit.service import record_audit_event
    record_audit_event(
        db=db,
        action="QDS_SIGNATURE_CREATED",
        severity="INFO",
        outcome="SUCCESS",
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        actor_role=current_user.role,
        resource_type="QDS_SESSION",
        resource_id=session.session_id,
        details={
            "session_id": session.session_id,
            "sender_id": session.sender_id,
            "message_hash_prefix": session.message_hash[:16],
            "nonce": session.nonce
        }
    )

    resp = QDSSessionResponse(
        id=db_session.id,
        session_id=session.session_id,
        user_id=db_session.user_id,
        sender_id=session.sender_id,
        message=session.message,
        message_hash=session.message_hash,
        nonce=session.nonce,
        status="PENDING",
        timestamp=session.timestamp,
        verification_attempts=0,
        created_at=db_session.created_at
    )

    if idempotency_key:
        idempotency_store.set(idempotency_key, req_body_str, resp.model_dump())

    return resp


# Backward compatibility route for /encode
@router.post(
    "/encode",
    summary="Legacy encode signature endpoint",
    include_in_schema=False
)
def legacy_encode(
    req: CreateSignatureRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    resp = create_signature(req, current_user, db)
    session = active_sessions[resp.session_id]
    return {
        "success": True,
        "data": session.to_dict()
    }


@router.post(
    "/teleport",
    summary="Transmit quantum signature states via quantum teleportation"
)
def teleport_signature(
    req: TeleportRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Transmits signature states using the Phase 3 QuantumTeleportationProcessor.
    Updates session state to TELEPORTED upon completion.
    """
    session = _get_or_restore_session(req.session_id, db)
    db_session = db.query(QDSSessionModel).filter(QDSSessionModel.session_id == req.session_id).first()
    if db_session:
        _check_session_access(db_session, current_user)

    # Execute teleportation protocol
    session.run_teleportation(deterministic=True)

    if db_session:
        db_session.status = "TELEPORTED"
        db.commit()

    # Observability & Real-Time Event
    try:
        publish_security_event(
            db=db,
            event_type=SecurityEventType.TELEPORTATION_COMPLETED,
            severity=SecurityEventSeverity.INFO,
            session_id=session.session_id,
            user_id=current_user.id,
            message=f"Teleportation completed with {len(session.expected_qubits)} Bell pairs",
            metadata={"bell_pair_count": len(session.expected_qubits)}
        )
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "session_id": session.session_id,
            "status": "TELEPORTED",
            "classical_bits": session.classical_bits,
            "bell_pair_count": len(session.expected_qubits),
            "timestamp": session.timestamp
        }
    }


@router.post(
    "/verify",
    summary="Verify quantum digital signature using non-AI threat decision engine"
)
def verify_signature(
    request: Request,
    req: VerifySignatureRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verifies signature fidelity, QBER, and mismatch rate.
    Persists verification telemetry to VerificationResultModel and updates session status.
    """
    check_rate_limit(request, "qds_verify", settings.RATE_LIMIT_VERIFY_PER_MINUTE)
    
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

    # Automatically teleport if still pending
    if session.status == QDSStatus.ENCODED or session.status == "PENDING":
        session.run_teleportation(deterministic=True)

    # Evaluate signature using deterministic Phase 4 threat engine
    authorized_sender = (db_session.sender_id if db_session and db_session.sender_id else session.sender_id)
    eval_result = global_threat_engine.evaluate_session(
        session,
        authorized_sender_id=authorized_sender
    )

    status_str = "VERIFIED" if eval_result["decision"] == "LEGITIMATE" else "REJECTED"

    # Update database session
    if db_session:
        db_session.status = status_str
        db_session.verification_attempts = session.verification_attempt_count
        db.commit()

    # Metrics
    metrics_collector.increment("qds_verifications_total")
    if eval_result["decision"] == "LEGITIMATE":
        metrics_collector.increment("qds_verifications_accepted")
    else:
        metrics_collector.increment("qds_verifications_rejected")
        metrics_collector.increment("threats_detected")

    # Persist verification telemetry
    metrics = eval_result["metrics"]
    ver_result = VerificationResultModel(
        id=f"ver-{uuid.uuid4().hex[:8]}",
        qds_session_id=session.session_id,
        fidelity=metrics["state_fidelity"],
        qber=metrics["qber_percent"],
        mismatch_rate=metrics["mismatch_rate"],
        statistical_deviation=metrics.get("statistical_deviation", 0.0),
        forgery_probability=metrics.get("forgery_probability", 0.0),
        verification_accuracy=metrics.get("verification_accuracy", 100.0),
        decision=eval_result["decision"]
    )
    db.add(ver_result)

    # Persist threat log entry
    import json
    threat_log = ThreatLogModel(
        id=f"log-{uuid.uuid4().hex[:8]}",
        qds_session_id=session.session_id,
        attack_type=eval_result.get("threat_type", "NONE"),
        severity="CRITICAL" if eval_result["decision"] == "MALICIOUS" else ("HIGH" if eval_result["decision"] == "SUSPICIOUS" else "LOW"),
        decision=eval_result["decision"],
        reason="; ".join(a.get("message", "") for a in eval_result.get("alerts", [])) or "Verification evaluated successfully",
        qber_percent=metrics["qber_percent"],
        state_fidelity=metrics["state_fidelity"],
        mismatch_rate=metrics["mismatch_rate"],
        details_json=json.dumps(eval_result)
    )
    db.add(threat_log)
    db.commit()

    # Publish real-time security events
    try:
        event_type = (
            SecurityEventType.SIGNATURE_VERIFIED
            if eval_result["decision"] == "LEGITIMATE"
            else SecurityEventType.SIGNATURE_REJECTED
        )
        sev = (
            SecurityEventSeverity.INFO
            if eval_result["decision"] == "LEGITIMATE"
            else (
                SecurityEventSeverity.HIGH
                if eval_result["decision"] == "SUSPICIOUS"
                else SecurityEventSeverity.CRITICAL
            )
        )
        sec_event = publish_security_event(
            db=db,
            event_type=event_type,
            severity=sev,
            session_id=session.session_id,
            user_id=current_user.id,
            message=f"Signature verification decision: {eval_result['decision']} (Fidelity: {metrics['state_fidelity']:.4f}, QBER: {metrics['qber_percent']:.2f}%)",
            metadata={
                "fidelity": metrics["state_fidelity"],
                "qber": metrics["qber_percent"],
                "decision": eval_result["decision"]
            }
        )
        if eval_result["decision"] != "LEGITIMATE":
            from app.incidents.correlation import correlate_event
            correlate_event(db, sec_event)
    except Exception:
        pass

    # Phase 9: Record Audit Event
    from app.audit.service import record_audit_event
    audit_action = "QDS_SIGNATURE_VERIFIED" if eval_result["decision"] == "LEGITIMATE" else "QDS_VERIFICATION_REJECTED"
    audit_sev = "INFO" if eval_result["decision"] == "LEGITIMATE" else ("HIGH" if eval_result["decision"] == "SUSPICIOUS" else "CRITICAL")
    audit_outcome = "SUCCESS" if eval_result["decision"] == "LEGITIMATE" else "FAILURE"
    record_audit_event(
        db=db,
        action=audit_action,
        severity=audit_sev,
        outcome=audit_outcome,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        actor_role=current_user.role,
        resource_type="QDS_SESSION",
        resource_id=session.session_id,
        details={
            "session_id": session.session_id,
            "decision": eval_result["decision"],
            "state_fidelity": metrics["state_fidelity"],
            "qber_percent": metrics["qber_percent"]
        }
    )

    result_payload = {
        "success": True,
        "data": eval_result
    }

    if idempotency_key:
        idempotency_store.set(idempotency_key, req_body_str, result_payload)

    return result_payload


@router.get(
    "/session/{session_id}",
    response_model=QDSSessionResponse,
    summary="Get QDS session details by ID"
)
def get_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QDSSessionResponse:
    """
    Fetches QDS session details.
    Enforces authorization: Only session owner, SECURITY_ANALYST, or ADMIN can access.
    """
    db_session = db.query(QDSSessionModel).filter(QDSSessionModel.session_id == session_id).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QDS session '{session_id}' not found"
        )

    _check_session_access(db_session, current_user)

    # Retrieve latest verification result if available
    latest_ver = db.query(VerificationResultModel).filter(
        VerificationResultModel.qds_session_id == session_id
    ).order_by(VerificationResultModel.created_at.desc()).first()

    ver_resp = VerificationResultResponse.model_validate(latest_ver) if latest_ver else None

    # Retrieve classical bits from memory cache if active
    mem_session = active_sessions.get(session_id)
    classical_bits = mem_session.classical_bits if mem_session else None

    return QDSSessionResponse(
        id=db_session.id,
        session_id=db_session.session_id,
        user_id=db_session.user_id,
        sender_id=db_session.sender_id,
        message=db_session.message,
        message_hash=db_session.message_hash,
        nonce=db_session.nonce,
        status=db_session.status,
        timestamp=db_session.timestamp,
        verification_attempts=db_session.verification_attempts,
        created_at=db_session.created_at,
        classical_bits=classical_bits,
        verification_result=ver_resp
    )
