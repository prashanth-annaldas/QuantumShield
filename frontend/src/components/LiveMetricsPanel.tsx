import React from 'react';
import { MonitoringMetrics } from '../types';
import { MetricCard } from './MetricCard';
import { Radio, ShieldAlert, CheckCircle, AlertTriangle } from 'lucide-react';

interface LiveMetricsPanelProps {
  metrics: MonitoringMetrics | null;
  wsConnected: boolean;
  className?: string;
}

export const LiveMetricsPanel: React.FC<LiveMetricsPanelProps> = ({
  metrics,
  wsConnected,
  className = '',
}) => {
  const verificationsTotal = metrics?.qds_metrics?.verifications_total ?? 0;
  const acceptanceRate = metrics?.qds_metrics?.acceptance_rate ?? 1.0;
  const threatsSimulated = metrics?.threat_metrics?.threats_simulated ?? 0;
  const threatsDetected = metrics?.threat_metrics?.threats_detected ?? 0;
  const openIncidents = metrics?.incident_metrics?.open_incidents ?? 0;
  const criticalIncidents = metrics?.incident_metrics?.critical_incidents ?? 0;

  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
      <MetricCard
        title="WebSocket Telemetry"
        value={wsConnected ? 'CONNECTED' : 'DISCONNECTED'}
        subtitle={`Active Stream Clients: ${metrics?.websocket_metrics?.active_connections ?? 1}`}
        icon={Radio}
        variant={wsConnected ? 'emerald' : 'rose'}
        badge={wsConnected ? 'LIVE' : 'OFFLINE'}
        badgeType={wsConnected ? 'success' : 'danger'}
      />

      <MetricCard
        title="QDS Verifications"
        value={verificationsTotal}
        subtitle={`Acceptance Rate: ${(acceptanceRate * 100).toFixed(1)}%`}
        icon={CheckCircle}
        variant="indigo"
        badge={`${metrics?.qds_metrics?.verifications_accepted ?? 0} Accepted`}
        badgeType="success"
      />

      <MetricCard
        title="Threats Detected"
        value={threatsDetected}
        subtitle={`Simulations Run: ${threatsSimulated}`}
        icon={ShieldAlert}
        variant={threatsDetected > 0 ? 'amber' : 'slate'}
        badge={threatsDetected > 0 ? 'ACTIVE THREATS' : 'CLEAN'}
        badgeType={threatsDetected > 0 ? 'warning' : 'neutral'}
      />

      <MetricCard
        title="Open Incidents"
        value={openIncidents}
        subtitle={`Critical Incidents: ${criticalIncidents}`}
        icon={AlertTriangle}
        variant={criticalIncidents > 0 ? 'rose' : (openIncidents > 0 ? 'amber' : 'purple')}
        badge={criticalIncidents > 0 ? 'ACTION REQUIRED' : 'NORMAL'}
        badgeType={criticalIncidents > 0 ? 'danger' : 'neutral'}
      />
    </div>
  );
};
