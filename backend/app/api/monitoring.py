"""
Phase 9: Monitoring, Observability & Performance API Endpoints.
Provides structured operational metrics, latency percentiles (p50, p95, p99),
and subsystem readiness health probes (HEALTHY / DEGRADED / UNAVAILABLE).
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import require_role
from app.db.schemas import (
    MonitoringMetricsResponse,
    ReadinessResponse,
    PerformanceMetricsResponse,
)
from app.monitoring.service import get_monitoring_metrics
from app.monitoring.metrics import metrics_collector
from app.realtime.manager import ws_manager

router = APIRouter(tags=["Monitoring & System Readiness"])


@router.get(
    "/monitoring/metrics",
    response_model=MonitoringMetricsResponse,
    summary="Get operational and security metrics",
    description="Retrieve live API, QDS protocol, threat detection, incident, and WebSocket metrics. Restricted to SECURITY_ANALYST and ADMIN.",
)
def get_metrics(
    current_user=Depends(require_role("SECURITY_ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Retrieve operational and security metrics snapshot."""
    return get_monitoring_metrics(db)


@router.get(
    "/monitoring/performance",
    response_model=PerformanceMetricsResponse,
    summary="Get API performance and latency percentiles",
    description="Retrieve high-resolution request counts, error rate, auth failure stats, and latency percentiles (p50, p95, p99).",
)
def get_performance(
    current_user=Depends(require_role("SECURITY_ANALYST", "ADMIN")),
):
    """Retrieve latency percentiles and performance metrics."""
    return metrics_collector.get_performance_metrics()


@router.get(
    "/system/readiness",
    response_model=ReadinessResponse,
    summary="System readiness health check",
    description="Check if all required subsystems (database, simulation engine, WebSocket manager, threat engine) are operational. No secrets exposed.",
)
def check_readiness(db: Session = Depends(get_db)):
    """Check readiness status of database and core subsystems."""
    checks = {}
    db_status = "HEALTHY"
    qds_status = "HEALTHY"
    threat_status = "HEALTHY"
    realtime_status = "HEALTHY"

    # 1. Database probe
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "HEALTHY"
    except Exception as exc:
        db_status = "UNAVAILABLE"
        checks["database"] = f"UNAVAILABLE: {type(exc).__name__}"

    # 2. Quantum simulation engine probe
    try:
        from app.quantum import QubitState
        _ = QubitState(1.0, 0.0)
        checks["quantum_engine"] = "HEALTHY"
    except Exception as exc:
        qds_status = "UNAVAILABLE"
        checks["quantum_engine"] = f"UNAVAILABLE: {type(exc).__name__}"

    # 3. Threat detection engine probe
    try:
        from app.threats.engine import ThreatDecisionEngine
        _ = ThreatDecisionEngine()
        checks["threat_engine"] = "HEALTHY"
    except Exception as exc:
        threat_status = "UNAVAILABLE"
        checks["threat_engine"] = f"UNAVAILABLE: {type(exc).__name__}"

    # 4. Metrics & Real-time subsystem probe
    try:
        _ = metrics_collector.get_snapshot()
        _ = ws_manager.connection_count
        checks["metrics_collector"] = "HEALTHY"
        checks["realtime"] = "HEALTHY"
    except Exception as exc:
        realtime_status = "DEGRADED"
        checks["metrics_collector"] = f"DEGRADED: {type(exc).__name__}"
        checks["realtime"] = f"DEGRADED: {type(exc).__name__}"

    # Determine overall status: READY, DEGRADED, or NOT_READY
    if db_status == "UNAVAILABLE" or qds_status == "UNAVAILABLE":
        overall_status = "NOT_READY"
    elif any(s != "HEALTHY" for s in (db_status, qds_status, threat_status, realtime_status)):
        overall_status = "DEGRADED"
    else:
        overall_status = "READY"

    return ReadinessResponse(
        status=overall_status,
        checks=checks,
        database=db_status,
        qds_engine=qds_status,
        threat_engine=threat_status,
        realtime=realtime_status,
    )
