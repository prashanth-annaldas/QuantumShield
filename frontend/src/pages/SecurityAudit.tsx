import React, { useEffect, useState } from 'react';
import {
  FileText,
  Filter,
  RefreshCw,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Lock,
} from 'lucide-react';
import { auditApi } from '../services/api';
import { AuditLog } from '../types';
import { RequestTrace } from '../components/RequestTrace';

export const SecurityAudit: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [actionFilter, setActionFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [outcomeFilter, setOutcomeFilter] = useState<string>('');
  const [requestIdFilter, setRequestIdFilter] = useState<string>('');
  const [page, setPage] = useState<number>(0);
  const pageSize = 20;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await auditApi.getLogs({
          action: actionFilter || undefined,
          severity: severityFilter || undefined,
          outcome: outcomeFilter || undefined,
          request_id: requestIdFilter || undefined,
          limit: pageSize,
          skip: page * pageSize,
        });
        if (!cancelled) {
          setLogs(res.audit_logs);
          setTotalCount(res.total_count);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          setError(detail || 'Failed to load security audit logs.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [actionFilter, severityFilter, outcomeFilter, requestIdFilter, page]);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await auditApi.getLogs({
        action: actionFilter || undefined,
        severity: severityFilter || undefined,
        outcome: outcomeFilter || undefined,
        request_id: requestIdFilter || undefined,
        limit: pageSize,
        skip: page * pageSize,
      });
      setLogs(res.audit_logs);
      setTotalCount(res.total_count);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to load security audit logs.');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'WARNING':
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'INFO':
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  const getOutcomeBadge = (outcome: string) => {
    return outcome === 'SUCCESS' ? (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
        <CheckCircle2 className="w-3 h-3" /> SUCCESS
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full">
        <XCircle className="w-3 h-3" /> FAILURE
      </span>
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div>
        <div>
          <h1 className="text-xl font-bold text-slate-900">Security Audit Trail</h1>
        </div>
      </div>

      {/* End-to-End Request Correlation Component */}
      <RequestTrace logs={logs} />

      {/* Audit Log Table and Filters */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Filters Bar */}
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
            <Filter className="w-4 h-4 text-slate-400" />
            Filters:
          </div>

          <div className="relative min-w-[180px]">
            <input
              type="text"
              placeholder="Filter by Request ID..."
              value={requestIdFilter}
              onChange={(e) => {
                setRequestIdFilter(e.target.value);
                setPage(0);
              }}
              className="w-full text-xs py-1.5 pl-3 pr-3 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
            />
          </div>

          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(0);
            }}
            className="text-xs py-1.5 px-3 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Actions</option>
            <option value="AUTH_LOGIN_SUCCESS">AUTH_LOGIN_SUCCESS</option>
            <option value="AUTH_LOGIN_FAILURE">AUTH_LOGIN_FAILURE</option>
            <option value="AUTH_REGISTER">AUTH_REGISTER</option>
            <option value="QDS_SIGNATURE_CREATED">QDS_SIGNATURE_CREATED</option>
            <option value="QDS_SIGNATURE_VERIFIED">QDS_SIGNATURE_VERIFIED</option>
            <option value="QDS_VERIFICATION_REJECTED">QDS_VERIFICATION_REJECTED</option>
            <option value="THREAT_SIMULATED">THREAT_SIMULATED</option>
            <option value="THREAT_DETECTED">THREAT_DETECTED</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setPage(0);
            }}
            className="text-xs py-1.5 px-3 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Severities</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>

          <select
            value={outcomeFilter}
            onChange={(e) => {
              setOutcomeFilter(e.target.value);
              setPage(0);
            }}
            className="text-xs py-1.5 px-3 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Outcomes</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILURE">FAILURE</option>
          </select>

          {(actionFilter || severityFilter || outcomeFilter || requestIdFilter) && (
            <button
              onClick={() => {
                setActionFilter('');
                setSeverityFilter('');
                setOutcomeFilter('');
                setRequestIdFilter('');
                setPage(0);
              }}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium ml-auto"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Table View */}
        {error ? (
          <div className="p-8 text-center text-rose-600 text-sm flex items-center justify-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        ) : loading && logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
            Loading security audit logs...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            No audit records matching the specified criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Request ID</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap text-slate-500 font-mono">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-indigo-600">
                      {log.request_id}
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900 font-mono">
                      {log.action}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-slate-800">{log.actor_user_id || 'System'}</span>
                      {log.actor_role && (
                        <span className="ml-1 text-[10px] text-slate-400">({log.actor_role})</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {log.resource_type ? (
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px]">
                          {log.resource_type}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4">{getOutcomeBadge(log.outcome)}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getSeverityBadge(
                          log.severity
                        )}`}
                      >
                        {log.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-600 max-w-xs truncate">
                      {log.metadata && Object.keys(log.metadata).length > 0 ? (
                        JSON.stringify(log.metadata)
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing <strong className="text-slate-900">{logs.length}</strong> of{' '}
            <strong className="text-slate-900">{totalCount}</strong> recorded events
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0 || loading}
              className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2">
              Page {page + 1} of {Math.max(1, totalPages)}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1 || loading}
              className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
