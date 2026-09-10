import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  variant?: 'indigo' | 'purple' | 'cyan' | 'emerald' | 'amber' | 'rose' | 'slate';
  badge?: string;
  badgeType?: 'success' | 'warning' | 'danger' | 'neutral';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'indigo',
  badge,
  badgeType = 'neutral',
  className = '',
}) => {
  const variantStyles = {
    indigo: {
      bg: 'bg-indigo-50/50',
      border: 'border-indigo-100',
      iconBg: 'bg-indigo-50 text-indigo-600',
      hoverBorder: 'hover:border-indigo-300',
    },
    purple: {
      bg: 'bg-purple-50/50',
      border: 'border-purple-100',
      iconBg: 'bg-purple-50 text-purple-600',
      hoverBorder: 'hover:border-purple-300',
    },
    cyan: {
      bg: 'bg-cyan-50/50',
      border: 'border-cyan-100',
      iconBg: 'bg-cyan-50 text-cyan-600',
      hoverBorder: 'hover:border-cyan-300',
    },
    emerald: {
      bg: 'bg-emerald-50/50',
      border: 'border-emerald-100',
      iconBg: 'bg-emerald-50 text-emerald-600',
      hoverBorder: 'hover:border-emerald-300',
    },
    amber: {
      bg: 'bg-amber-50/50',
      border: 'border-amber-100',
      iconBg: 'bg-amber-50 text-amber-600',
      hoverBorder: 'hover:border-amber-300',
    },
    rose: {
      bg: 'bg-rose-50/50',
      border: 'border-rose-100',
      iconBg: 'bg-rose-50 text-rose-600',
      hoverBorder: 'hover:border-rose-300',
    },
    slate: {
      bg: 'bg-slate-50/50',
      border: 'border-slate-200',
      iconBg: 'bg-slate-100 text-slate-600',
      hoverBorder: 'hover:border-slate-300',
    },
  }[variant];

  const badgeStyles = {
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border-rose-200',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  }[badgeType];

  return (
    <div
      className={`bg-white rounded-xl p-5 border transition-all duration-200 shadow-sm hover:shadow-md ${variantStyles.border} ${variantStyles.hoverBorder} ${className}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        {Icon && (
          <div className={`p-2 rounded-lg ${variantStyles.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <div className="text-2xl font-bold font-mono tracking-tight text-slate-900">
          {value}
        </div>
        {badge && (
          <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${badgeStyles}`}>
            {badge}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-500 font-medium">
          {subtitle}
        </p>
      )}
    </div>
  );
};
