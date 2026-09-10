import React from 'react';
import {
  UserCheck,
  FileText,
  Hash,
  Cpu,
  Radio,
  Send,
  ShieldCheck,
  ShieldAlert,
  Database,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
} from 'lucide-react';

export type TimelineStageStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED';

export interface TimelineStage {
  id: string;
  name: string;
  description: string;
  status: TimelineStageStatus;
  detail?: string;
}

interface DemoTimelineProps {
  stages: TimelineStage[];
  className?: string;
}

const STAGE_ICONS: Record<string, React.ElementType> = {
  auth: UserCheck,
  message: FileText,
  hash: Hash,
  encode: Cpu,
  bell: Radio,
  teleport: Send,
  verify: ShieldCheck,
  threat: ShieldAlert,
  audit: Database,
};

export const DemoTimeline: React.FC<DemoTimelineProps> = ({ stages, className = '' }) => {
  return (
    <div className={`p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4 ${className}`}>
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-200">
            Real Protocol Execution Pipeline
          </span>
          <span className="text-xs text-slate-400 font-mono">
            9-Stage End-to-End Journey
          </span>
        </div>
        <div className="flex items-center gap-4 text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-slate-300" /> Pending
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" /> Running
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Completed
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-rose-500" /> Flagged
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-9 gap-2">
        {stages.map((stage, idx) => {
          const Icon = STAGE_ICONS[stage.id] || Clock;

          let badgeColor = 'bg-slate-50 border-slate-200 text-slate-400';
          let iconColor = 'text-slate-400';
          let statusBadge = (
            <span className="text-[9px] font-semibold text-slate-400 uppercase">
              Pending
            </span>
          );

          if (stage.status === 'RUNNING') {
            badgeColor = 'bg-indigo-50 border-indigo-300 text-indigo-900 shadow-sm';
            iconColor = 'text-indigo-600 animate-pulse';
            statusBadge = (
              <span className="text-[9px] font-bold text-indigo-600 uppercase flex items-center gap-1">
                <Loader2 className="w-2.5 h-2.5 animate-spin" /> Active
              </span>
            );
          } else if (stage.status === 'SUCCESS') {
            badgeColor = 'bg-emerald-50/70 border-emerald-200 text-emerald-950';
            iconColor = 'text-emerald-600';
            statusBadge = (
              <span className="text-[9px] font-bold text-emerald-700 uppercase flex items-center gap-0.5">
                <CheckCircle2 className="w-2.5 h-2.5" /> Done
              </span>
            );
          } else if (stage.status === 'FAILED') {
            badgeColor = 'bg-rose-50 border-rose-200 text-rose-950';
            iconColor = 'text-rose-600';
            statusBadge = (
              <span className="text-[9px] font-bold text-rose-700 uppercase flex items-center gap-0.5">
                <XCircle className="w-2.5 h-2.5" /> Threat
              </span>
            );
          }

          return (
            <div
              key={stage.id}
              className={`p-3 rounded-xl border flex flex-col justify-between transition-all duration-300 ${badgeColor}`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono font-bold text-slate-400">
                    {`0${idx + 1}`}
                  </span>
                  {statusBadge}
                </div>
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
                  <h4 className="text-[11px] font-bold text-slate-800 leading-tight">
                    {stage.name}
                  </h4>
                </div>
                <p className="text-[10px] text-slate-500 leading-snug line-clamp-2">
                  {stage.description}
                </p>
              </div>

              {stage.detail && (
                <div className="mt-2 pt-1.5 border-t border-black/5 font-mono text-[9px] text-slate-600 truncate">
                  {stage.detail}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
