"""
Phase 9: Monitoring and Observability Metrics Collection.
Provides a thread-safe in-memory singleton for recording operational metrics,
high-resolution latency percentiles (p50, p95, p99), and event counts with bounded memory usage.
"""
import threading
import time
from typing import Dict, Any, List


class MetricsCollector:
    """Thread-safe singleton metrics collector with latency percentiles."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsCollector, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._metric_lock = threading.Lock()
        self._start_time = time.time()
        self._counters: Dict[str, int] = {
            "http_requests_total": 0,
            "http_requests_failed": 0,
            "auth_failures_total": 0,
            "qds_signatures_created": 0,
            "qds_verifications_total": 0,
            "qds_verifications_accepted": 0,
            "qds_verifications_rejected": 0,
            "threats_simulated": 0,
            "threats_detected": 0,
            "rate_limit_exceeded_total": 0,
            "incidents_created_total": 0,
            "security_events_total": 0,
            "audit_events_total": 0,
        }
        self._latencies: List[float] = []  # Bounded to last 1000 measurements
        self._max_latencies = 1000

    def increment(self, metric_name: str, count: int = 1) -> None:
        """Increment a counter by the given count."""
        with self._metric_lock:
            if metric_name in self._counters:
                self._counters[metric_name] += count
            else:
                self._counters[metric_name] = count

    def record_auth_failure(self) -> None:
        """Increment auth failure counter."""
        self.increment("auth_failures_total")

    def record_latency(self, duration_ms: float) -> None:
        """Record an HTTP request duration in milliseconds."""
        with self._metric_lock:
            self._latencies.append(duration_ms)
            if len(self._latencies) > self._max_latencies:
                self._latencies.pop(0)

    def get_latency_percentiles(self) -> Dict[str, float]:
        """Compute average, p50, p95, and p99 from the bounded latency buffer."""
        with self._metric_lock:
            latencies = sorted(self._latencies)

        if not latencies:
            return {
                "average_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "sample_count": 0,
            }

        n = len(latencies)
        avg = sum(latencies) / n
        p50 = latencies[int(n * 0.50)]
        p95 = latencies[min(int(n * 0.95), n - 1)]
        p99 = latencies[min(int(n * 0.99), n - 1)]

        return {
            "average_ms": round(avg, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "sample_count": n,
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return dedicated performance metrics payload."""
        with self._metric_lock:
            counters = dict(self._counters)
            uptime = time.time() - self._start_time

        req_total = counters.get("http_requests_total", 0)
        req_failed = counters.get("http_requests_failed", 0)
        error_rate = (req_failed / req_total) if req_total > 0 else 0.0

        return {
            "requests_total": req_total,
            "errors_total": req_failed,
            "error_rate": round(error_rate, 4),
            "auth_failures_total": counters.get("auth_failures_total", 0),
            "rate_limit_violations_total": counters.get("rate_limit_exceeded_total", 0),
            "latency": self.get_latency_percentiles(),
            "uptime_seconds": round(uptime, 2),
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """Return a full snapshot of current operational metrics."""
        with self._metric_lock:
            counters = dict(self._counters)
            uptime_seconds = time.time() - self._start_time

        percentiles = self.get_latency_percentiles()
        verifications_total = counters.get("qds_verifications_total", 0)
        verifications_accepted = counters.get("qds_verifications_accepted", 0)
        acceptance_rate = (
            verifications_accepted / verifications_total
            if verifications_total > 0
            else 1.0
        )

        return {
            "uptime_seconds": round(uptime_seconds, 2),
            "counters": counters,
            "latency": {
                "avg_ms": percentiles["average_ms"],
                "p50_ms": percentiles["p50_ms"],
                "p95_ms": percentiles["p95_ms"],
                "p99_ms": percentiles["p99_ms"],
                "sample_count": percentiles["sample_count"],
            },
            "acceptance_rate": round(acceptance_rate, 4),
        }

    def reset(self) -> None:
        """Reset all metrics (useful for isolated unit testing)."""
        with self._metric_lock:
            self._start_time = time.time()
            for key in self._counters:
                self._counters[key] = 0
            self._latencies.clear()


# Global singleton instance
metrics_collector = MetricsCollector()
