import React, { useState } from 'react';
import { SecurityEvent } from '../types';
import { StatusBadge } from './StatusBadge';
import { ShieldAlert, Filter, Activity, Clock } from 'lucide-react';

interface LiveThreatFeedProps {
  events: SecurityEvent[];
  maxItems?: number;
  showFilter?: boolean;
  className?: string;
}

export const LiveThreatFeed: React.FC<LiveThreatFeedProps> = ({
  events,
  maxItems = 50,
  showFilter = true,
  className = '',
}) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');

  const filteredEvents = events
    .filter((e) => {
      if (selectedSeverity === 'ALL') return true;
      return e.severity === selectedSeverity;
    })
    .slice(0, maxItems);

  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Activity className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 text-sm">Live Security Event Feed</h3>
            <p className="text-xs text-slate-500">Real-time WebSocket event stream ({events.length} buffered)</p>
          </div>
        </div>

        {showFilter && (
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical Only</option>
              <option value="HIGH">High Only</option>
              <option value="MEDIUM">Medium Only</option>
              <option value="LOW">Low Only</option>
              <option value="INFO">Info Only</option>
            </select>
          </div>
        )}
      </div>

      {/* Feed List */}
      <div className="divide-y divide-slate-100 max-h-[460px] overflow-y-auto">
        {filteredEvents.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <ShieldAlert className="w-8 h-8 mx-auto mb-2 opacity-40 text-slate-400" />
            <p className="text-xs font-medium">No security events matching filter</p>
          </div>
        ) : (
          filteredEvents.map((evt, idx) => (
            <div
              key={evt.event_id || idx}
              className="p-3.5 hover:bg-slate-50/80 transition-colors flex items-start justify-between gap-3"
            >
              <div className="space-y-1 flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <StatusBadge status={evt.severity} size="sm" />
                  <span className="text-xs font-mono font-semibold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
                    {evt.event_type}
                  </span>
                  {evt.session_id && (
                    <span className="text-[11px] font-mono text-slate-400">
                      ID: {evt.session_id.slice(0, 12)}...
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 leading-relaxed break-words">{evt.message}</p>
                {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                  <div className="text-[10px] font-mono text-slate-400 flex flex-wrap gap-2 pt-0.5">
                    {Object.entries(evt.metadata).map(([k, v]) => (
                      <span key={k} className="bg-slate-50 px-1.5 py-0.5 rounded border border-slate-100">
                        {k}: {typeof v === 'number' ? v.toFixed(3) : String(v)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="text-[10px] text-slate-400 whitespace-nowrap flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-300" />
                {new Date(evt.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
