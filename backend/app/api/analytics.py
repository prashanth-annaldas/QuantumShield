"""
Security Analytics and Health Metrics FastAPI endpoints.
Computes deterministic aggregate statistics from persisted database tables without AI.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models import (
    UserModel,
    QDSSessionModel,
    VerificationResultModel,
    ThreatLogModel,
)
from app.db.schemas import (
    SecurityAnalyticsResponse,
    ThreatStatisticsResponse,
    SecurityMetricsResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Health"])

STANDARD_ATTACK_TYPES = [
    "FORGERY",
    "IMPERSONATION",
    "REPLAY",
    "CHANNEL_MANIPULATION",
    "UNAUTHORIZED_VERIFICATION"
]


@router.get(
    "/summary",
    response_model=SecurityAnalyticsResponse,
    summary="Get overall security summary analytics"
)
def get_analytics_summary(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SecurityAnalyticsResponse:
    """
    Returns high-level protocol statistics:
    - total, accepted, and rejected sessions
    - acceptance rate
    - average fidelity, QBER, mismatch rate
    - threat breakdown by category
    - current system health status
    """
    total_sessions = db.query(QDSSessionModel).count()
    accepted_sessions = db.query(QDSSessionModel).filter(QDSSessionModel.status == "VERIFIED").count()
    rejected_sessions = db.query(QDSSessionModel).filter(QDSSessionModel.status == "REJECTED").count()

    acceptance_rate = round((accepted_sessions / total_sessions * 100.0), 2) if total_sessions > 0 else 100.0

    # Threat breakdown
    threat_counts: Dict[str, int] = {att: 0 for att in STANDARD_ATTACK_TYPES}
    raw_counts = (
        db.query(ThreatLogModel.attack_type, func.count(ThreatLogModel.id))
        .filter(ThreatLogModel.attack_type != "NONE")
        .group_by(ThreatLogModel.attack_type)
        .all()
    )
    total_threats = 0
    for attack_type, count in raw_counts:
        norm_type = attack_type.replace("_ATTACK", "").replace("SIGNATURE_", "").replace("QUANTUM_", "")
        threat_counts[norm_type] = threat_counts.get(norm_type, 0) + count
        total_threats += count

    # Verification averages
    ver_count = db.query(VerificationResultModel).count()
    if ver_count > 0:
        avg_fidelity = float(db.query(func.avg(VerificationResultModel.fidelity)).scalar() or 1.0)
        avg_qber = float(db.query(func.avg(VerificationResultModel.qber)).scalar() or 0.0)
        avg_mismatch = float(db.query(func.avg(VerificationResultModel.mismatch_rate)).scalar() or 0.0)
    else:
        avg_fidelity = 1.0
        avg_qber = 0.0
        avg_mismatch = 0.0

    # System Health Assessment
    critical_threats = db.query(ThreatLogModel).filter(ThreatLogModel.severity == "CRITICAL").count()
    suspicious_threats = db.query(ThreatLogModel).filter(ThreatLogModel.severity.in_(["HIGH", "MEDIUM"])).count()

    if critical_threats > 5:
        health_status = "CRITICAL_ATTACKS_DETECTED"
    elif suspicious_threats > 0 or critical_threats > 0:
        health_status = "WARNING_SUSPICIOUS_ACTIVITY"
    else:
        health_status = "OPTIMAL"

    return SecurityAnalyticsResponse(
        total_sessions=total_sessions,
        accepted_sessions=accepted_sessions,
        rejected_sessions=rejected_sessions,
        total_threats=total_threats,
        average_fidelity=round(avg_fidelity, 4),
        average_qber=round(avg_qber, 2),
        average_mismatch_rate=round(avg_mismatch, 4),
        threat_counts_by_type=threat_counts,
        acceptance_rate=acceptance_rate,
        system_health_status=health_status
    )


@router.get(
    "/threat-statistics",
    response_model=ThreatStatisticsResponse,
    summary="Get detailed threat occurrence and severity statistics"
)
def get_threat_statistics(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreatStatisticsResponse:
    """
    Returns threat counts grouped by attack category and severity levels.
    """
    raw_type_counts = (
        db.query(ThreatLogModel.attack_type, func.count(ThreatLogModel.id))
        .filter(ThreatLogModel.attack_type != "NONE")
        .group_by(ThreatLogModel.attack_type)
        .all()
    )
    threat_counts_by_type = {t: c for t, c in raw_type_counts}
    total_threats = sum(c for _, c in raw_type_counts)

    raw_sev_counts = (
        db.query(ThreatLogModel.severity, func.count(ThreatLogModel.id))
        .group_by(ThreatLogModel.severity)
        .all()
    )
    severity_breakdown = {s: c for s, c in raw_sev_counts}

    return ThreatStatisticsResponse(
        total_threats=total_threats,
        threat_counts_by_type=threat_counts_by_type,
        severity_breakdown=severity_breakdown
    )


@router.get(
    "/security-metrics",
    response_model=SecurityMetricsResponse,
    summary="Get aggregated quantum physical and protocol security metrics"
)
def get_security_metrics(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SecurityMetricsResponse:
    """
    Returns quantum fidelity, QBER, and mismatch rate distributions across verified sessions.
    """
    ver_count = db.query(VerificationResultModel).count()
    if ver_count == 0:
        return SecurityMetricsResponse(
            average_fidelity=1.0,
            average_qber=0.0,
            average_mismatch_rate=0.0,
            min_fidelity=1.0,
            max_qber=0.0,
            total_verified_sessions=0
        )

    avg_fidelity = float(db.query(func.avg(VerificationResultModel.fidelity)).scalar() or 1.0)
    avg_qber = float(db.query(func.avg(VerificationResultModel.qber)).scalar() or 0.0)
    avg_mismatch = float(db.query(func.avg(VerificationResultModel.mismatch_rate)).scalar() or 0.0)
    min_fidelity = float(db.query(func.min(VerificationResultModel.fidelity)).scalar() or 1.0)
    max_qber = float(db.query(func.max(VerificationResultModel.qber)).scalar() or 0.0)

    return SecurityMetricsResponse(
        average_fidelity=round(avg_fidelity, 4),
        average_qber=round(avg_qber, 2),
        average_mismatch_rate=round(avg_mismatch, 4),
        min_fidelity=round(min_fidelity, 4),
        max_qber=round(max_qber, 2),
        total_verified_sessions=ver_count
    )


# Backward compatibility endpoint for /analytics/dashboard
@router.get(
    "/dashboard",
    summary="Legacy dashboard analytics endpoint",
    include_in_schema=False
)
def get_dashboard_legacy(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_sessions = db.query(QDSSessionModel).count()
    logs = db.query(ThreatLogModel).all()
    total_logs = len(logs)

    legitimate_count = sum(1 for log in logs if log.decision == "LEGITIMATE")
    malicious_count = sum(1 for log in logs if log.decision == "MALICIOUS")
    suspicious_count = sum(1 for log in logs if log.decision == "SUSPICIOUS")

    threat_breakdown = {att: 0 for att in STANDARD_ATTACK_TYPES}
    for log in logs:
        for att in STANDARD_ATTACK_TYPES:
            if att in log.attack_type:
                threat_breakdown[att] += 1

    avg_qber = float(db.query(func.avg(ThreatLogModel.qber_percent)).scalar() or 0.0)
    avg_fidelity = float(db.query(func.avg(ThreatLogModel.state_fidelity)).scalar() or 1.0)

    health_status = "CRITICAL_ATTACKS_DETECTED" if malicious_count > 5 else ("WARNING_SUSPICIOUS_ACTIVITY" if suspicious_count > 0 else "OPTIMAL")

    return {
        "success": True,
        "data": {
            "total_sessions": max(total_sessions, total_logs),
            "legitimate_sessions": legitimate_count,
            "malicious_sessions": malicious_count,
            "suspicious_sessions": suspicious_count,
            "threat_breakdown": threat_breakdown,
            "average_qber_percent": round(avg_qber, 2),
            "average_state_fidelity": round(avg_fidelity, 4),
            "system_health_status": health_status
        }
    }
