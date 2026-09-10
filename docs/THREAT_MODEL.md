# Cybersecurity Threat Model & Non-AI Detection Specification

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. Threat Detection Philosophy (Non-AI / Non-ML)

In classical and quantum cybersecurity, AI/ML models can suffer from black-box unexplainability, adversarial manipulation, and false positives. 

This project enforces a **strictly non-AI threat detection architecture**. All security decisions are grounded in:
1. **Quantum Linear Algebra Metrics**: State fidelity $F$, Quantum Bit Error Rate ($QBER$), state vector mismatch rate $\mu$.
2. **Cryptographic Protocol Validation**: Session ID uniqueness, anti-replay nonces, timestamp validity windows ($\Delta t$).
3. **Behavioral Rate Limits & Policy Enforcements**: Verification attempt counters, role-based access tokens.

---

## 2. Threat Vector Definitions & Detection Algorithms

```
                                  ┌───────────────────────────────────┐
                                  │      OBSERVED SIGNATURE SESSION   │
                                  └─────────────────┬─────────────────┘
                                                    │
             ┌──────────────────────┬───────────────┴───────────────┬──────────────────────┐
             ▼                      ▼                               ▼                      ▼
    [ PROTOCOL CHECK ]     [ QUANTUM FIDELITY ]           [ NOISE & QBER ]        [ RATE & AUTH ]
    - Nonce Cache          - Fidelity F < 0.95            - QBER > 5.0%           - Attempt Count > 3
    - Timestamp Δt > 300s  - Mismatch Rate μ > 5%         - Bit-flip Anomaly      - Invalid Role
             │                      │                               │                      │
             ▼                      ▼                               ▼                      ▼
    (Replay Detected)     (Forgery / Impersonation)       (Channel Interference) (Unauthorized Access)
             │                      │                               │                      │
             └──────────────────────┴───────────────┬───────────────┘──────────────────────┘
                                                    │
                                                    ▼
                                     ┌─────────────────────────────┐
                                     │  THREAT DETECTION MATRIX    │
                                     │  LEGITIMATE or REJECT+ALERT │
                                     └─────────────────────────────┘
```

### 2.1 Threat Vector 1 — Signature Forgery
* **Attack Scenario**: An attacker intercepts the transmission payload and modifies classical message content $M \to M'$ or tampers with classical measurement bits $m_1 m_2$.
* **Impact**: Message content or signature bits are altered.
* **Detection Logic**:
  1. Re-calculate SHA-256 hash $H(M')$.
  2. Compute expected qubit sequence $|\psi_{exp}\rangle$ from $H(M')$.
  3. Compare Bob's reconstructed qubits $|\psi_{rec}\rangle$ against expected qubits.
  4. Calculate State Mismatch Rate:
     $$\mu = 1 - \bar{F} = 1 - \frac{1}{N}\sum_{k=1}^N |\langle \psi_{exp}^{(k)} | \psi_{rec}^{(k)} \rangle|^2$$
* **Threshold Condition**: If $\mu > \tau_{mismatch}$ (where $\tau_{mismatch} = 0.05$ or $5\%$), trigger **SIGNATURE_FORGERY** alert.

---

### 2.2 Threat Vector 2 — Impersonation Attack
* **Attack Scenario**: An attacker attempts to submit a signature session acting as Alice using an unverified public key state or mismatched identity parameters.
* **Impact**: Unauthenticated sender attempts to pass off forged signatures as legitimate.
* **Detection Logic**:
  1. Verify cryptographic sender public key fingerprint:
     $$\text{HMAC}_{K_{shared}}(M) \stackrel{?}{=} \text{Received HMAC}$$
  2. Evaluate initial state vector orientation relative to registered sender base vector.
* **Threshold Condition**: If HMAC signature validation fails OR state orientation angle $\theta_{dev} > 15^\circ$, trigger **IMPERSONATION_ATTACK** alert.

---

### 2.3 Threat Vector 3 — Replay Attack
* **Attack Scenario**: An eavesdropper intercepts a valid historical session payload $\mathcal{P}_{session}$ and re-transmits it to Bob at a later time to bypass authentication.
* **Impact**: Unauthorized execution of duplicated transactions (e.g., repeating a "Pay ₹100" request).
* **Detection Logic**:
  1. **Nonce Freshness Lookup**: Search active session cache for `nonce`.
  2. **Timestamp Window Audit**:
     $$\Delta t = |t_{current} - t_{session}|$$
* **Threshold Condition**: If `nonce` is present in `SessionNonceCache` OR $\Delta t > T_{max}$ (where $T_{max} = 300\text{ seconds}$), trigger **REPLAY_ATTACK** alert.

---

### 2.4 Threat Vector 4 — Quantum Channel Manipulation / Noise Eavesdropping
* **Attack Scenario**: An active adversary (Eve) attempts an Intercept-Resend attack on the simulated quantum channel or environment noise introduces phase-flips/bit-flips on the Bell pairs.
* **Impact**: Entanglement degradation and decoherence of teleported signature states.
* **Detection Logic**:
  1. Calculate Quantum Bit Error Rate ($QBER$) across $N$ measured qubits:
     $$QBER = \frac{\sum_{k=1}^N \mathbb{I}(\text{Observed}_k \neq \text{Expected}_k)}{N} \times 100\%$$
* **Threshold Condition**: If $QBER > \tau_{QBER}$ (where $\tau_{QBER} = 5.0\%$), trigger **QUANTUM_CHANNEL_MANIPULATION** alert.

---

### 2.5 Threat Vector 5 — Unauthorized Verification Attempts
* **Attack Scenario**: An unauthenticated user or automated bot attempts repeated brute-force signature verifications for a session ID.
* **Impact**: Denial of Service (DoS) or verification oracle exploitation.
* **Detection Logic**:
  1. Increment `verification_attempt_count` for session ID.
  2. Check user role permissions (`USER`, `SECURITY_ANALYST`, `ADMIN`).
* **Threshold Condition**: If `attempt_count` $> N_{max}$ (where $N_{max} = 3$ attempts per session) OR user lacks verification permissions, trigger **UNAUTHORIZED_VERIFICATION** alert.

---

## 3. Statistical Threat Decision Matrix

The Decision Engine evaluates all security rules deterministically and outputs a final decision status:

| Threat Category | Metric Trigger | Mathematical Threshold Rule | Decision Status | Action Taken |
| :--- | :--- | :--- | :--- | :--- |
| **None (Clean)** | All Metrics Normal | $QBER \le 5\% \land F \ge 0.95 \land \Delta t \le 300\text{s} \land \text{Nonce Fresh}$ | **LEGITIMATE** | **ACCEPT** Signature |
| **Forgery** | High Mismatch | State Mismatch Rate $\mu > 0.05 \land F < 0.95$ | **MALICIOUS** | **REJECT** + Log Forgery Alert |
| **Impersonation** | Key Mismatch | HMAC Validation Failed $\lor \theta_{dev} > 15^\circ$ | **MALICIOUS** | **REJECT** + Alert Security Officer |
| **Replay Attack** | Nonce Reuse | Nonce Found in Cache $\lor \Delta t > 300\text{s}$ | **MALICIOUS** | **REJECT** + Quarantine Session |
| **Channel Noise** | High Error Rate | $QBER > 5.0\%$ | **SUSPICIOUS** | **REJECT** + Channel Re-calibration |
| **Unauthorized** | Rate Limit / Auth | Attempt Count $> 3 \lor \text{Role Unauthorized}$ | **SUSPICIOUS** | **REJECT** + Block Client IP |

---

## 4. Threat Log Record Schema

Every threat decision creates an auditable threat log entry:
```json
{
  "log_id": "log-89f4b12c",
  "session_id": "qds-sess-9021",
  "timestamp": "2026-09-09T00:45:00Z",
  "decision": "MALICIOUS",
  "threat_type": "SIGNATURE_FORGERY",
  "metrics": {
    "qber_percent": 18.75,
    "state_fidelity": 0.8125,
    "mismatch_rate": 0.1875,
    "nonce_valid": true,
    "time_delta_seconds": 12,
    "attempt_count": 1
  },
  "explanation": "Signature verification failed: Quantum bit error rate (18.75%) exceeded security threshold (5.00%). State fidelity degraded to 0.8125."
}
```
