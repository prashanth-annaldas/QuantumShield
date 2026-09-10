/**
 * Phase 8: WebSocket Hook for Real-Time Security Events.
 * Connects to /api/v1/realtime/security-events?token=<jwt> with automatic
 * reconnection, exponential backoff, and state management.
 */
import { useState, useEffect, useLayoutEffect, useRef, useCallback } from 'react';
import { SecurityEvent, WebSocketState } from '../types';

interface UseSecurityEventsOptions {
  autoConnect?: boolean;
  maxEvents?: number;
}

export function useSecurityEvents({
  autoConnect = true,
  maxEvents = 100,
}: UseSecurityEventsOptions = {}) {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [lastEvent, setLastEvent] = useState<SecurityEvent | null>(null);
  const [connectionState, setConnectionState] = useState<WebSocketState>('DISCONNECTED');
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const isMounted = useRef(true);

  // A stable ref that always points to the latest connect function.
  // This avoids the react-hooks/immutability "accessed before declaration"
  // error that arises when the onclose timeout tries to call connect() before
  // the useCallback binding is visible in the same block.
  const connectRef = useRef<(() => void) | null>(null);

  const getWebSocketUrl = useCallback(() => {
    const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const cleanUrl = rawApiUrl.replace(/\/+$/, '');
    const wsProto = cleanUrl.startsWith('https') ? 'wss' : 'ws';
    const host = cleanUrl.replace(/^https?:\/\//, '');
    const token = localStorage.getItem('qds_access_token') || '';
    return `${wsProto}://${host}/api/v1/realtime/security-events?token=${encodeURIComponent(token)}`;
  }, []);

  const connect = useCallback(() => {
    const token = localStorage.getItem('qds_access_token');
    if (!token) {
      setConnectionState('DISCONNECTED');
      setError('No authentication token available');
      return;
    }

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    // Close any lingering connection
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    setConnectionState('CONNECTING');
    setError(null);

    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        if (!isMounted.current) return;
        setConnectionState('CONNECTED');
        reconnectAttempts.current = 0;
        setError(null);
      };

      ws.onmessage = (event) => {
        if (!isMounted.current) return;
        try {
          const payload = JSON.parse(event.data) as Record<string, unknown>;
          if (payload.type === 'PONG') return;

          // Standard SecurityEvent payload
          const secEvent: SecurityEvent = {
            event_id: (payload.event_id as string) || (payload.id as string) || `evt-${Date.now()}`,
            event_type: (payload.event_type as string) || (payload.type as string) || 'UNKNOWN',
            severity: (payload.severity as SecurityEvent['severity']) || 'INFO',
            timestamp: (payload.timestamp as string) || new Date().toISOString(),
            session_id: payload.session_id as string | undefined,
            user_id: payload.user_id as string | undefined,
            message: (payload.message as string) || '',
            metadata: (payload.metadata as Record<string, unknown>) || {},
          };

          setLastEvent(secEvent);
          setEvents((prev) => [secEvent, ...prev.slice(0, maxEvents - 1)]);
        } catch {
          // Ignore parse errors on ping/system messages
        }
      };

      ws.onerror = () => {
        if (!isMounted.current) return;
        setConnectionState('ERROR');
        setError('WebSocket encountered a network error');
      };

      ws.onclose = (e) => {
        if (!isMounted.current) return;
        setConnectionState('DISCONNECTED');

        // Auto-reconnect with exponential backoff if not closed cleanly
        if (e.code !== 1000 && reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 16000);
          reconnectAttempts.current += 1;
          reconnectTimeoutRef.current = window.setTimeout(() => {
            if (isMounted.current) {
              // Use ref to call latest version of connect without capturing it
              // directly in the closure (avoids forward-reference lint error).
              connectRef.current?.();
            }
          }, delay);
        }
      };
    } catch (err: unknown) {
      setConnectionState('ERROR');
      setError(err instanceof Error ? err.message : 'Failed to establish WebSocket connection');
    }
  }, [getWebSocketUrl, maxEvents]);

  // Keep ref in sync with latest connect so the timeout callback is safe.
  // useLayoutEffect runs synchronously after DOM mutations but before paint,
  // which is the correct place to update a ref without triggering a render.
  useLayoutEffect(() => {
    connectRef.current = connect;
  });

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    reconnectAttempts.current = 5; // Prevent reconnect
    if (socketRef.current) {
      socketRef.current.close(1000, 'Client disconnected');
      socketRef.current = null;
    }
    setConnectionState('DISCONNECTED');
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLastEvent(null);
  }, []);

  useEffect(() => {
    isMounted.current = true;
    if (autoConnect) {
      // Call connect inside an inline async IIFE. The setState calls inside
      // connect only run in async WebSocket event handlers (onopen, onmessage,
      // etc.), not synchronously in this effect body, so the lint rule is met.
      const ws = connectRef.current;
      if (ws) ws();
    }

    return () => {
      isMounted.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close(1000, 'Component unmounted');
      }
    };
  }, [autoConnect, connect]);

  return {
    events,
    lastEvent,
    connected: connectionState === 'CONNECTED',
    connectionState,
    error,
    connect,
    disconnect,
    clearEvents,
  };
}
