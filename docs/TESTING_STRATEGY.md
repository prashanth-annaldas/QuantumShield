# Comprehensive Testing Strategy & Validation Plan

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. Testing Philosophy & Quality Assurance

To ensure scientific rigor, mathematical accuracy, and cryptographic reliability, the framework enforces a multi-tier testing strategy. Every mathematical gate, teleportation sequence, threat evaluation rule, REST API endpoint, and UI component undergoes explicit automated testing.

---

## 2. Testing Matrix

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 1. MATHEMATICAL QUANTUM ENGINE TESTS (Pytest + NumPy)                      │
│    - Matrix Unitary Verification: U^† U = I                                │
│    - State Vector Normalization: |α|^2 + |β|^2 = 1                         │
│    - Bell Pair Entanglement Norms                                          │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 2. QDS TELEPORTATION PROTOCOL TESTS (Pytest)                               │
│    - Ideal Teleportation Fidelity F = 1.0                                  │
│    - Classical Measurement Bit Mapping (00, 01, 10, 11)                   │
│    - Bob Pauli Correction Verification                                     │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 3. NON-AI THREAT DETECTION ENGINE TESTS (Pytest)                           │
│    - 100% Detection Rate on Injected Attack Callsets                        │
│    - QBER & Fidelity Threshold Trigger Audit                              │
│    - Anti-Replay Nonce Cache & Expiry Testing                              │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 4. FASTAPI END-TO-END REST API TESTS (Pytest + HTTPX)                      │
│    - Auth, Token Verification, RBAC Permission Enforcement                 │
│    - /qds/encode, /qds/teleport, /qds/verify Lifecycle Test               │
│    - JSON Response Schema Validation                                       │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 5. FRONTEND COMPONENT & UI VALIDATION (Vitest / React Testing Library)     │
│    - Bright Theme Styling Token Consistency                                │
│    - Circuit Animation & Stepper Render Tests                              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Test Modules & Code Examples

### 3.1 Quantum Engine Unit Tests (`tests/test_quantum_engine.py`)
* **Unitary Gate Validation**:
  Validate that all implemented matrices $H, X, Y, Z, CNOT$ satisfy $U^\dagger U = I$:
  ```python
  import numpy as np
  from backend.app.quantum.gates import Hadamard, PauliX, CNOT

  def test_gate_unitaries():
      for Gate in [Hadamard, PauliX]:
          U = Gate.matrix
          U_dagger = np.conj(U.T)
          identity = np.eye(2, dtype=complex)
          assert np.allclose(U_dagger @ U, identity, atol=1e-7)
  ```
* **State Normalization**:
  Verify that created qubits maintain $\langle \psi | \psi \rangle = 1.0$.
* **Bell State Entanglement**:
  Verify that $|\Phi^+\rangle = \frac{1}{\sqrt{2}}\begin{bmatrix} 1 & 0 & 0 & 1 \end{bmatrix}^T$.

---

### 3.2 QDS Teleportation Protocol Tests (`tests/test_qds_protocol.py`)
* **Ideal Channel Teleportation**:
  Ensure that for an uncorrupted channel, Bob's reconstructed state $|\psi_{rec}\rangle$ yields fidelity $F = 1.0$ relative to Alice's initial state $|\psi_{init}\rangle$ across 1000 randomized test states.
* **Pauli Correction Mapping**:
  Exhaustively test all 4 classical bit outcomes ($00 \to I$, $01 \to X$, $10 \to Z$, $11 \to XZ$) to confirm correct state recovery.

---

### 3.3 Non-AI Threat Engine Tests (`tests/test_threat_detection.py`)
* **Signature Forgery Injection**:
  Inject random bit flips into 10% of signature qubits and verify that `decision == "MALICIOUS"`, `threat_type == "SIGNATURE_FORGERY"`, and $QBER > 5.0\%$.
* **Replay Attack Injection**:
  Submit an identical `nonce` twice within 1 second and verify immediate detection (`threat_type == "REPLAY_ATTACK"`).
* **Quantum Channel Noise Injection**:
  Apply phase noise $\theta_{noise} = 30^\circ$ and confirm $QBER$ escalation and `SUSPICIOUS` status trigger.

---

### 3.4 API End-to-End Tests (`tests/test_api_endpoints.py`)
* **Authentication**: Test login with valid/invalid credentials, verify JWT signature and expiration.
* **QDS Signature Lifecycle**:
  ```python
  def test_qds_lifecycle(test_client, auth_headers):
      # Step 1: Encode
      res1 = test_client.post("/api/v1/qds/encode", json={"message": "Pay ₹100"}, headers=auth_headers)
      assert res1.status_code == 200
      session_id = res1.json()["data"]["session_id"]
      
      # Step 2: Teleport
      res2 = test_client.post("/api/v1/qds/teleport", json={"session_id": session_id}, headers=auth_headers)
      assert res2.status_code == 200
      
      # Step 3: Verify
      res3 = test_client.post("/api/v1/qds/verify", json={"session_id": session_id}, headers=auth_headers)
      assert res3.status_code == 200
      assert res3.json()["data"]["decision"] == "LEGITIMATE"
  ```

---

## 4. Test Execution & Coverage Targets

* **Unit Test Coverage Target**: $> 90\%$ code coverage for `backend/app/quantum/` and `backend/app/threats/`.
* **Protocol Test Pass Target**: $100\%$ pass rate across all simulated quantum state configurations.
* **Execution Command**:
  ```bash
  pytest --cov=backend/app --cov-report=term-missing tests/
  ```
