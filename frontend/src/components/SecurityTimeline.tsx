import React from 'react';
import { SecurityEvent } from '../types';
import { StatusBadge } from './StatusBadge';
import { CheckCircle, AlertTriangle, XCircle, Clock, Key, Shield, Radio, Server } from 'lucide-react';

interface SecurityTimelineProps {
  events: SecurityEvent[];
  sessionId: string;
  className?: string;
}

export const SecurityTimeline: React.FC<SecurityTimelineProps> = ({
  events,
  sessionId,
  className = '',
}) => {
  const getIconForEvent = (type: string, severity: string) => {
    if (severity === 'CRITICAL' || type.includes('FORGERY') || type.includes('REJECT')) {
      return <XCircle className="w-4 h-4 text-rose-600" />;
    }
    if (severity === 'HIGH' || severity === 'MEDIUM' || type.includes('NOISE') || type.includes('IMPERSONATION')) {
      return <AlertTriangle className="w-4 h-4 text-amber-600" />;
    }
    if (type.includes('SIGNATURE_CREATED')) {
      return <Key className="w-4 h-4 text-indigo-600" />;
    }
    if (type.includes('TELEPORTATION')) {
      return <Radio className="w-4 h-4 text-purple-600" />;
    }
    if (type.includes('VERIFIED') || type.includes('ACCEPTED')) {
      return <CheckCircle className="w-4 h-4 text-emerald-600" />;
    }
    return <Server className="w-4 h-4 text-slate-500" />;
  };

  const getNodeColor = (type: string, severity: string) => {
    if (severity === 'CRITICAL' || type.includes('FORGERY') || type.includes('REJECT')) {
      return 'bg-rose-50 border-rose-200 text-rose-600';
    }
    if (severity === 'HIGH' || severity === 'MEDIUM') {
      return 'bg-amber-50 border-amber-200 text-amber-600';
    }
    if (type.includes('VERIFIED') || type.includes('ACCEPTED')) {
      return 'bg-emerald-50 border-emerald-200 text-emerald-600';
    }
    if (type.includes('TELEPORTATION')) {
      return 'bg-purple-50 border-purple-200 text-purple-600';
    }
    return 'bg-indigo-50 border-indigo-200 text-indigo-600';
  };

  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm p-5 ${className}`}>
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-indigo-600" />
          <h3 className="font-semibold text-slate-800 text-sm">Session Audit Timeline</h3>
        </div>
        <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
          {events.length} Events Logged
        </span>
      </div>

      {events.length === 0 ? (
        <div className="py-8 text-center text-slate-400">
          <Clock className="w-6 h-6 mx-auto mb-1 opacity-50" />
          <p className="text-xs">No events logged for session {sessionId}</p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
          {events.map((evt, idx) => {
            const nodeStyle = getNodeColor(evt.event_type, evt.severity);
            const icon = getIconForEvent(evt.event_type, evt.severity);

            return (
              <div key={evt.event_id || idx} className="relative group">
                {/* Node icon */}
                <div
                  className={`absolute -left-6 top-0.5 w-6 h-6 rounded-full border flex items-center justify-center shadow-xs transition-transform group-hover:scale-110 ${nodeStyle}`}
                >
                  {icon}
                </div>

                {/* Content */}
                <div className="bg-slate-50/70 border border-slate-100 rounded-lg p-3 group-hover:bg-slate-50 transition-colors">
                  <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-800">
                        {evt.event_type}
                      </span>
                      <StatusBadge status={evt.severity} size="sm" />
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {new Date(evt.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{evt.message}</p>

                  {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-200/60 flex flex-wrap gap-2">
                      {Object.entries(evt.metadata).map(([k, v]) => (
                        <span
                          key={k}
                          className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-600"
                        >
                          <span className="text-slate-400">{k}:</span> {typeof v === 'number' ? v.toFixed(4) : String(v)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
