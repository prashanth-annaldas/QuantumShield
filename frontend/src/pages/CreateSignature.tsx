import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu,
  ArrowRight,
  Copy,
  Check,
  User,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { QuantumStateCard } from '../components/QuantumStateCard';
import { StatusBadge } from '../components/StatusBadge';
import { ErrorMessage } from '../components/ErrorMessage';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { qdsApi } from '../services/api';
import { QDSSession } from '../types';
import { formatDate } from '../utils/formatters';
import { useAuth } from '../hooks/useAuth';

export const CreateSignature: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [message, setMessage] = useState('');
  const [senderId, setSenderId] = useState(user?.username ? `usr-${user.username}` : 'usr-alice');
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<QDSSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreateSignature = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const newSession = await qdsApi.createSignature({
        message,
        sender_id: senderId,
      });
      setSession(newSession);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to generate quantum digital signature.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopySessionId = () => {
    if (session?.session_id) {
      navigator.clipboard.writeText(session.session_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Convert first few hex characters of message hash into educational sample bits for preview
  const sampleBits = session?.message_hash
    ? session.message_hash
      .slice(0, 8)
      .split('')
      .map((hexChar) => (parseInt(hexChar, 16) % 2))
    : [0, 1, 1, 0, 1, 0, 0, 1];

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans">
      <PageHeader
        title="QDS Cryptographic State Encoding"
      />

      {error && <ErrorMessage message={error} onRetry={() => setError(null)} />}

      {/* Message Creation Form */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Input Message Specification
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            SHA-256 Digest to 256 Qubit Register
          </span>
        </div>

        <form onSubmit={handleCreateSignature} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Message Payload to Sign
            </label>
            <textarea
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter message text, transaction payload, or contract string..."
              className="w-full p-3.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-sans focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Authorized Signer Identity
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={senderId}
                  onChange={(e) => setSenderId(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading || !message.trim()}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors shadow-sm disabled:opacity-50"
              >
                {loading && <LoadingSpinner label="" size="sm" />}
                {loading ? 'Encoding Quantum States...' : 'Generate QDS Signature'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Generated QDS Session Output */}
      {session && (
        <div className="p-6 bg-white rounded-2xl border border-indigo-100 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  QDS Session Generated
                </span>
                <StatusBadge status={session.status} size="sm" />
              </div>
              <h3 className="mt-1 text-lg font-bold font-mono text-slate-900 flex items-center gap-2">
                <span>{session.session_id}</span>
                <button
                  onClick={handleCopySessionId}
                  className="p-1 text-slate-400 hover:text-indigo-600 rounded transition-colors"
                  title="Copy Session ID"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                </button>
              </h3>
            </div>

            <button
              onClick={() => navigate('/teleportation', { state: { sessionId: session.session_id } })}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-colors shadow-sm self-start sm:self-auto"
            >
              <span>Continue to Teleportation</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Cryptographic Metadata Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">
                SHA-256 Message Digest (256-Bit)
              </span>
              <span className="mt-1 text-slate-800 font-bold break-all block">
                {session.message_hash}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">
                Cryptographic Anti-Replay Nonce
              </span>
              <span className="mt-1 text-indigo-700 font-bold break-all block">
                {session.nonce}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">
                Signature State Register
              </span>
              <span className="mt-1 text-purple-700 font-bold block text-sm">
                256 Independent Qubit States
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Timestamp: {formatDate(session.timestamp || session.created_at)}
              </span>
            </div>
          </div>

          {/* Educational Quantum States Preview */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Encoded Quantum State Register Sample (Qubits #000 - #007)
                </h4>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                Pure computational basis $|0\rangle \equiv [1, 0]^T$, $|1\rangle \equiv [0, 1]^T$
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {sampleBits.map((bit, i) => (
                <QuantumStateCard key={i} index={i} bit={bit} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
