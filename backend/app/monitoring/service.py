"""
Phase 8: Monitoring Service.
Aggregates in-memory operational metrics with database-level metrics
for the monitoring endpoints.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.monitoring.metrics import metrics_collector
from app.realtime.manager import ws_manager
from app.db.models import IncidentModel, SecurityEventModel, QDSSessionModel


def get_monitoring_metrics(db: Session) -> Dict[str, Any]:
    """
    Aggregate all monitoring metrics across in-memory counters,
    database models, and WebSocket connection state.
    """
    snapshot = metrics_collector.get_snapshot()

    # DB metrics
    total_incidents = db.query(func.count(IncidentModel.id)).scalar() or 0
    open_incidents = (
        db.query(func.count(IncidentModel.id))
        .filter(IncidentModel.status.in_(["OPEN", "INVESTIGATING"]))
        .scalar()
        or 0
    )
    critical_incidents = (
        db.query(func.count(IncidentModel.id))
        .filter(
            IncidentModel.severity == "CRITICAL",
            IncidentModel.status.in_(["OPEN", "INVESTIGATING"]),
        )
        .scalar()
        or 0
    )
    total_security_events = (
        db.query(func.count(SecurityEventModel.id)).scalar() or 0
    )
    total_sessions = db.query(func.count(QDSSessionModel.id)).scalar() or 0

    return {
        "uptime_seconds": snapshot["uptime_seconds"],
        "api_metrics": {
            "http_requests_total": snapshot["counters"].get(
                "http_requests_total", 0
            ),
            "http_requests_failed": snapshot["counters"].get(
                "http_requests_failed", 0
            ),
            "avg_latency_ms": snapshot["latency"]["avg_ms"],
            "p95_latency_ms": snapshot["latency"]["p95_ms"],
        },
        "qds_metrics": {
            "signatures_created": snapshot["counters"].get(
                "qds_signatures_created", 0
            ),
            "verifications_total": snapshot["counters"].get(
                "qds_verifications_total", 0
            ),
            "verifications_accepted": snapshot["counters"].get(
                "qds_verifications_accepted", 0
            ),
            "verifications_rejected": snapshot["counters"].get(
                "qds_verifications_rejected", 0
            ),
            "acceptance_rate": snapshot["acceptance_rate"],
            "total_sessions": total_sessions,
        },
        "threat_metrics": {
            "threats_simulated": snapshot["counters"].get(
                "threats_simulated", 0
            ),
            "threats_detected": snapshot["counters"].get(
                "threats_detected", 0
            ),
            "rate_limit_exceeded": snapshot["counters"].get(
                "rate_limit_exceeded_total", 0
            ),
        },
        "incident_metrics": {
            "total_incidents": total_incidents,
            "open_incidents": open_incidents,
            "critical_incidents": critical_incidents,
            "total_security_events": total_security_events,
        },
        "websocket_metrics": {
            "active_connections": ws_manager.connection_count,
        },
    }
