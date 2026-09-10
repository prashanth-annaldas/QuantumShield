/**
 * Formatting and styling helper utilities for quantum and threat metrics.
 */

export const truncateHash = (hash?: string, head = 8, tail = 8): string => {
  if (!hash) return '—';
  if (hash.length <= head + tail) return hash;
  return `${hash.slice(0, head)}...${hash.slice(-tail)}`;
};

export const formatPercent = (val?: number, decimals = 2): string => {
  if (val === undefined || val === null || isNaN(val)) return '0.00%';
  return `${val.toFixed(decimals)}%`;
};

export const formatFidelity = (val?: number, decimals = 4): string => {
  if (val === undefined || val === null || isNaN(val)) return '1.0000';
  return Number(val).toFixed(decimals);
};

export const formatDate = (dateStr?: string | number): string => {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  } catch {
    return String(dateStr);
  }
};

export const getDecisionColor = (decision?: string): { bg: string; text: string; border: string } => {
  const norm = (decision || '').toUpperCase();
  if (norm === 'LEGITIMATE' || norm === 'ACCEPT') {
    return { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' };
  }
  if (norm === 'SUSPICIOUS') {
    return { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' };
  }
  if (norm === 'MALICIOUS' || norm === 'REJECT') {
    return { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' };
  }
  return { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200' };
};

export const getSeverityColor = (severity?: string): { bg: string; text: string; border: string } => {
  const norm = (severity || '').toUpperCase();
  switch (norm) {
    case 'CRITICAL':
      return { bg: 'bg-rose-100', text: 'text-rose-800', border: 'border-rose-300' };
    case 'HIGH':
      return { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' };
    case 'MEDIUM':
      return { bg: 'bg-amber-100', text: 'text-amber-800', border: 'border-amber-300' };
    case 'LOW':
      return { bg: 'bg-emerald-100', text: 'text-emerald-800', border: 'border-emerald-300' };
    default:
      return { bg: 'bg-slate-100', text: 'text-slate-800', border: 'border-slate-300' };
  }
};

export const getStatusColor = (status?: string): { bg: string; text: string; border: string } => {
  const norm = (status || '').toUpperCase();
  switch (norm) {
    case 'VERIFIED':
      return { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' };
    case 'TELEPORTED':
      return { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' };
    case 'PENDING':
    case 'ENCODED':
      return { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' };
    case 'REJECTED':
    case 'FAILED':
      return { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' };
    default:
      return { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200' };
  }
};
