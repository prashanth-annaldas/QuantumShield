/**
 * Centralized Axios API Client for QDS Framework.
 * Attaches JWT Bearer token, handles API base URL via VITE_API_URL, and provides typed calls.
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import {
  User,
  TokenResponse,
  LoginRequest,
  RegisterRequest,
  QDSSession,
  CreateSignatureRequest,
  TeleportResponse,
  VerifySignatureResponse,
  AttackSimulationRequest,
  AttackSimulationResult,
  ThreatDetectionResult,
  ThreatLog,
  SecurityAnalyticsSummary,
  ThreatStatistics,
  SecurityMetrics,
  HealthCheckResponse,
  SecurityEvent,
  Incident,
  IncidentUpdateRequest,
  IncidentListResponse,
  MonitoringMetrics,
  ReadinessStatus,
  AuditLogListResponse,
  PerformanceMetrics,
} from '../types';

const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// Strip trailing slash if present
const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request Interceptor: Attach JWT token if stored
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('qds_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
// Response Interceptor: Catch 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // If unauthorized, trigger logout event if user was logged in
      const currentToken = localStorage.getItem('qds_access_token');
      if (currentToken) {
        localStorage.removeItem('qds_access_token');
        localStorage.removeItem('qds_user');
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
    }
    return Promise.reject(error);
  }
);

// ─────────────────────────────────────────────────────────────────────────────
// Typed API Services
// ─────────────────────────────────────────────────────────────────────────────

export const authApi = {
  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/api/v1/auth/register', data);
    return res.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/api/v1/auth/login', data);
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/api/v1/auth/me');
    return res.data;
  },
};

export const qdsApi = {
  createSignature: async (data: CreateSignatureRequest): Promise<QDSSession> => {
    const res = await apiClient.post<QDSSession>('/api/v1/qds/create-signature', data);
    return res.data;
  },

  teleportSignature: async (sessionId: string): Promise<TeleportResponse> => {
    const res = await apiClient.post<TeleportResponse>('/api/v1/qds/teleport', {
      session_id: sessionId,
    });
    return res.data;
  },

  verifySignature: async (sessionId: string): Promise<VerifySignatureResponse> => {
    const res = await apiClient.post<VerifySignatureResponse>('/api/v1/qds/verify', {
      session_id: sessionId,
    });
    return res.data;
  },

  getSession: async (sessionId: string): Promise<QDSSession> => {
    const res = await apiClient.get<QDSSession>(`/api/v1/qds/session/${sessionId}`);
    return res.data;
  },
};

export const threatsApi = {
  simulateAttack: async (data: AttackSimulationRequest): Promise<AttackSimulationResult> => {
    const res = await apiClient.post<AttackSimulationResult>('/api/v1/threats/simulate', data);
    return res.data;
  },

  detectThreats: async (sessionId: string): Promise<ThreatDetectionResult> => {
    const res = await apiClient.post<ThreatDetectionResult>('/api/v1/threats/detect', {
      session_id: sessionId,
    });
    return res.data;
  },

  getThreatLogs: async (filters?: {
    attack_type?: string;
    decision?: string;
    severity?: string;
    limit?: number;
    skip?: number;
  }): Promise<{ logs: ThreatLog[]; total_count: number; limit: number; skip: number }> => {
    const res = await apiClient.get<{
      success: boolean;
      data: { logs: ThreatLog[]; total_count: number; limit: number; skip: number };
    }>('/api/v1/threats/logs', { params: filters });
    return res.data.data;
  },
};

export const analyticsApi = {
  getSummary: async (): Promise<SecurityAnalyticsSummary> => {
    const res = await apiClient.get<SecurityAnalyticsSummary>('/api/v1/analytics/summary');
    return res.data;
  },

  getThreatStatistics: async (): Promise<ThreatStatistics> => {
    const res = await apiClient.get<ThreatStatistics>('/api/v1/analytics/threat-statistics');
    return res.data;
  },

  getSecurityMetrics: async (): Promise<SecurityMetrics> => {
    const res = await apiClient.get<SecurityMetrics>('/api/v1/analytics/security-metrics');
    return res.data;
  },
};

export const systemApi = {
  getHealth: async (): Promise<HealthCheckResponse> => {
    const res = await apiClient.get<HealthCheckResponse>('/health');
    return res.data;
  },
};

export const realtimeApi = {
  getSessionTimeline: async (sessionId: string): Promise<{
    session_id: string;
    events: SecurityEvent[];
    total_events: number;
  }> => {
    const res = await apiClient.get<{
      session_id: string;
      events: SecurityEvent[];
      total_events: number;
    }>(`/api/v1/realtime/sessions/${sessionId}/timeline`);
    return res.data;
  },
};

export const incidentsApi = {
  getIncidents: async (filters?: {
    severity?: string;
    status?: string;
    limit?: number;
    skip?: number;
  }): Promise<IncidentListResponse> => {
    const res = await apiClient.get<{
      success: boolean;
      data: IncidentListResponse;
    }>('/api/v1/incidents', { params: filters });
    return res.data.data;
  },

  getIncident: async (incidentId: string): Promise<Incident> => {
    const res = await apiClient.get<{
      success: boolean;
      data: Incident;
    }>(`/api/v1/incidents/${incidentId}`);
    return res.data.data;
  },

  updateIncident: async (
    incidentId: string,
    updates: IncidentUpdateRequest
  ): Promise<Incident> => {
    const res = await apiClient.patch<{
      success: boolean;
      data: Incident;
    }>(`/api/v1/incidents/${incidentId}`, updates);
    return res.data.data;
  },
};

export const monitoringApi = {
  getMetrics: async (): Promise<MonitoringMetrics> => {
    const res = await apiClient.get<MonitoringMetrics>('/api/v1/monitoring/metrics');
    return res.data;
  },

  getPerformance: async (): Promise<PerformanceMetrics> => {
    const res = await apiClient.get<PerformanceMetrics>('/api/v1/monitoring/performance');
    return res.data;
  },

  getReadiness: async (): Promise<ReadinessStatus> => {
    const res = await apiClient.get<ReadinessStatus>('/api/v1/system/readiness');
    return res.data;
  },
};

export const auditApi = {
  getLogs: async (filters?: {
    action?: string;
    severity?: string;
    outcome?: string;
    request_id?: string;
    limit?: number;
    skip?: number;
  }): Promise<AuditLogListResponse> => {
    const res = await apiClient.get<{
      success: boolean;
      data: AuditLogListResponse;
    }>('/api/v1/audit/logs', { params: filters });
    return res.data.data;
  },
};
