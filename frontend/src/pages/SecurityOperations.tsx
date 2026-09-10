import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { LiveMetricsPanel } from '../components/LiveMetricsPanel';
import { LiveThreatFeed } from '../components/LiveThreatFeed';
import { IncidentCard } from '../components/IncidentCard';
import { StatusBadge } from '../components/StatusBadge';
import { useSecurityEvents } from '../hooks/useSecurityEvents';
import { monitoringApi, incidentsApi } from '../services/api';
import { MonitoringMetrics, Incident, IncidentStatus } from '../types';
import { Shield, Radio, RefreshCw, Trash2, AlertOctagon, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const SecurityOperations: React.FC = () => {
  const {
    events,
    connected,
    connectionState,
    connect,
    disconnect,
    clearEvents,
  } = useSecurityEvents({ autoConnect: true, maxEvents: 100 });

  const [metrics, setMetrics] = useState<MonitoringMetrics | null>(null);
  const [openIncidents, setOpenIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [m, inc] = await Promise.all([
        monitoringApi.getMetrics().catch((err) => {
          if (err?.response?.status === 403) {
            setPermissionError('SOC metrics require SECURITY_ANALYST or ADMIN role. Please log in with an elevated account.');
          }
          return null;
        }),
        incidentsApi.getIncidents({ status: 'OPEN', limit: 5 }).catch((err) => {
          if (err?.response?.status === 403) {
            setPermissionError('SOC metrics require SECURITY_ANALYST or ADMIN role. Please log in with an elevated account.');
          }
          return { incidents: [], total_count: 0, open_count: 0, critical_count: 0 };
        }),
      ]);
      if (m) { setMetrics(m); setPermissionError(null); }
      if (inc && inc.incidents) setOpenIncidents(inc.incidents);
    } catch {
      // Graceful fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const doFetch = async () => {
      try {
        setLoading(true);
        const [m, inc] = await Promise.all([
          monitoringApi.getMetrics().catch((err) => {
            if (!cancelled && err?.response?.status === 403) {
              setPermissionError('SOC metrics require SECURITY_ANALYST or ADMIN role. Please log in with an elevated account.');
            }
            return null;
          }),
          incidentsApi.getIncidents({ status: 'OPEN', limit: 5 }).catch(() => ({
            incidents: [],
            total_count: 0,
            open_count: 0,
            critical_count: 0,
          })),
        ]);
        if (!cancelled) {
          if (m) { setMetrics(m); setPermissionError(null); }
          if (inc && inc.incidents) setOpenIncidents(inc.incidents);
        }
      } catch {
        // Graceful fallback
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void doFetch();
    const timer = setInterval(() => { void doFetch(); }, 10000);
    return () => { cancelled = true; clearInterval(timer); };
  }, []);


  const handleIncidentStatusChange = async (incidentId: string, status: IncidentStatus) => {
    try {
      await incidentsApi.updateIncident(incidentId, { status });
      void fetchData();
    } catch {
      // Ignore
    }
  };

  return (
    <div className="space-y-6">
      {permissionError && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-300 rounded-xl text-sm text-amber-800">
          <span className="text-amber-500 mt-0.5">⚠</span>
          <div>
            <span className="font-bold">Access Restricted: </span>{permissionError}
          </div>
        </div>
      )}
      <PageHeader
        title="Security Operations Center (SOC)"
        subtitle="Real-time WebSocket event streaming, live threat telemetry, operational metrics, and incident triage."
        icon={Shield}
        badge="Phase 8 SOC Live"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={connected ? disconnect : connect}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                connected
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                  : 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100'
              }`}
            >
              <Radio className={`w-3.5 h-3.5 ${connected ? 'animate-pulse text-emerald-600' : 'text-rose-600'}`} />
              {connected ? 'WS Connected' : 'Reconnect WS'}
            </button>

            <button
              onClick={fetchData}
              disabled={loading}
              className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
              title="Refresh Metrics"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={clearEvents}
              className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg border border-slate-200 transition-colors"
              title="Clear Local Event Buffer"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        }
      />

      {/* Live Metrics Grid */}
      <LiveMetricsPanel metrics={metrics} wsConnected={connected} />

      {/* Main Grid: Live Feed (2/3) + Open Incidents Sidebar (1/3) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Threat Feed */}
        <div className="lg:col-span-2">
          <LiveThreatFeed events={events} maxItems={60} />
        </div>

        {/* Right 1 Col: Active Incidents Quick Panel */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <AlertOctagon className="w-4 h-4 text-rose-500" />
                <h3 className="font-semibold text-slate-800 text-sm">Active Incidents</h3>
              </div>
              <Link
                to="/incidents"
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1"
              >
                View All <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {openIncidents.length === 0 ? (
              <div className="py-8 text-center text-slate-400">
                <p className="text-xs">No active open incidents</p>
                <span className="text-[10px] text-emerald-600 font-medium">All security events normal</span>
              </div>
            ) : (
              <div className="space-y-3">
                {openIncidents.map((inc) => (
                  <IncidentCard
                    key={inc.id || inc.incident_id}
                    incident={inc}
                    canManage={true}
                    onStatusChange={(status) => handleIncidentStatusChange(inc.incident_id, status)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Connection Telemetry Box */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-2">
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-medium">WebSocket State:</span>
              <StatusBadge status={connectionState} size="sm" />
            </div>
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-medium">Events in Memory:</span>
              <span className="font-mono font-bold text-slate-800">{events.length}</span>
            </div>
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-medium">Correlation Engine:</span>
              <span className="font-semibold text-indigo-600">5 Deterministic Rules (C-01 to C-05)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
