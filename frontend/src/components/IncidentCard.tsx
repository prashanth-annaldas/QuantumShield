import React from 'react';
import { Incident, IncidentStatus } from '../types';
import { StatusBadge } from './StatusBadge';
import { AlertOctagon, User, Clock, ChevronRight } from 'lucide-react';

interface IncidentCardProps {
  incident: Incident;
  onClick?: () => void;
  onStatusChange?: (status: IncidentStatus) => void;
  isSelected?: boolean;
  canManage?: boolean;
}

export const IncidentCard: React.FC<IncidentCardProps> = ({
  incident,
  onClick,
  onStatusChange,
  isSelected = false,
  canManage = false,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border transition-all cursor-pointer p-4 ${
        isSelected
          ? 'border-indigo-500 ring-2 ring-indigo-500/20 shadow-md'
          : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
            {incident.incident_id}
          </span>
          <StatusBadge status={incident.severity} size="sm" />
          <StatusBadge status={incident.status} size="sm" />
        </div>
        <div className="text-[11px] text-slate-400 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {new Date(incident.created_at).toLocaleDateString()}
        </div>
      </div>

      <h4 className="font-semibold text-slate-800 text-sm mb-1.5 line-clamp-1">{incident.title}</h4>
      <p className="text-xs text-slate-500 line-clamp-2 mb-3">{incident.description}</p>

      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-mono text-[11px]">
            <AlertOctagon className="w-3.5 h-3.5 text-rose-500" />
            {incident.event_count} {incident.event_count === 1 ? 'event' : 'events'}
          </span>
          {incident.assigned_to_user_id && (
            <span className="flex items-center gap-1 text-[11px]">
              <User className="w-3.5 h-3.5 text-slate-400" />
              {incident.assigned_to_user_id}
            </span>
          )}
        </div>

        {canManage && onStatusChange && (
          <div
            className="flex items-center gap-1"
            onClick={(e) => e.stopPropagation()}
          >
            {incident.status !== 'RESOLVED' && (
              <button
                type="button"
                onClick={() => onStatusChange('RESOLVED')}
                className="text-[11px] font-medium text-emerald-600 hover:bg-emerald-50 px-2 py-1 rounded border border-emerald-200 transition-colors"
              >
                Resolve
              </button>
            )}
            {incident.status === 'OPEN' && (
              <button
                type="button"
                onClick={() => onStatusChange('INVESTIGATING')}
                className="text-[11px] font-medium text-amber-600 hover:bg-amber-50 px-2 py-1 rounded border border-amber-200 transition-colors"
              >
                Investigate
              </button>
            )}
          </div>
        )}

        {!canManage && (
          <ChevronRight className="w-4 h-4 text-slate-300" />
        )}
      </div>
    </div>
  );
};
