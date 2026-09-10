"""
Pydantic validation schemas for requests and responses.
Separates API contracts from database ORM models.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field


# ─────────────────────────────────────────────────────────────────────────────
# Authentication & User Schemas
# ─────────────────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = Field("USER", description="USER, SECURITY_ANALYST, ADMIN")


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─────────────────────────────────────────────────────────────────────────────
# QDS Protocol Schemas
# ─────────────────────────────────────────────────────────────────────────────

class CreateSignatureRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Raw message payload to sign")
    sender_id: Optional[str] = Field(None, description="Sender identity identifier")


class TeleportRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Unique QDS session identifier")


class VerifySignatureRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Unique QDS session identifier")


class VerificationResultResponse(BaseModel):
    id: str
    qds_session_id: str
    fidelity: float
    qber: float
    mismatch_rate: float
    statistical_deviation: float
    forgery_probability: float
    verification_accuracy: float
    decision: str
    created_at: datetime

    class Config:
        from_attributes = True


class QDSSessionResponse(BaseModel):
    id: Optional[str] = None
    session_id: str
    user_id: Optional[str] = None
    sender_id: Optional[str] = None
    message: Optional[str] = None
    message_hash: str
    nonce: str
    status: str
    timestamp: Optional[Any] = None
    verification_attempts: int = 0
    created_at: Optional[datetime] = None
    classical_bits: Optional[List[int]] = None
    verification_result: Optional[VerificationResultResponse] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Threat Detection & Simulation Schemas
# ─────────────────────────────────────────────────────────────────────────────

class AttackSimulationRequest(BaseModel):
    session_id: str
    attack_type: str = Field(
        ...,
        description="FORGERY, IMPERSONATION, REPLAY, CHANNEL_MANIPULATION, UNAUTHORIZED_VERIFICATION"
    )
    tamper_ratio: Optional[float] = Field(0.15, ge=0.0, le=1.0)
    error_rate: Optional[float] = Field(0.15, ge=0.0, le=1.0)


class ThreatDetectionRequest(BaseModel):
    session_id: str


class ThreatDetectionResponse(BaseModel):
    session_id: str
    attack_type: str
    decision: str  # LEGITIMATE, SUSPICIOUS, MALICIOUS
    reason: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]] = []


class ThreatLogResponse(BaseModel):
    id: str
    qds_session_id: str
    attack_type: str
    severity: str
    decision: str
    reason: Optional[str] = None
    qber_percent: float
    state_fidelity: float
    mismatch_rate: float
    created_at: datetime
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Analytics Schemas
# ─────────────────────────────────────────────────────────────────────────────

class SecurityAnalyticsResponse(BaseModel):
    total_sessions: int
    accepted_sessions: int
    rejected_sessions: int
    total_threats: int
    average_fidelity: float
    average_qber: float
    average_mismatch_rate: float
    threat_counts_by_type: Dict[str, int]
    acceptance_rate: float
    system_health_status: str


class ThreatStatisticsResponse(BaseModel):
    total_threats: int
    threat_counts_by_type: Dict[str, int]
    severity_breakdown: Dict[str, int]


class SecurityMetricsResponse(BaseModel):
    average_fidelity: float
    average_qber: float
    average_mismatch_rate: float
    min_fidelity: float
    max_qber: float
    total_verified_sessions: int


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8: Real-Time Events, Incidents, Monitoring Schemas
# ─────────────────────────────────────────────────────────────────────────────

class SecurityEventResponse(BaseModel):
    event_id: str
    event_type: str
    severity: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: str
    incident_id: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    source_session_id: Optional[str] = None
    source_user_id: Optional[str] = None
    event_count: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_to_user_id: Optional[str] = None

    class Config:
        from_attributes = True


class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE")
    assigned_to_user_id: Optional[str] = None
    description: Optional[str] = None


class IncidentListResponse(BaseModel):
    incidents: List[Dict[str, Any]]
    total_count: int


class MonitoringMetricsResponse(BaseModel):
    uptime_seconds: float = 0.0
    api_metrics: Dict[str, Any] = Field(default_factory=dict)
    qds_metrics: Dict[str, Any] = Field(default_factory=dict)
    threat_metrics: Dict[str, Any] = Field(default_factory=dict)
    incident_metrics: Dict[str, Any] = Field(default_factory=dict)
    websocket_metrics: Dict[str, Any] = Field(default_factory=dict)
    # Backward compatibility aliases
    requests: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    threats: Optional[Dict[str, Any]] = None
    incidents: Optional[Dict[str, Any]] = None
    websocket: Optional[Dict[str, Any]] = None


class ReadinessResponse(BaseModel):
    status: str
    checks: Dict[str, str] = Field(default_factory=dict)
    database: Optional[str] = "HEALTHY"
    qds_engine: Optional[str] = "HEALTHY"
    threat_engine: Optional[str] = "HEALTHY"
    realtime: Optional[str] = "HEALTHY"


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9: Audit & Performance Schemas
# ─────────────────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: str
    event_id: str
    request_id: str
    actor_user_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    outcome: str
    severity: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total_count: int
    limit: int
    skip: int


class LatencyPercentiles(BaseModel):
    average_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    sample_count: int


class PerformanceMetricsResponse(BaseModel):
    requests_total: int
    errors_total: int
    error_rate: float
    auth_failures_total: int
    rate_limit_violations_total: int
    latency: LatencyPercentiles
    uptime_seconds: float
