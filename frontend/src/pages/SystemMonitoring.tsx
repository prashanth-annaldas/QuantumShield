import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import { monitoringApi } from '../services/api';
import { MonitoringMetrics, ReadinessStatus } from '../types';
import { Activity, Server, Cpu, Database, RefreshCw, Zap, Clock } from 'lucide-react';

export const SystemMonitoring: React.FC = () => {
  const [metrics, setMetrics] = useState<MonitoringMetrics | null>(null);
  const [readiness, setReadiness] = useState<ReadinessStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchObservabilityData = async () => {
    try {
      setLoading(true);
      const [m, r] = await Promise.all([
        monitoringApi.getMetrics().catch(() => null),
        monitoringApi.getReadiness().catch(() => null),
      ]);
      if (m) setMetrics(m);
      if (r) setReadiness(r);
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const doFetch = async () => {
      try {
        setLoading(true);
        const [m, r] = await Promise.all([
          monitoringApi.getMetrics().catch(() => null),
          monitoringApi.getReadiness().catch(() => null),
        ]);
        if (!cancelled) {
          if (m) setMetrics(m);
          if (r) setReadiness(r);
        }
      } catch {
        // Ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void doFetch();
    if (!autoRefresh) return () => { cancelled = true; };
    const interval = setInterval(() => { void doFetch(); }, 5000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [autoRefresh]);

  const formatUptime = (seconds: number = 0) => {
    const mins = Math.floor(seconds / 60);
    const hrs = Math.floor(mins / 60);
    if (hrs > 0) return `${hrs}h ${mins % 60}m`;
    return `${mins}m ${Math.floor(seconds % 60)}s`;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Observability & Monitoring"
        subtitle="Live operational telemetry, subsystem readiness probes, request latency distributions, and protocol health."
        icon={Activity}
        badge="Phase 8 Observability"
        actions={
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-600 cursor-pointer bg-white px-3 py-1.5 rounded-lg border border-slate-200">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500/20"
              />
              Auto-refresh (5s)
            </label>

            <button
              onClick={fetchObservabilityData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Now
            </button>
          </div>
        }
      />

      {/* Readiness & Subsystem Health Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <Server className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Subsystem Readiness Status</h3>
              <p className="text-xs text-slate-500">Live operational probes across framework services</p>
            </div>
          </div>
          <StatusBadge status={readiness?.status || 'UNKNOWN'} size="md" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Database className="w-4 h-4 text-indigo-600" />
              <div>
                <span className="text-xs font-bold text-slate-800 block">Database Engine</span>
                <span className="text-[10px] text-slate-500">SQLAlchemy / SQLite</span>
              </div>
            </div>
            <StatusBadge status={readiness?.checks?.database || 'HEALTHY'} size="sm" />
          </div>

          <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Cpu className="w-4 h-4 text-purple-600" />
              <div>
                <span className="text-xs font-bold text-slate-800 block">Quantum Engine</span>
                <span className="text-[10px] text-slate-500">NumPy Linear Algebra</span>
              </div>
            </div>
            <StatusBadge status={readiness?.checks?.quantum_engine || 'HEALTHY'} size="sm" />
          </div>

          <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Activity className="w-4 h-4 text-emerald-600" />
              <div>
                <span className="text-xs font-bold text-slate-800 block">Metrics Collector</span>
                <span className="text-[10px] text-slate-500">In-Memory Singleton</span>
              </div>
            </div>
            <StatusBadge status={readiness?.checks?.metrics_collector || 'HEALTHY'} size="sm" />
          </div>
        </div>
      </div>

      {/* Latency & API Health Metrics */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
          API & HTTP Gateway Performance
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total HTTP Requests"
            value={metrics?.api_metrics?.http_requests_total ?? 0}
            subtitle={`Failed: ${metrics?.api_metrics?.http_requests_failed ?? 0}`}
            icon={Server}
            variant="indigo"
          />

          <MetricCard
            title="Average Latency"
            value={`${metrics?.api_metrics?.avg_latency_ms ?? 0} ms`}
            subtitle="Mean server execution time"
            icon={Clock}
            variant="cyan"
          />

          <MetricCard
            title="P95 Latency"
            value={`${metrics?.api_metrics?.p95_latency_ms ?? 0} ms`}
            subtitle="95th percentile response time"
            icon={Zap}
            variant="purple"
          />

          <MetricCard
            title="System Uptime"
            value={formatUptime(metrics?.uptime_seconds)}
            subtitle="Continuous running duration"
            icon={Activity}
            variant="emerald"
          />
        </div>
      </div>

      {/* QDS Protocol & Threat Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* QDS Protocol Telemetry */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm">QDS Protocol Operations</h3>
            <span className="text-xs font-mono bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-semibold">
              {(metrics?.qds_metrics?.acceptance_rate ?? 1.0 * 100).toFixed(1)}% Acceptance
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Signatures Created:</span>
              <span className="font-mono font-bold text-slate-800 text-base">
                {metrics?.qds_metrics?.signatures_created ?? 0}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Total Verifications:</span>
              <span className="font-mono font-bold text-slate-800 text-base">
                {metrics?.qds_metrics?.verifications_total ?? 0}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Accepted Signatures:</span>
              <span className="font-mono font-bold text-emerald-600 text-base">
                {metrics?.qds_metrics?.verifications_accepted ?? 0}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Rejected Signatures:</span>
              <span className="font-mono font-bold text-rose-600 text-base">
                {metrics?.qds_metrics?.verifications_rejected ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* Threat Detection & Incidents */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm">Threat & Incident Operations</h3>
            <span className="text-xs font-mono bg-rose-50 text-rose-700 px-2 py-0.5 rounded font-semibold">
              {metrics?.incident_metrics?.critical_incidents ?? 0} Critical
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Threats Simulated:</span>
              <span className="font-mono font-bold text-slate-800 text-base">
                {metrics?.threat_metrics?.threats_simulated ?? 0}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Threats Detected:</span>
              <span className="font-mono font-bold text-amber-600 text-base">
                {metrics?.threat_metrics?.threats_detected ?? 0}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Rate Limit Violations:</span>
              <span className="font-mono font-bold text-slate-800 text-base">
                {metrics?.threat_metrics?.rate_limit_exceeded ?? 0}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Security Events Logged:</span>
              <span className="font-mono font-bold text-indigo-600 text-base">
                {metrics?.incident_metrics?.total_security_events ?? 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
