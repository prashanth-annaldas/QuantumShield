/**
 * TypeScript Type Definitions for Quantum Digital Signature (QDS) Framework.
 * Synchronized with Phase 5 backend Pydantic schemas.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Authentication & User Types
// ─────────────────────────────────────────────────────────────────────────────

export type UserRole = 'USER' | 'SECURITY_ANALYST' | 'ADMIN';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role?: UserRole;
}

export interface LoginRequest {
  username: string;
  password: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// QDS Protocol Types
// ─────────────────────────────────────────────────────────────────────────────

export type QDSStatusType = 'PENDING' | 'ENCODED' | 'TELEPORTED' | 'VERIFIED' | 'REJECTED' | 'FAILED';

export interface VerificationResult {
  id: string;
  qds_session_id: string;
  fidelity: number;
  qber: number;
  mismatch_rate: number;
  statistical_deviation: number;
  forgery_probability: number;
  verification_accuracy: number;
  decision: 'LEGITIMATE' | 'SUSPICIOUS' | 'MALICIOUS';
  created_at: string;
}

export interface QDSSession {
  id?: string;
  session_id: string;
  user_id?: string;
  sender_id?: string;
  message?: string;
  message_hash: string;
  nonce: string;
  status: QDSStatusType | string;
  timestamp?: string | number;
  verification_attempts: number;
  created_at?: string;
  classical_bits?: number[];
  verification_result?: VerificationResult | null;
}

export interface CreateSignatureRequest {
  message: string;
  sender_id?: string;
}

export interface TeleportResponse {
  success: boolean;
  data: {
    session_id: string;
    status: string;
    classical_bits: number[];
    bell_pair_count: number;
    timestamp: string | number;
  };
}

export interface VerifySignatureResponse {
  success: boolean;
  data: ThreatDetectionResult;
}

// ─────────────────────────────────────────────────────────────────────────────
// Threat Simulation & Detection Types
// ─────────────────────────────────────────────────────────────────────────────

export type AttackType =
  | 'FORGERY'
  | 'SIGNATURE_FORGERY'
  | 'IMPERSONATION'
  | 'IMPERSONATION_ATTACK'
  | 'REPLAY'
  | 'REPLAY_ATTACK'
  | 'CHANNEL_MANIPULATION'
  | 'QUANTUM_CHANNEL_MANIPULATION'
  | 'UNAUTHORIZED_VERIFICATION'
  | 'NONE';

export type ThreatDecision = 'LEGITIMATE' | 'SUSPICIOUS' | 'MALICIOUS';
export type ThreatSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ThreatMetrics {
  state_fidelity: number;
  mismatch_rate: number;
  qber_percent: number;
  statistical_deviation?: number;
  forgery_probability?: number;
  verification_accuracy?: number;
  bit_mismatches?: number;
  total_bits?: number;
  session_age_seconds?: number;
  attempt_count?: number;
  [key: string]: string | number | boolean | undefined;
}

export interface ThreatAlertItem {
  code: string;
  severity: string;
  message: string;
}

export interface ThreatDetectionResult {
  session_id: string;
  attack_type: string;
  decision: ThreatDecision;
  reason: string;
  severity: ThreatSeverity;
  metrics: ThreatMetrics;
  alerts: ThreatAlertItem[];
  action?: 'ACCEPT' | 'REJECT';
  authorized_sender?: string;
  evaluated_sender?: string;
}

export interface AttackSimulationRequest {
  session_id: string;
  attack_type: string;
  tamper_ratio?: number;
  error_rate?: number;
}

export interface AttackSimulationResult {
  success: boolean;
  data: {
    session_id: string;
    injected_threat: string;
    details: {
      attack_type?: string;
      tamper_count?: number;
      tamper_indices?: number[];
      noise_count?: number;
      error_rate?: number;
      fake_sender?: string;
      time_offset_seconds?: number;
      attempt_count?: number;
      [key: string]: unknown;
    };
  };
}

export interface ThreatLog {
  id: string;
  qds_session_id: string;
  session_id?: string;
  attack_type: string;
  threat_type?: string;
  severity: ThreatSeverity | string;
  decision: ThreatDecision | string;
  reason?: string;
  qber_percent: number;
  state_fidelity: number;
  mismatch_rate: number;
  created_at: string;
  details?: Record<string, unknown>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Security Analytics Types
// ─────────────────────────────────────────────────────────────────────────────

export interface SecurityAnalyticsSummary {
  total_sessions: number;
  accepted_sessions: number;
  rejected_sessions: number;
  total_threats: number;
  average_fidelity: number;
  average_qber: number;
  average_mismatch_rate: number;
  threat_counts_by_type: Record<string, number>;
  acceptance_rate: number;
  system_health_status: 'OPTIMAL' | 'WARNING_SUSPICIOUS_ACTIVITY' | 'CRITICAL_ATTACKS_DETECTED' | string;
}

export interface ThreatStatistics {
  total_threats: number;
  threat_counts_by_type: Record<string, number>;
  severity_breakdown: Record<string, number>;
}

export interface SecurityMetrics {
  average_fidelity: number;
  average_qber: number;
  average_mismatch_rate: number;
  min_fidelity: number;
  max_qber: number;
  total_verified_sessions: number;
}

export interface HealthCheckResponse {
  status: string;
  application: string;
  environment?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase 8: Real-Time Security Operations & Observability Types
// ─────────────────────────────────────────────────────────────────────────────

export type SecurityEventSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type SecurityEventType =
  | 'SIGNATURE_CREATED'
  | 'SIGNATURE_ENCODED'
  | 'BELL_PAIR_CREATED'
  | 'TELEPORTATION_STARTED'
  | 'TELEPORTATION_COMPLETED'
  | 'VERIFICATION_STARTED'
  | 'VERIFICATION_ACCEPTED'
  | 'VERIFICATION_REJECTED'
  | 'THREAT_SIMULATION_STARTED'
  | 'THREAT_DETECTED'
  | 'FORGERY_DETECTED'
  | 'IMPERSONATION_DETECTED'
  | 'REPLAY_DETECTED'
  | 'CHANNEL_NOISE_DETECTED'
  | 'UNAUTHORIZED_ACCESS_DETECTED'
  | 'INCIDENT_CREATED'
  | 'INCIDENT_ESCALATED'
  | 'INCIDENT_UPDATED'
  | 'INCIDENT_RESOLVED'
  | 'RATE_LIMIT_EXCEEDED'
  | 'SYSTEM_HEALTH_CHANGED'
  | string;

export interface SecurityEvent {
  event_id: string;
  event_type: SecurityEventType;
  severity: SecurityEventSeverity;
  timestamp: string;
  session_id?: string | null;
  user_id?: string | null;
  message: string;
  metadata?: Record<string, unknown>;
}

export type IncidentStatus = 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';
export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Incident {
  id: string;
  incident_id: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  source_session_id?: string | null;
  source_user_id?: string | null;
  event_count: number;
  assigned_to_user_id?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  correlated_events?: SecurityEvent[];
}

export interface IncidentUpdateRequest {
  status?: IncidentStatus;
  assigned_to_user_id?: string | null;
  description?: string;
}

export interface IncidentListResponse {
  incidents: Incident[];
  total_count: number;
  open_count: number;
  critical_count: number;
}

export interface MonitoringMetrics {
  uptime_seconds: number;
  api_metrics: {
    http_requests_total: number;
    http_requests_failed: number;
    avg_latency_ms: number;
    p95_latency_ms: number;
  };
  qds_metrics: {
    signatures_created: number;
    verifications_total: number;
    verifications_accepted: number;
    verifications_rejected: number;
    acceptance_rate: number;
    total_sessions: number;
  };
  threat_metrics: {
    threats_simulated: number;
    threats_detected: number;
    rate_limit_exceeded: number;
  };
  incident_metrics: {
    total_incidents: number;
    open_incidents: number;
    critical_incidents: number;
    total_security_events: number;
  };
  websocket_metrics: {
    active_connections: number;
  };
}

export interface ReadinessStatus {
  status: 'READY' | 'DEGRADED' | 'NOT_READY' | string;
  checks: Record<string, string>;
  database?: string;
  qds_engine?: string;
  threat_engine?: string;
  realtime?: string;
}

export type WebSocketState = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'ERROR';

// ─────────────────────────────────────────────────────────────────────────────
// Phase 9: Enterprise Resilience & Security Audit Types
// ─────────────────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: string;
  event_id: string;
  request_id: string;
  actor_user_id?: string | null;
  actor_role?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  outcome: 'SUCCESS' | 'FAILURE' | string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogListResponse {
  audit_logs: AuditLog[];
  total_count: number;
  limit: number;
  skip: number;
}

export interface LatencyPercentiles {
  average_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  sample_count: number;
}

export interface PerformanceMetrics {
  requests_total: number;
  errors_total: number;
  error_rate: number;
  auth_failures_total: number;
  rate_limit_violations_total: number;
  latency: LatencyPercentiles;
  uptime_seconds: number;
}

