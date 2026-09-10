import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Radio, ArrowRight } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { CircuitDiagram } from '../components/CircuitDiagram';
import { StatusBadge } from '../components/StatusBadge';
import { ErrorMessage } from '../components/ErrorMessage';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { qdsApi } from '../services/api';
import { QDSSession, TeleportResponse } from '../types';

export const TeleportationSim: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [sessionId, setSessionId] = useState<string>(() => {
    const passedId = (location.state as { sessionId?: string } | null)?.sessionId;
    return passedId || '';
  });
  const [loading, setLoading] = useState(false);
  const [teleportResult, setTeleportResult] = useState<TeleportResponse['data'] | null>(null);
  const [sessionDetails, setSessionDetails] = useState<QDSSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSession = async (id: string) => {
    try {
      const sess = await qdsApi.getSession(id);
      setSessionDetails(sess);
    } catch {
      // Ignore if not found yet
    }
  };

  useEffect(() => {
    let cancelled = false;
    const passedId = (location.state as { sessionId?: string } | null)?.sessionId;
    if (passedId) {
      (async () => {
        try {
          const sess = await qdsApi.getSession(passedId);
          if (!cancelled) setSessionDetails(sess);
        } catch {
          // Ignore
        }
      })();
    }
    return () => { cancelled = true; };
  }, [location.state]);

  const handleTeleport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const resp = await qdsApi.teleportSignature(sessionId.trim());
      setTeleportResult(resp.data);
      await loadSession(sessionId.trim());
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to execute quantum teleportation protocol.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans">
      <PageHeader
        title="Quantum Teleportation Simulator"
        subtitle="Step 2: Transmits the 256-qubit digital signature state from Alice to Bob using pre-shared Bell pairs and classical measurement channels."
        icon={Radio}
        badge="Stage 2 of 3"
      />

      {error && <ErrorMessage message={error} onRetry={() => setError(null)} />}

      {/* Session Input Form */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <form onSubmit={handleTeleport} className="flex flex-col sm:flex-row items-end gap-3">
          <div className="flex-1 w-full">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Active QDS Session Identifier
            </label>
            <input
              type="text"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="e.g. qds-sess-xxxxxxxx"
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !sessionId.trim()}
            className="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors shadow-sm disabled:opacity-50"
          >
            {loading && <LoadingSpinner label="" size="sm" />}
            {loading ? 'Teleporting...' : 'Transmit Signature'}
          </button>
        </form>

        {sessionDetails && (
          <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs font-mono text-slate-500 gap-2">
            <div>
              <span className="text-slate-400">Sender:</span>{' '}
              <span className="font-semibold text-slate-800">{sessionDetails.sender_id || 'usr-alice'}</span>
            </div>
            <div>
              <span className="text-slate-400">Status:</span>{' '}
              <StatusBadge status={sessionDetails.status} size="sm" />
            </div>
            <div>
              <span className="text-slate-400">Message Digest:</span>{' '}
              <span className="font-semibold text-slate-800">
                {sessionDetails.message_hash?.slice(0, 16)}...
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Interactive Circuit Visualization */}
      <CircuitDiagram
        classicalBits={teleportResult?.classical_bits?.slice(0, 2) || [0, 1]}
        fidelity={1.0}
        bellPairCount={teleportResult?.bell_pair_count || 256}
      />

      {/* Teleportation Execution Results */}
      {teleportResult && (
        <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Transmission Status
                </span>
                <StatusBadge status={teleportResult.status} size="sm" />
              </div>
              <h3 className="mt-1 text-base font-bold text-slate-900">
                Quantum State Reconstructed by Bob with 100% Deterministic Fidelity
              </h3>
            </div>

            <button
              onClick={() => navigate('/verification', { state: { sessionId } })}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-colors shadow-sm self-start sm:self-auto"
            >
              <span>Proceed to Verification</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Teleported Classical Syndrome Preview */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700 uppercase tracking-wider">
                Classical Measurement Bit Stream (First 64 of 256 bits)
              </span>
              <span className="font-mono text-slate-400 text-[11px]">
                Total: {teleportResult.classical_bits?.length || 256} bits
              </span>
            </div>
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl font-mono text-xs text-slate-700 break-all leading-relaxed">
              {teleportResult.classical_bits?.slice(0, 64).join('') || '0110100101101111...'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
