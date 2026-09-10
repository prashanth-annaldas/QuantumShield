import React from 'react';
import { AlertTriangle, ShieldCheck, AlertOctagon, Info } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { ThreatSeverity, ThreatDecision } from '../types';

interface ThreatAlertProps {
  severity?: ThreatSeverity | string;
  attackType?: string;
  decision: ThreatDecision | string;
  reason?: string;
  alerts?: Array<{ code?: string; severity?: string; message?: string }>;
  className?: string;
}

export const ThreatAlert: React.FC<ThreatAlertProps> = ({
  severity = 'LOW',
  attackType = 'NONE',
  decision,
  reason,
  alerts = [],
  className = '',
}) => {
  const normDecision = (decision || '').toUpperCase();

  let bannerBg = 'bg-slate-50 border-slate-200 text-slate-900';
  let Icon = Info;
  let iconColor = 'text-slate-500';

  if (normDecision === 'LEGITIMATE' || normDecision === 'ACCEPT') {
    bannerBg = 'bg-emerald-50 border-emerald-200 text-emerald-950';
    Icon = ShieldCheck;
    iconColor = 'text-emerald-600';
  } else if (normDecision === 'SUSPICIOUS') {
    bannerBg = 'bg-amber-50 border-amber-200 text-amber-950';
    Icon = AlertTriangle;
    iconColor = 'text-amber-600';
  } else if (normDecision === 'MALICIOUS' || normDecision === 'REJECT') {
    bannerBg = 'bg-rose-50 border-rose-200 text-rose-950';
    Icon = AlertOctagon;
    iconColor = 'text-rose-600';
  }

  return (
    <div className={`p-4 rounded-xl border ${bannerBg} ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5">
            <Icon className={`w-5 h-5 ${iconColor}`} />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-sm tracking-tight">
                {normDecision === 'LEGITIMATE' ? 'Signature Verified & Secure' : `Security Threat Detected: ${attackType}`}
              </span>
            </div>
            {reason && (
              <p className="mt-1 text-xs opacity-90 leading-relaxed font-sans">
                {reason}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {severity && severity !== 'NONE' && (
            <StatusBadge status={severity} size="sm" />
          )}
          <StatusBadge status={decision} size="sm" />
        </div>
      </div>

      {alerts && alerts.length > 0 && (
        <div className="mt-3 pt-3 border-t border-black/5 space-y-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Triggered Security Rules ({alerts.length})
          </span>
          {alerts.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs bg-white/80 px-2.5 py-1.5 rounded-lg border border-black/5">
              <span className="font-mono text-[11px] font-semibold text-slate-700">{item.code || 'RULE_VIOLATION'}</span>
              <span className="text-slate-600 text-[11px] truncate max-w-md">{item.message}</span>
              <StatusBadge status={item.severity || 'HIGH'} size="sm" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
