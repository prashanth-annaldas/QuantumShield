import React, { useState, useEffect } from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Eye,
  X,
  Database,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { threatsApi } from '../services/api';
import { ThreatLog } from '../types';
import { formatDate, formatFidelity, formatPercent } from '../utils/formatters';

export const ThreatLogs: React.FC = () => {
  const [logs, setLogs] = useState<ThreatLog[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchSession, setSearchSession] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterDecision, setFilterDecision] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');

  // Selected Log for detail modal
  const [selectedLog, setSelectedLog] = useState<ThreatLog | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await threatsApi.getThreatLogs({
        attack_type: filterType || undefined,
        decision: filterDecision || undefined,
        severity: filterSeverity || undefined,
        limit: 100,
      });
      setLogs(resp.logs || []);
      setTotalCount(resp.total_count || 0);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to fetch threat audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await threatsApi.getThreatLogs({
          attack_type: filterType || undefined,
          decision: filterDecision || undefined,
          severity: filterSeverity || undefined,
          limit: 100,
        });
        if (!cancelled) {
          setLogs(resp.logs || []);
          setTotalCount(resp.total_count || 0);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          setError(detail || 'Failed to fetch threat audit logs.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [filterType, filterDecision, filterSeverity]);

  const filteredLogs = logs.filter((log) => {
    const sId = log.qds_session_id || log.session_id || '';
    if (searchSession.trim() && !sId.toLowerCase().includes(searchSession.trim().toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans">
      <PageHeader
        title="Persisted Threat Audit Logs"
        subtitle="Forensic telemetry audit trail persisted into the database for compliance, anomaly analysis, and threat hunting."
        icon={FileText}
        badge={`Total Records: ${totalCount}`}
        actions={
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="p-2 bg-white hover:bg-slate-50 text-slate-600 rounded-xl border border-slate-200 transition-colors shadow-sm disabled:opacity-50"
            title="Refresh Logs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        }
      />

      {error && <ErrorMessage message={error} onRetry={fetchLogs} />}

      {/* Filter and Search Bar */}
      <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
          <input
            type="text"
            value={searchSession}
            onChange={(e) => setSearchSession(e.target.value)}
            placeholder="Search by session ID..."
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="grid grid-cols-3 gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="py-2 px-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Attack Types</option>
            <option value="FORGERY">FORGERY</option>
            <option value="IMPERSONATION">IMPERSONATION</option>
            <option value="REPLAY">REPLAY</option>
            <option value="CHANNEL_MANIPULATION">CHANNEL NOISE</option>
            <option value="UNAUTHORIZED_VERIFICATION">UNAUTHORIZED</option>
          </select>

          <select
            value={filterDecision}
            onChange={(e) => setFilterDecision(e.target.value)}
            className="py-2 px-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Decisions</option>
            <option value="LEGITIMATE">LEGITIMATE</option>
            <option value="SUSPICIOUS">SUSPICIOUS</option>
            <option value="MALICIOUS">MALICIOUS</option>
          </select>

          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="py-2 px-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Severities</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading && logs.length === 0 ? (
          <LoadingSpinner label="Querying Persistent Threat Logs..." size="lg" className="py-20" />
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2">
            <Database className="w-8 h-8 mx-auto text-slate-300" />
            <p className="text-sm font-semibold text-slate-600">No Threat Logs Found</p>
            <p className="text-xs">Run a signature verification or simulated attack to generate audit log records.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Session ID</th>
                  <th className="py-3 px-4">Attack Vector</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Decision</th>
                  <th className="py-3 px-4 font-mono">Fidelity (F)</th>
                  <th className="py-3 px-4 font-mono">QBER</th>
                  <th className="py-3 px-4 font-mono">Mismatch</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLogs.map((log) => {
                  const sId = log.qds_session_id || log.session_id || '—';
                  const att = log.attack_type || log.threat_type || 'NONE';
                  return (
                    <tr
                      key={log.id}
                      onClick={() => setSelectedLog(log)}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                    >
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                        {formatDate(log.created_at)}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-800">
                        {sId.length > 20 ? `${sId.slice(0, 16)}...` : sId}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-700">
                        {att}
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={log.severity} size="sm" />
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={log.decision} size="sm" />
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-800">
                        {formatFidelity(log.state_fidelity)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-800">
                        {formatPercent(log.qber_percent)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-800">
                        {formatPercent(log.mismatch_rate * 100)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="p-1 text-slate-400 group-hover:text-indigo-600 inline-block">
                          <Eye className="w-4 h-4" />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Forensic Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-2xl w-full p-6 space-y-5 overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Forensic Telemetry Entry
                </span>
                <h3 className="text-base font-bold text-slate-900 font-mono">
                  {selectedLog.qds_session_id || selectedLog.session_id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 text-[10px] uppercase block">Decision</span>
                <StatusBadge status={selectedLog.decision} size="sm" className="mt-1" />
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 text-[10px] uppercase block">Severity</span>
                <StatusBadge status={selectedLog.severity} size="sm" className="mt-1" />
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 text-[10px] uppercase block">Fidelity</span>
                <span className="font-bold text-slate-900 mt-1 block">{formatFidelity(selectedLog.state_fidelity)}</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 text-[10px] uppercase block">QBER</span>
                <span className="font-bold text-slate-900 mt-1 block">{formatPercent(selectedLog.qber_percent)}</span>
              </div>
            </div>

            {selectedLog.reason && (
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px] block">
                  Evaluation Rationales
                </span>
                <p className="text-slate-600 leading-relaxed font-sans">{selectedLog.reason}</p>
              </div>
            )}

            {selectedLog.details && (
              <div className="space-y-1.5">
                <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px] block">
                  Raw JSON Payload
                </span>
                <pre className="p-3.5 bg-slate-900 text-emerald-400 rounded-xl text-[11px] font-mono overflow-x-auto max-h-48 leading-relaxed">
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-colors"
              >
                Close Audit Entry
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
