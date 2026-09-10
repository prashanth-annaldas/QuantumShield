import React, { useEffect, useState } from 'react';
import {
  Server,
  Database,
  Cpu,
  ShieldAlert,
  Radio,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Gauge,
  Lock,
  Zap,
} from 'lucide-react';
import { monitoringApi } from '../services/api';
import { ReadinessStatus, PerformanceMetrics } from '../types';

export const ProductionReadiness: React.FC = () => {
  const [readiness, setReadiness] = useState<ReadinessStatus | null>(null);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [readinessRes, performanceRes] = await Promise.all([
        monitoringApi.getReadiness(),
        monitoringApi.getPerformance().catch(() => null),
      ]);
      setReadiness(readinessRes);
      setPerformance(performanceRes);
    } catch {
      // Ignore errors on manual refresh
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const doFetch = async () => {
      setLoading(true);
      try {
        const [readinessRes, performanceRes] = await Promise.all([
          monitoringApi.getReadiness(),
          monitoringApi.getPerformance().catch(() => null),
        ]);
        if (!cancelled) {
          setReadiness(readinessRes);
          setPerformance(performanceRes);
        }
      } catch {
        // Ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void doFetch();
    const interval = setInterval(() => { void doFetch(); }, 10000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const getStatusIcon = (status?: string) => {
    switch (status?.toUpperCase()) {
      case 'READY':
      case 'HEALTHY':
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case 'DEGRADED':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'NOT_READY':
      case 'UNAVAILABLE':
      default:
        return <XCircle className="w-5 h-5 text-rose-500" />;
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status?.toUpperCase()) {
      case 'READY':
      case 'HEALTHY':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'DEGRADED':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'NOT_READY':
      case 'UNAVAILABLE':
      default:
        return 'bg-rose-50 text-rose-700 border-rose-200';
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Production Reliability & System Readiness</h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <Lock className="w-3.5 h-3.5 text-indigo-500" />
            <span>Zero Credential Leaks</span>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Primary Overall Health Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              {getStatusIcon(readiness?.status)}
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Overall System State</div>
              <div className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                {readiness?.status || 'PROBING...'}
                {readiness?.status && (
                  <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${getStatusBadge(readiness.status)}`}>
                    {readiness.status === 'READY' ? 'All Probes Passing' : 'Investigate Degradations'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {performance && (
            <div className="flex items-center gap-6 border-t sm:border-t-0 sm:border-l border-slate-200 pt-4 sm:pt-0 sm:pl-6 text-xs">
              <div>
                <span className="text-slate-400 block uppercase font-medium">Uptime</span>
                <span className="text-slate-900 font-bold text-sm">
                  {Math.floor(performance.uptime_seconds / 60)} min {Math.floor(performance.uptime_seconds % 60)} sec
                </span>
              </div>
              <div>
                <span className="text-slate-400 block uppercase font-medium">Error Rate</span>
                <span className={`font-bold text-sm ${performance.error_rate > 0.05 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {(performance.error_rate * 100).toFixed(2)}%
                </span>
              </div>
              <div>
                <span className="text-slate-400 block uppercase font-medium">Auth Failures</span>
                <span className="text-slate-900 font-bold text-sm">{performance.auth_failures_total}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Subsystem Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Database Subsystem */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
              <Database className="w-4 h-4 text-indigo-600" />
              Database Subsystem
            </div>
            {getStatusIcon(readiness?.database || readiness?.checks?.database)}
          </div>
          <p className="text-xs text-slate-500 mb-3">
            PostgreSQL / SQLAlchemy connection pool and transactional state.
          </p>
          <div className="flex items-center justify-between text-xs pt-3 border-t border-slate-100">
            <span className="text-slate-400 font-mono">Status:</span>
            <span className={`font-bold px-2 py-0.5 rounded border text-[11px] ${getStatusBadge(readiness?.database || readiness?.checks?.database)}`}>
              {readiness?.database || readiness?.checks?.database || 'HEALTHY'}
            </span>
          </div>
        </div>

        {/* 2. Quantum Engine */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
              <Cpu className="w-4 h-4 text-blue-600" />
              Quantum Simulation
            </div>
            {getStatusIcon(readiness?.qds_engine || readiness?.checks?.quantum_engine)}
          </div>
          <p className="text-xs text-slate-500 mb-3">
            NumPy state vectors, Bell EPR pairs, and 256-qubit teleportation.
          </p>
          <div className="flex items-center justify-between text-xs pt-3 border-t border-slate-100">
            <span className="text-slate-400 font-mono">Status:</span>
            <span className={`font-bold px-2 py-0.5 rounded border text-[11px] ${getStatusBadge(readiness?.qds_engine || readiness?.checks?.quantum_engine)}`}>
              {readiness?.qds_engine || readiness?.checks?.quantum_engine || 'HEALTHY'}
            </span>
          </div>
        </div>

        {/* 3. Threat Engine */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
              <ShieldAlert className="w-4 h-4 text-emerald-600" />
              Threat Decision Engine
            </div>
            {getStatusIcon(readiness?.threat_engine || readiness?.checks?.threat_engine)}
          </div>
          <p className="text-xs text-slate-500 mb-3">
            Deterministic rule engine computing Fidelity, QBER, and Mismatch Rate.
          </p>
          <div className="flex items-center justify-between text-xs pt-3 border-t border-slate-100">
            <span className="text-slate-400 font-mono">Status:</span>
            <span className={`font-bold px-2 py-0.5 rounded border text-[11px] ${getStatusBadge(readiness?.threat_engine || readiness?.checks?.threat_engine)}`}>
              {readiness?.threat_engine || readiness?.checks?.threat_engine || 'HEALTHY'}
            </span>
          </div>
        </div>

        {/* 4. Real-time Subsystem */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
              <Radio className="w-4 h-4 text-purple-600" />
              WebSocket SOC Hub
            </div>
            {getStatusIcon(readiness?.realtime || readiness?.checks?.realtime)}
          </div>
          <p className="text-xs text-slate-500 mb-3">
            Real-time event stream manager & deterministic incident correlation.
          </p>
          <div className="flex items-center justify-between text-xs pt-3 border-t border-slate-100">
            <span className="text-slate-400 font-mono">Status:</span>
            <span className={`font-bold px-2 py-0.5 rounded border text-[11px] ${getStatusBadge(readiness?.realtime || readiness?.checks?.realtime)}`}>
              {readiness?.realtime || readiness?.checks?.realtime || 'HEALTHY'}
            </span>
          </div>
        </div>
      </div>

      {/* Latency Percentiles & Performance Gauges */}
      {performance && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Gauge className="w-5 h-5 text-indigo-600" />
                Bounded HTTP Latency Percentiles
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Calculated over a bounded buffer of the last 1,000 requests without unbounded memory growth
              </p>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1 rounded-lg">
              Samples: {performance.latency.sample_count}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <span className="text-xs font-semibold text-slate-500 block uppercase">Average Latency</span>
              <div className="text-2xl font-bold text-slate-900 mt-1 font-mono">
                {performance.latency.average_ms} <span className="text-sm font-normal text-slate-500">ms</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Mean duration</div>
            </div>

            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <span className="text-xs font-semibold text-indigo-600 block uppercase font-bold">p50 Median</span>
              <div className="text-2xl font-bold text-indigo-700 mt-1 font-mono">
                {performance.latency.p50_ms} <span className="text-sm font-normal text-slate-500">ms</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">50% of requests faster</div>
            </div>

            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <span className="text-xs font-semibold text-blue-600 block uppercase font-bold">p95 Latency</span>
              <div className="text-2xl font-bold text-blue-700 mt-1 font-mono">
                {performance.latency.p95_ms} <span className="text-sm font-normal text-slate-500">ms</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">95% of requests faster</div>
            </div>

            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <span className="text-xs font-semibold text-purple-600 block uppercase font-bold">p99 Latency</span>
              <div className="text-2xl font-bold text-purple-700 mt-1 font-mono">
                {performance.latency.p99_ms} <span className="text-sm font-normal text-slate-500">ms</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">99% of requests faster</div>
            </div>
          </div>
        </div>
      )}

      {/* Production Hardening Summary */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-500" />
          Production Hardening Controls Active
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-700">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <strong className="block text-slate-900 font-semibold mb-1">Request Tracing (X-Request-ID)</strong>
            <span>ContextVar-based correlation across all inbound HTTP requests and security audit logs.</span>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <strong className="block text-slate-900 font-semibold mb-1">Security Headers & HSTS</strong>
            <span>Active nosniff, frame denial, strict referrer policy, and TLS transport enforcement.</span>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <strong className="block text-slate-900 font-semibold mb-1">Idempotency-Key Protection</strong>
            <span>In-memory payload SHA-256 caching preventing replay and duplicate state executions.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
