import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Flame,
  Sparkles,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { ThreatAlert } from '../components/ThreatAlert';
import { StatusBadge } from '../components/StatusBadge';
import { ErrorMessage } from '../components/ErrorMessage';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { threatsApi, qdsApi } from '../services/api';
import { ThreatDetectionResult } from '../types';
import { formatPercent, formatFidelity } from '../utils/formatters';

const ATTACK_OPTIONS = [
  {
    id: 'FORGERY',
    name: 'Quantum Signature Forgery',
    desc: 'Alters a fraction of reconstructed qubit states using Pauli-X bit flips to simulate malicious forgery.',
    severity: 'CRITICAL',
    hasTamperRatio: true,
  },
  {
    id: 'IMPERSONATION',
    name: 'Impersonation Attack',
    desc: 'Corrupts sender identity token to verify signature under an unauthorized sender identity.',
    severity: 'CRITICAL',
    hasTamperRatio: false,
  },
  {
    id: 'REPLAY',
    name: 'Replay Attack (Nonce Reuse & Expired Timestamp)',
    desc: 'Re-submits a previously registered nonce or backdates timestamp to bypass freshness checks.',
    severity: 'HIGH',
    hasTamperRatio: false,
  },
  {
    id: 'UNAUTHORIZED_VERIFICATION',
    name: 'Unauthorized Verification (Rate-Limit Exceeded)',
    desc: 'Executes rapid repeated verification attempts exceeding security rate-limit threshold (max 3 attempts).',
    severity: 'MEDIUM',
    hasTamperRatio: false,
  },
];

export const AttackSimulator: React.FC = () => {
  const location = useLocation();

  const [sessionId, setSessionId] = useState<string>(() => {
    const passedId = (location.state as { sessionId?: string } | null)?.sessionId;
    return passedId || '';
  });
  const [selectedAttack, setSelectedAttack] = useState<string>('FORGERY');
  const [tamperRatio, setTamperRatio] = useState<number>(0.20);
  const [errorRate, setErrorRate] = useState<number>(0.15);
  const [loading, setLoading] = useState(false);

  const [detectionResult, setDetectionResult] = useState<ThreatDetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleQuickCreateSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const sess = await qdsApi.createSignature({
        message: 'High-value transaction test payload for attack simulation',
        sender_id: 'usr-alice',
      });
      await qdsApi.teleportSignature(sess.session_id);
      setSessionId(sess.session_id);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to auto-generate session.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateAndDetect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId.trim()) return;

    setLoading(true);
    setError(null);
    try {
      // 1. Inject Attack
      await threatsApi.simulateAttack({
        session_id: sessionId.trim(),
        attack_type: selectedAttack,
        tamper_ratio: tamperRatio,
        error_rate: errorRate,
      });

      // 2. Run Deterministic Detection
      const detResp = await threatsApi.detectThreats(sessionId.trim());
      setDetectionResult(detResp);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to simulate or detect attack.');
    } finally {
      setLoading(false);
    }
  };

  const activeAttack = ATTACK_OPTIONS.find((a) => a.id === selectedAttack) || ATTACK_OPTIONS[0];

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans">
      <PageHeader
        title="Adversarial Attack Simulator"
        subtitle="Simulates realistic cyber threats against quantum digital signatures in a controlled educational sandbox."
        icon={Flame}
        badge="Controlled Cyber Sandbox"
      />

      {error && <ErrorMessage message={error} onRetry={() => setError(null)} />}

      {/* Simulator Control Panel */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              SIMULATED ATTACK INJECTION
            </span>
          </div>
          {!sessionId && (
            <button
              type="button"
              onClick={handleQuickCreateSession}
              disabled={loading}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Auto-generate Fresh Target Session</span>
            </button>
          )}
        </div>

        <form onSubmit={handleSimulateAndDetect} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Target QDS Session
            </label>
            <input
              type="text"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="Enter active session ID or click auto-generate above..."
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500"
              required
            />
          </div>

          {/* Attack Vector Selection Radio Cards */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              Select Attack Vector to Inject
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {ATTACK_OPTIONS.map((att) => (
                <div
                  key={att.id}
                  onClick={() => setSelectedAttack(att.id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${selectedAttack === att.id
                    ? 'bg-rose-50/50 border-rose-400 shadow-sm'
                    : 'bg-white border-slate-200 hover:border-slate-300'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{att.name}</span>
                    <StatusBadge status={att.severity} size="sm" />
                  </div>
                  <p className="mt-1 text-[11px] text-slate-500 leading-relaxed">{att.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Dynamic Parameters based on selected attack */}
          {activeAttack.hasTamperRatio && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex justify-between items-center text-xs font-semibold text-slate-700">
                <span>Tamper Ratio (Fraction of Qubits Flipped):</span>
                <span className="font-mono font-bold text-rose-600">{(tamperRatio * 100).toFixed(0)}% ({Math.round(256 * tamperRatio)} qubits)</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.50"
                step="0.05"
                value={tamperRatio}
                onChange={(e) => setTamperRatio(parseFloat(e.target.value))}
                className="w-full accent-rose-600 cursor-pointer"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !sessionId.trim()}
            className="w-full py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors shadow-sm disabled:opacity-50"
          >
            {loading && <LoadingSpinner label="" size="sm" />}
            {loading ? 'Simulating Attack Vector...' : 'Execute Attack Simulation & Run Detection'}
          </button>
        </form>
      </div>

      {/* Comparison View: BEFORE vs AFTER */}
      {detectionResult && (
        <div className="space-y-6">
          <ThreatAlert
            decision={detectionResult.decision}
            severity={detectionResult.severity}
            attackType={detectionResult.attack_type}
            reason={detectionResult.reason}
            alerts={detectionResult.alerts}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Baseline Before Attack */}
            <div className="p-5 rounded-xl bg-emerald-50/40 border border-emerald-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                  BASELINE (BEFORE ATTACK)
                </span>
                <StatusBadge status="LEGITIMATE" size="sm" />
              </div>
              <div className="space-y-2 font-mono text-xs text-slate-700">
                <div className="flex justify-between">
                  <span>State Fidelity:</span>
                  <span className="font-bold text-emerald-700">1.0000 (100.0%)</span>
                </div>
                <div className="flex justify-between">
                  <span>QBER:</span>
                  <span className="font-bold text-emerald-700">0.00%</span>
                </div>
                <div className="flex justify-between">
                  <span>Mismatch Rate:</span>
                  <span className="font-bold text-emerald-700">0.00%</span>
                </div>
                <div className="flex justify-between">
                  <span>Replay/Nonce:</span>
                  <span className="font-bold text-emerald-700">Fresh Nonce</span>
                </div>
              </div>
            </div>

            {/* Injected Attack Posture */}
            <div className="p-5 rounded-xl bg-rose-50/50 border border-rose-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-800">
                  OBSERVED (AFTER INJECTED ATTACK)
                </span>
                <StatusBadge status={detectionResult.decision} size="sm" />
              </div>
              <div className="space-y-2 font-mono text-xs text-slate-700">
                <div className="flex justify-between">
                  <span>State Fidelity:</span>
                  <span className="font-bold text-rose-700">
                    {formatFidelity(detectionResult.metrics.state_fidelity)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>QBER:</span>
                  <span className="font-bold text-rose-700">
                    {formatPercent(detectionResult.metrics.qber_percent)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Mismatch Rate:</span>
                  <span className="font-bold text-rose-700">
                    {formatPercent((detectionResult.metrics.mismatch_rate ?? 0) * 100)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Attack Classification:</span>
                  <span className="font-bold text-rose-700">{detectionResult.attack_type}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
