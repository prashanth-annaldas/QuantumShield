import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Cpu,
  Radio,
  Clock,
  Search,
  UserCheck,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { ThreatAlert } from '../components/ThreatAlert';
import { ErrorMessage } from '../components/ErrorMessage';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { threatsApi } from '../services/api';
import { ThreatDetectionResult } from '../types';
import { formatFidelity, formatPercent } from '../utils/formatters';

export const ThreatDetection: React.FC = () => {
  const location = useLocation();

  const [sessionId, setSessionId] = useState<string>(() => {
    const passedId = (location.state as { sessionId?: string } | null)?.sessionId;
    return passedId || '';
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ThreatDetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDetectDirect = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await threatsApi.detectThreats(id.trim());
      setResult(resp);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Threat detection failed. Make sure session ID is valid.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const passedId = (location.state as { sessionId?: string } | null)?.sessionId;
    if (passedId) {
      (async () => {
        setLoading(true);
        setError(null);
        try {
          const resp = await threatsApi.detectThreats(passedId.trim());
          if (!cancelled) setResult(resp);
        } catch (err: unknown) {
          if (!cancelled) {
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(detail || 'Threat detection failed. Make sure session ID is valid.');
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
    }
    return () => { cancelled = true; };
  }, [location.state]);

  const handleDetect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId.trim()) return;
    void handleDetectDirect(sessionId);
  };

  const fidelity = result?.metrics?.state_fidelity ?? 1.0;
  const qber = result?.metrics?.qber_percent ?? 0.0;

  // Rule verification flags
  const rule1FidelityPass = fidelity >= 0.95;
  const rule2QberPass = qber <= 5.0;
  const rule5ImpersonationPass = !result?.alerts?.some((a) => a.code?.includes('IMPERSONATION'));
  const rule6ReplayPass = !result?.alerts?.some((a) => a.code?.includes('REPLAY'));

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans">
      <PageHeader
        title="Deterministic Threat Detection Engine"
        subtitle="Analytical, non-AI rule evaluation matrix based on complex inner products, quantum error thresholds, and cryptographic bounds."
        icon={ShieldAlert}
        badge="Pure Deterministic Logic"
      />

      {error && <ErrorMessage message={error} onRetry={() => handleDetectDirect(sessionId)} />}

      {/* Target Session Search */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
        <form onSubmit={handleDetect} className="flex flex-col sm:flex-row items-end gap-3">
          <div className="flex-1 w-full">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Inspect Active QDS Session
            </label>
            <input
              type="text"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="e.g. qds-sess-xxxxxxxx"
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !sessionId.trim()}
            className="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors shadow-sm disabled:opacity-50"
          >
            {loading && <LoadingSpinner label="" size="sm" />}
            {loading ? 'Evaluating...' : 'Run Threat Audit'}
          </button>
        </form>
      </div>

      {result && (
        <div className="space-y-6">
          {/* Main Decision Banner */}
          <ThreatAlert
            decision={result.decision}
            severity={result.severity}
            attackType={result.attack_type}
            reason={result.reason}
            alerts={result.alerts}
          />

          {/* Deterministic Rule Evaluation Matrix */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
                Deterministic Rule Evaluation Matrix (Phase 4 Specification)
              </h3>
              <span className="text-[11px] font-semibold text-slate-400 font-mono">
                No Neural Networks • No Statistical AI
              </span>
            </div>

            <div className="space-y-3">
              {/* RULE 1: Fidelity */}
              <div className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${rule1FidelityPass ? 'bg-slate-50 border-slate-200' : 'bg-rose-50/50 border-rose-200'}`}>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${rule1FidelityPass ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                      Rule 1 — Quantum State Fidelity
                    </span>
                    <span className="text-xs text-slate-500 font-mono block mt-0.5">
                      Actual: F = {formatFidelity(fidelity)} | Threshold: F ≥ 0.9500
                    </span>
                  </div>
                </div>
                <div>
                  {rule1FidelityPass ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-xs">
                      <CheckCircle2 className="w-4 h-4" /> PASS
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-rose-700 font-bold text-xs">
                      <XCircle className="w-4 h-4" /> FAILED
                    </span>
                  )}
                </div>
              </div>

              {/* RULE 2: QBER */}
              <div className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${rule2QberPass ? 'bg-slate-50 border-slate-200' : 'bg-rose-50/50 border-rose-200'}`}>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${rule2QberPass ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                    <Radio className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                      Rule 2 — Quantum Bit Error Rate (QBER)
                    </span>
                    <span className="text-xs text-slate-500 font-mono block mt-0.5">
                      Actual: {formatPercent(qber)} | Threshold: QBER ≤ 5.0%
                    </span>
                  </div>
                </div>
                <div>
                  {rule2QberPass ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-xs">
                      <CheckCircle2 className="w-4 h-4" /> PASS
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-rose-700 font-bold text-xs">
                      <XCircle className="w-4 h-4" /> FAILED
                    </span>
                  )}
                </div>
              </div>

              {/* RULE 3: Anti-Replay Nonce & Timestamp */}
              <div className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${rule6ReplayPass ? 'bg-slate-50 border-slate-200' : 'bg-rose-50/50 border-rose-200'}`}>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${rule6ReplayPass ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                      Rule 3 — Cryptographic Replay & Freshness Validation
                    </span>
                    <span className="text-xs text-slate-500 font-mono block mt-0.5">
                      Delta: &lt; 300s | Nonce Status: {rule6ReplayPass ? 'Fresh (First seen)' : 'Replayed or Expired'}
                    </span>
                  </div>
                </div>
                <div>
                  {rule6ReplayPass ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-xs">
                      <CheckCircle2 className="w-4 h-4" /> PASS
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-rose-700 font-bold text-xs">
                      <XCircle className="w-4 h-4" /> FAILED
                    </span>
                  )}
                </div>
              </div>

              {/* RULE 4: Impersonation / Sender Check */}
              <div className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${rule5ImpersonationPass ? 'bg-slate-50 border-slate-200' : 'bg-rose-50/50 border-rose-200'}`}>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${rule5ImpersonationPass ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                    <UserCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                      Rule 4 — Sender Identity Token Validation
                    </span>
                    <span className="text-xs text-slate-500 font-mono block mt-0.5">
                      Binding: {rule5ImpersonationPass ? 'Matched Authorized Signer' : 'Identity Mismatch / Impersonation'}
                    </span>
                  </div>
                </div>
                <div>
                  {rule5ImpersonationPass ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-xs">
                      <CheckCircle2 className="w-4 h-4" /> PASS
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-rose-700 font-bold text-xs">
                      <XCircle className="w-4 h-4" /> FAILED
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
