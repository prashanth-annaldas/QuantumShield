import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { SecurityTimeline } from '../components/SecurityTimeline';
import { realtimeApi } from '../services/api';
import { SecurityEvent } from '../types';
import { History, Search, RefreshCw, AlertCircle, Clock } from 'lucide-react';

export const SessionTimeline: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSessionId = searchParams.get('session_id') || '';

  const [sessionId, setSessionId] = useState(initialSessionId);
  const [activeSessionId, setActiveSessionId] = useState(initialSessionId);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTimeline = async (id: string) => {
    if (!id.trim()) return;
    try {
      setLoading(true);
      setError(null);
      const res = await realtimeApi.getSessionTimeline(id.trim());
      setEvents(res.events || []);
      setActiveSessionId(id.trim());
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Failed to fetch session event timeline');
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    if (initialSessionId) {
      (async () => {
        try {
          setLoading(true);
          setError(null);
          const res = await realtimeApi.getSessionTimeline(initialSessionId.trim());
          if (!cancelled) {
            setEvents(res.events || []);
            setActiveSessionId(initialSessionId.trim());
          }
        } catch (err: unknown) {
          if (!cancelled) {
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(detail || 'Failed to fetch session event timeline');
            setEvents([]);
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
    }
    return () => { cancelled = true; };
  }, [initialSessionId]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (sessionId.trim()) {
      setSearchParams({ session_id: sessionId.trim() });
      fetchTimeline(sessionId.trim());
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Session Security Timeline"
        subtitle="Inspect the complete chronological audit trail and deterministic state transitions for any QDS session."
        icon={History}
        badge="Session Audit"
      />

      {/* Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <form onSubmit={handleSearch} className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="Enter QDS Session ID (e.g. qds-sess-..., sess-...)"
              className="w-full pl-10 pr-4 py-2 text-xs border border-slate-200 rounded-lg bg-slate-50 text-slate-800 font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:bg-white transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !sessionId.trim()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs disabled:opacity-50 disabled:cursor-not-allowed transition-all inline-flex items-center gap-1.5"
          >
            {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
            Inspect Timeline
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Timeline View */}
      {activeSessionId ? (
        <SecurityTimeline events={events} sessionId={activeSessionId} />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-16 text-center text-slate-400">
          <Clock className="w-10 h-10 mx-auto mb-3 opacity-30 text-indigo-500" />
          <p className="text-sm font-semibold text-slate-600">No Session Selected</p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Enter a session ID above or navigate from the Security Operations Center to view its chronological event history.
          </p>
        </div>
      )}
    </div>
  );
};
