import React, { useState } from 'react';
import { Search, Shield, Key, Activity, AlertTriangle, CheckCircle } from 'lucide-react';
import { AuditLog } from '../types';

interface RequestTraceProps {
  logs: AuditLog[];
}

export const RequestTrace: React.FC<RequestTraceProps> = ({ logs }) => {
  const [selectedRequestId, setSelectedRequestId] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Extract unique request IDs
  const requestIds = Array.from(new Set(logs.map((l) => l.request_id).filter(Boolean)));

  const activeRequestId = selectedRequestId || (requestIds.length > 0 ? requestIds[0] : '');
  const matchingLogs = logs.filter((l) => l.request_id === activeRequestId);

  const filteredRequestIds = requestIds.filter((id) =>
    id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-5 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            End-to-End Request Correlation Tracer
          </h3>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search Request ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 min-h-[300px]">
        {/* Request ID Selector */}
        <div className="md:col-span-4 border-r border-slate-200 bg-slate-50/50 p-3 max-h-[360px] overflow-y-auto">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2 mb-2">
            Recent Correlation IDs ({filteredRequestIds.length})
          </p>
          {filteredRequestIds.length === 0 ? (
            <p className="text-xs text-slate-400 italic px-2">No request IDs found</p>
          ) : (
            <div className="space-y-1">
              {filteredRequestIds.map((reqId) => {
                const isSelected = reqId === activeRequestId;
                const count = logs.filter((l) => l.request_id === reqId).length;
                return (
                  <button
                    key={reqId}
                    onClick={() => setSelectedRequestId(reqId)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs font-mono transition-colors flex items-center justify-between ${isSelected
                      ? 'bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200 shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100'
                      }`}
                  >
                    <span className="truncate">{reqId}</span>
                    <span className="ml-2 px-1.5 py-0.5 rounded-full text-[10px] bg-slate-200 text-slate-700">
                      {count} {count === 1 ? 'event' : 'events'}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Trace Flow Visualization */}
        <div className="md:col-span-8 p-5">
          {matchingLogs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center py-12">
              <Shield className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm font-medium">Select a Request ID to view correlation chain</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-xs text-slate-500 font-mono">
                  Trace Target: <strong className="text-indigo-600">{activeRequestId}</strong>
                </span>
                <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Correlated Pipeline
                </span>
              </div>

              {/* Step Sequence */}
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                {matchingLogs.map((log, idx) => {
                  const isAuth = log.action.startsWith('AUTH');
                  const isQds = log.action.startsWith('QDS');
                  const isThreat = log.action.startsWith('THREAT');

                  let icon = <Activity className="w-4 h-4 text-slate-500" />;
                  let badgeColor = 'bg-slate-100 text-slate-700';

                  if (isAuth) {
                    icon = <Key className="w-4 h-4 text-blue-600" />;
                    badgeColor = 'bg-blue-50 text-blue-700 border-blue-200';
                  } else if (isQds) {
                    icon = <Shield className="w-4 h-4 text-indigo-600" />;
                    badgeColor = 'bg-indigo-50 text-indigo-700 border-indigo-200';
                  } else if (isThreat) {
                    icon = <AlertTriangle className="w-4 h-4 text-amber-600" />;
                    badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
                  }

                  return (
                    <div key={log.id || idx} className="relative group">
                      <div className="absolute -left-[27px] top-1 w-5 h-5 rounded-full bg-white border-2 border-indigo-600 flex items-center justify-center shadow-xs">
                        <div className="w-2 h-2 rounded-full bg-indigo-600" />
                      </div>

                      <div className="p-3.5 rounded-lg border border-slate-200 bg-white hover:border-indigo-300 transition-shadow shadow-xs">
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <div className="flex items-center gap-2">
                            {icon}
                            <span className="text-xs font-bold text-slate-900 font-mono">{log.action}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded border font-medium ${badgeColor}`}>
                              {log.resource_type || 'PIPELINE'}
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-400 font-mono">
                            {new Date(log.created_at).toLocaleTimeString()}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 mt-2 bg-slate-50 p-2.5 rounded border border-slate-100">
                          <div>
                            <span className="text-slate-400 text-[10px] uppercase block">Actor</span>
                            <span className="font-medium text-slate-700">{log.actor_user_id || 'System Anonymous'}</span> ({log.actor_role || 'PUBLIC'})
                          </div>
                          <div>
                            <span className="text-slate-400 text-[10px] uppercase block">Outcome & Severity</span>
                            <span className={`font-semibold ${log.outcome === 'SUCCESS' ? 'text-emerald-600' : 'text-rose-600'}`}>
                              {log.outcome}
                            </span>{' '}
                            • <span className="text-slate-600">{log.severity}</span>
                          </div>
                          {log.metadata && Object.keys(log.metadata).length > 0 && (
                            <div className="col-span-2 pt-1 border-t border-slate-200/60 font-mono text-[11px] text-slate-600">
                              <span className="text-slate-400 text-[10px] uppercase block font-sans">Details</span>
                              <pre className="whitespace-pre-wrap text-[10px] text-slate-700 mt-0.5 max-h-24 overflow-y-auto">
                                {JSON.stringify(log.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
