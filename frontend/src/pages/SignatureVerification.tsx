import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Activity,
  Radio,
  Cpu,
  CheckCircle2,
  XCircle,
  ArrowRight,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { ThreatAlert } from '../components/ThreatAlert';
import { MetricCard } from '../components/MetricCard';
import { ErrorMessage } from '../components/ErrorMessage';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { qdsApi } from '../services/api';
import { ThreatDetectionResult } from '../types';
import { formatPercent, formatFidelity } from '../utils/formatters';

export const SignatureVerification: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [sessionId, setSessionId] = useState<string>(() => {
    const passedId = (location.state as { sessionId?: string } | null)?.sessionId;
    return passedId || '';
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ThreatDetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerifyDirect = async (idToVerify: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await qdsApi.verifySignature(idToVerify.trim());
      setResult(resp.data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to verify quantum digital signature.');
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
          const resp = await qdsApi.verifySignature(passedId.trim());
          if (!cancelled) setResult(resp.data);
        } catch (err: unknown) {
          if (!cancelled) {
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(detail || 'Failed to verify quantum digital signature.');
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
    }
    return () => { cancelled = true; };
  }, [location.state]);

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId.trim()) return;
    void handleVerifyDirect(sessionId);
  };

  const fidelity = result?.metrics?.state_fidelity ?? 1.0;
  const qber = result?.metrics?.qber_percent ?? 0.0;
  const mismatch = (result?.metrics?.mismatch_rate ?? 0.0) * 100;
  const statDev = result?.metrics?.statistical_deviation ?? 0.0;
  const forgeryProb = (result?.metrics?.forgery_probability ?? 0.0) * 100;

  const fidelityPass = fidelity >= 0.95;
  const qberPass = qber <= 5.0;
  const mismatchPass = mismatch <= 5.0;

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans">
      <PageHeader
        title="QDS Signature Verification & Audit"
        subtitle="Step 3: Measures reconstructed states against transmitted signature vectors, evaluating pure quantum state fidelity and QBER."
        icon={ShieldCheck}
        badge="Stage 3 of 3"
      />

      {error && <ErrorMessage message={error} onRetry={() => handleVerifyDirect(sessionId)} />}

      {/* Verification Input Form */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <form onSubmit={handleVerify} className="flex flex-col sm:flex-row items-end gap-3">
          <div className="flex-1 w-full">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              QDS Session ID to Verify
            </label>
            <input
              type="text"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="e.g. qds-sess-xxxxxxxx"
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !sessionId.trim()}
            className="w-full sm:w-auto px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors shadow-sm disabled:opacity-50"
          >
            {loading && <LoadingSpinner label="" size="sm" />}
            {loading ? 'Verifying...' : 'Verify Signature'}
          </button>
        </form>
      </div>

      {/* Verification Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Decision Banner */}
          <ThreatAlert
            decision={result.decision}
            severity={result.severity}
            attackType={result.attack_type}
            reason={result.reason}
            alerts={result.alerts}
          />

          {/* Scientific Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="State Fidelity (F)"
              value={`F = ${formatFidelity(fidelity)}`}
              subtitle="Threshold: F ≥ 0.9500"
              icon={Cpu}
              variant={fidelityPass ? 'emerald' : 'rose'}
              badge={fidelityPass ? 'PASS' : 'FAIL'}
              badgeType={fidelityPass ? 'success' : 'danger'}
            />

            <MetricCard
              title="QBER"
              value={formatPercent(qber)}
              subtitle="Threshold: QBER ≤ 5.0%"
              icon={Radio}
              variant={qberPass ? 'emerald' : 'rose'}
              badge={qberPass ? 'PASS' : 'FAIL'}
              badgeType={qberPass ? 'success' : 'danger'}
            />

            <MetricCard
              title="Mismatch Rate (μ)"
              value={formatPercent(mismatch)}
              subtitle="Threshold: μ ≤ 5.0%"
              icon={Activity}
              variant={mismatchPass ? 'emerald' : 'rose'}
              badge={mismatchPass ? 'PASS' : 'FAIL'}
              badgeType={mismatchPass ? 'success' : 'danger'}
            />

            <MetricCard
              title="Forgery Probability"
              value={formatPercent(forgeryProb, 3)}
              subtitle={`σ = ${statDev.toFixed(4)}`}
              icon={ShieldAlert}
              variant={forgeryProb <= 5.0 ? 'indigo' : 'rose'}
              badge={forgeryProb <= 5.0 ? 'Negligible' : 'Critical'}
              badgeType={forgeryProb <= 5.0 ? 'success' : 'danger'}
            />
          </div>

          {/* Detailed Scientific Threshold Comparison Table */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
              Deterministic Security Threshold Evaluation
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 uppercase">
                    <th className="py-2.5 px-3">Security Metric</th>
                    <th className="py-2.5 px-3">Observed Value</th>
                    <th className="py-2.5 px-3">Acceptance Criteria</th>
                    <th className="py-2.5 px-3">Compliance Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="py-3 px-3 font-sans font-semibold text-slate-700">Quantum State Fidelity</td>
                    <td className="py-3 px-3 text-slate-900 font-bold">{formatFidelity(fidelity)}</td>
                    <td className="py-3 px-3 text-slate-500">≥ 0.9500 (95.0%)</td>
                    <td className="py-3 px-3">
                      {fidelityPass ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> COMPLIANT
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full font-bold">
                          <XCircle className="w-3.5 h-3.5" /> VIOLATION
                        </span>
                      )}
                    </td>
                  </tr>

                  <tr>
                    <td className="py-3 px-3 font-sans font-semibold text-slate-700">Quantum Bit Error Rate (QBER)</td>
                    <td className="py-3 px-3 text-slate-900 font-bold">{formatPercent(qber)}</td>
                    <td className="py-3 px-3 text-slate-500">≤ 5.00%</td>
                    <td className="py-3 px-3">
                      {qberPass ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> COMPLIANT
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full font-bold">
                          <XCircle className="w-3.5 h-3.5" /> VIOLATION
                        </span>
                      )}
                    </td>
                  </tr>

                  <tr>
                    <td className="py-3 px-3 font-sans font-semibold text-slate-700">State Mismatch Rate</td>
                    <td className="py-3 px-3 text-slate-900 font-bold">{formatPercent(mismatch)}</td>
                    <td className="py-3 px-3 text-slate-500">≤ 5.00%</td>
                    <td className="py-3 px-3">
                      {mismatchPass ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> COMPLIANT
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full font-bold">
                          <XCircle className="w-3.5 h-3.5" /> VIOLATION
                        </span>
                      )}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Quick Link to Test Attack Simulator */}
            <div className="pt-3 border-t border-slate-100 flex justify-between items-center">
              <span className="text-xs text-slate-500">
                Want to test system resilience against simulated quantum adversaries?
              </span>
              <button
                onClick={() => navigate('/attack-simulator', { state: { sessionId } })}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800"
              >
                <span>Launch Attack Simulator</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
