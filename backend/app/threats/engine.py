"""
Non-AI / Non-ML Statistical Threat Detection & Decision Engine for QDS Framework.

Decision logic:
  LEGITIMATE  → ACCEPT  (no alerts raised)
  SUSPICIOUS  → REJECT  (only MEDIUM / HIGH severity alerts)
  MALICIOUS   → REJECT  (at least one CRITICAL severity alert)

All decisions are deterministic and rule-based — no AI / ML / neural networks.
"""
import time
from typing import Dict, Any, List, Set

from app.quantum import calculate_sequence_fidelity, calculate_qber
from app.qds.encoder import SignatureStateEncoder
from app.qds.session import QDSSession, QDSStatus
from app.threats.metrics import compute_all_metrics


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

class SecurityThresholds:
    """
    Centralised security threshold constants for the QDS threat engine.
    All numeric values are deterministic security policy — not learned parameters.
    """
    MAX_QBER_PERCENT: float = 5.0          # Max allowable QBER (5 %)
    MIN_FIDELITY: float = 0.95             # Min allowable mean state fidelity
    MAX_MISMATCH_RATE: float = 0.05        # Max state mismatch rate (5 %)
    MAX_TIMESTAMP_DELTA_SEC: float = 300.0 # Max allowable session age (300 s)
    MAX_VERIFICATION_ATTEMPTS: int = 3     # Max allowable verification attempts


# ---------------------------------------------------------------------------
# Decision Engine
# ---------------------------------------------------------------------------

class ThreatDecisionEngine:
    """
    Evaluates quantum measurement outputs, state fidelity, anti-replay nonces,
    and rate-limit rules deterministically without machine learning.

    Security rules evaluated (in order):
      1. Anti-replay nonce cache check
      2. Timestamp freshness check
      3. Sender identity / impersonation check
      4. Verification rate-limit check
      5. Quantum state fidelity + mismatch threshold
      6. Quantum Bit Error Rate (QBER) threshold
      7. Statistical deviation + forgery probability (informational metrics)

    Final classification:
      • LEGITIMATE → ACCEPT
      • SUSPICIOUS → REJECT  (one or more HIGH/MEDIUM alerts, no CRITICAL)
      • MALICIOUS  → REJECT  (one or more CRITICAL alerts)
    """

    def __init__(self) -> None:
        # In-memory nonce registry — prevents replay attacks within this engine instance
        self._nonce_cache: Set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_session(
        self,
        session: QDSSession,
        authorized_sender_id: str = "usr-alice",
    ) -> Dict[str, Any]:
        """
        Performs a full mathematical and security-policy audit on a QDS session.

        Args:
            session:               The completed QDS session (must have reconstructed_qubits).
            authorized_sender_id:  The expected / trusted sender identity.

        Returns:
            Audit report dictionary with keys:
              session_id, decision, action, threat_type,
              metrics (dict), alerts (list), evaluated_at (epoch ms).
        """
        # Increment attempt counter on every call
        session.verification_attempt_count += 1

        alerts: List[Dict[str, str]] = []
        threat_type = "NONE"

        # ── 1. Anti-Replay: Nonce Cache Check ──────────────────────────────
        nonce_reused = session.nonce in self._nonce_cache
        if nonce_reused:
            alerts.append({
                "code": "REPLAY_NONCE_REUSE",
                "severity": "CRITICAL",
                "message": (
                    f"Nonce '{session.nonce[:8]}...' has already been registered "
                    f"in this engine's nonce cache — replay attack detected."
                ),
            })
            threat_type = "REPLAY_ATTACK"

        # Register nonce for future evaluations
        self._nonce_cache.add(session.nonce)

        # ── 2. Timestamp Freshness ─────────────────────────────────────────
        current_time_sec = time.time()
        if hasattr(session.timestamp, "timestamp"):
            session_ts_sec = session.timestamp.timestamp()
        elif isinstance(session.timestamp, (int, float)):
            # Handle millisecond timestamps
            session_ts_sec = (
                session.timestamp / 1000.0
                if session.timestamp > 1e11
                else float(session.timestamp)
            )
        else:
            session_ts_sec = current_time_sec  # Cannot determine — treat as current

        session_age_sec = max(0.0, current_time_sec - session_ts_sec)
        timestamp_expired = session_age_sec > SecurityThresholds.MAX_TIMESTAMP_DELTA_SEC

        if timestamp_expired:
            alerts.append({
                "code": "REPLAY_TIMESTAMP_EXPIRED",
                "severity": "HIGH",
                "message": (
                    f"Session timestamp expired. "
                    f"Age: {session_age_sec:.1f}s "
                    f"(Max: {SecurityThresholds.MAX_TIMESTAMP_DELTA_SEC}s)."
                ),
            })
            if threat_type == "NONE":
                threat_type = "REPLAY_ATTACK"

        # ── 3. Sender Identity / Impersonation Check ───────────────────────
        is_unauthorized_sender = session.sender_id != authorized_sender_id
        if is_unauthorized_sender:
            alerts.append({
                "code": "IMPERSONATION_UNAUTHORIZED_SENDER",
                "severity": "CRITICAL",
                "message": (
                    f"Sender ID '{session.sender_id}' does not match "
                    f"authorized identity '{authorized_sender_id}'."
                ),
            })
            if threat_type == "NONE":
                threat_type = "IMPERSONATION_ATTACK"

        # ── 4. Rate-Limiting: Verification Attempt Count ───────────────────
        exceeded_attempts = (
            session.verification_attempt_count > SecurityThresholds.MAX_VERIFICATION_ATTEMPTS
        )
        if exceeded_attempts:
            alerts.append({
                "code": "UNAUTHORIZED_RATE_LIMIT_EXCEEDED",
                "severity": "MEDIUM",
                "message": (
                    f"Verification attempt count "
                    f"({session.verification_attempt_count}) "
                    f"exceeded limit ({SecurityThresholds.MAX_VERIFICATION_ATTEMPTS})."
                ),
            })
            if threat_type == "NONE":
                threat_type = "UNAUTHORIZED_VERIFICATION"

        # ── 5. Quantum State Fidelity & Mismatch Rate ──────────────────────
        mean_fidelity = calculate_sequence_fidelity(
            session.expected_qubits, session.reconstructed_qubits
        )
        mismatch_rate = 1.0 - mean_fidelity

        # ── 6. Quantum Bit Error Rate (QBER) ───────────────────────────────
        observed_bits = SignatureStateEncoder.decode_qubits_to_bits(session.reconstructed_qubits)
        qber_percent, bit_mismatches = calculate_qber(session.expected_bits, observed_bits)

        # ── Threshold Evaluation ───────────────────────────────────────────
        low_fidelity = mean_fidelity < SecurityThresholds.MIN_FIDELITY
        high_mismatch = mismatch_rate > SecurityThresholds.MAX_MISMATCH_RATE
        high_qber = qber_percent > SecurityThresholds.MAX_QBER_PERCENT

        if low_fidelity or high_mismatch:
            alerts.append({
                "code": "QUANTUM_STATE_FORGERY",
                "severity": "CRITICAL",
                "message": (
                    f"State fidelity ({mean_fidelity:.4f}) below security threshold "
                    f"({SecurityThresholds.MIN_FIDELITY}). "
                    f"Mismatch rate: {mismatch_rate * 100:.2f}%."
                ),
            })
            if threat_type == "NONE":
                threat_type = "SIGNATURE_FORGERY"

        if high_qber:
            alerts.append({
                "code": "QUANTUM_CHANNEL_NOISE_ANOMALY",
                "severity": "HIGH",
                "message": (
                    f"QBER ({qber_percent:.2f}%) exceeds threshold "
                    f"({SecurityThresholds.MAX_QBER_PERCENT}%). "
                    f"Possible eavesdropping or channel manipulation."
                ),
            })
            if threat_type == "NONE":
                threat_type = "QUANTUM_CHANNEL_MANIPULATION"

        # ── 7. Additional Statistical Metrics (informational) ─────────────
        extra_metrics = compute_all_metrics(
            expected_bits=session.expected_bits,
            observed_bits=observed_bits,
            mean_fidelity=mean_fidelity,
            qber_percent=qber_percent,
            mismatch_rate=mismatch_rate,
        )

        # ── Final Classification ───────────────────────────────────────────
        if not alerts:
            decision = "LEGITIMATE"
            action = "ACCEPT"
            session.status = QDSStatus.VERIFIED
        elif any(a["severity"] == "CRITICAL" for a in alerts):
            decision = "MALICIOUS"
            action = "REJECT"
            session.status = QDSStatus.REJECTED
        else:
            decision = "SUSPICIOUS"
            action = "REJECT"
            session.status = QDSStatus.REJECTED

        return {
            "session_id": session.session_id,
            "decision": decision,
            "action": action,
            "threat_type": threat_type,
            "metrics": {
                "state_fidelity": round(mean_fidelity, 4),
                "mismatch_rate": round(mismatch_rate, 4),
                "qber_percent": round(qber_percent, 2),
                "bit_mismatches": bit_mismatches,
                "total_bits": len(session.expected_bits),
                "session_age_seconds": round(session_age_sec, 2),
                "attempt_count": session.verification_attempt_count,
                "statistical_deviation": extra_metrics["statistical_deviation"],
                "forgery_probability": extra_metrics["forgery_probability"],
            },
            "alerts": alerts,
            "evaluated_at": int(time.time() * 1000),
        }
