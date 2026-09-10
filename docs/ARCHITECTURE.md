# System Architecture Specification

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. High-Level Architecture Overview

The system is designed as a multi-tier, modular micro-architecture separating quantum simulation, cryptographic protocol logic, threat observation, statistical detection, backend service APIs, and a bright-theme web interface.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REACT / TYPESCRIPT FRONTEND                       │
│  (Bright Scientific UI: Dashboard, Circuit Visualizer, Threat Logs, Analytics)│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST / JSON (Axios)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FASTAPI BACKEND API                             │
│       (Routing, JWT Authentication, RBAC, Request/Response Pydantic Models) │
└──────────┬───────────────────────────┬───────────────────────────┬──────────┘
           │                           │                           │
           ▼                           ▼                           ▼
┌────────────────────┐   ┌───────────────────────────┐   ┌────────────────────┐
│   QUANTUM ENGINE   │   │       QDS PROTOCOL        │   │  THREAT DETECTION  │
│ (NumPy Linear Alg, │◄──┤ (State Enc, Bell Pair,    ├──►│   ENGINE (Non-AI)  │
│ Gates, Teleport,   │   │  Teleport Session Flow)   │   │(QBER, Fidelity F,  │
│ Measurements)      │   └───────────────────────────┘   │ Statistical Rules) │
└────────────────────┘                                   └─────────┬──────────┘
                                                                   │
                                                                   ▼
                                                         ┌────────────────────┐
                                                         │ SQLALCHEMY / DB    │
                                                         │ (PostgreSQL/SQLite)│
                                                         └────────────────────┘
```

---

## 2. Layered Component Architecture

### 2.1 UI Presentation Layer (Frontend)
* **Framework**: React 18 with TypeScript and Vite.
* **Styling**: Tailwind CSS configured with a strictly defined **Bright Light Theme** design system.
* **State Management & Data Fetching**: React Context / Custom Hooks with Axios HTTP client.
* **Data Visualization**: Recharts for statistical error graphs, trend charts, and real-time state fidelity meters.
* **Interactive Circuit Visualizer**: Custom SVG/Canvas visualizer for quantum teleportation circuits (Alice CNOT/Hadamard gates, classical channel, Bob Pauli gates).

### 2.2 API & Application Service Layer (Backend)
* **Framework**: FastAPI (Python 3.11+).
* **API Routers**:
  * `/api/v1/auth`: JWT Login, User Registration, Profile Management.
  * `/api/v1/qds`: Message processing, QDS state encoding, Bell pair generation, teleportation execution, verification.
  * `/api/v1/threats`: Attack injection engine (forgery, impersonation, replay, quantum channel noise, rate limit abuse) and real-time observation.
  * `/api/v1/analytics`: Aggregate statistics, historical logs, error rate summaries, security health metrics.
* **Security & Auth**: OAuth2 Password Bearer with JWT tokens, bcrypt password hashing, and role checks (`USER`, `SECURITY_ANALYST`, `ADMIN`).

### 2.3 Mathematical Quantum Simulation Engine (`quantum_engine`)
* **Core Philosophy**: Pure numerical matrix mechanics implemented in Python using `NumPy`. No reliance on external quantum cloud APIs or hardware dependencies.
* **Key Components**:
  * `Qubit`: Represents complex state vectors $\alpha|0\rangle + \beta|1\rangle$ normalized to $|\alpha|^2 + |\beta|^2 = 1$.
  * `QuantumGate`: Unitary matrices ($I, X, Y, Z, H, CNOT$).
  * `BellPair`: Mathematical formulation of entangled Bell states $|\Phi^+\rangle, |\Phi^-\rangle, |\Psi^+\rangle, |\Psi^-\rangle$.
  * `Measurement`: Projective operator calculation and probability calculation.
  * `StateFidelity`: Inner product computation $F = |\langle\psi_{exp}|\psi_{obs}\rangle|^2$.

### 2.4 QDS Protocol Engine (`qds_protocol`)
* Manages the complete lifecycle of a Quantum Digital Signature transaction:
  1. Hash input message using SHA-256.
  2. Encode message bits into simulated quantum state vectors.
  3. Generate Bell pairs for Alice and Bob.
  4. Perform Alice's joint CNOT and Hadamard operations.
  5. Measure Alice's qubits to extract classical measurement bits $m_1 m_2$.
  6. Transmit classical bits along with session nonces and timestamps.
  7. Apply Bob's Pauli correction operators ($I, X, Z, XZ$).
  8. Execute projective measurement on Bob's side to reconstruct original state vectors.

### 2.5 Non-AI Statistical Threat Detection Engine (`threat_detection`)
* Operates as an independent observation layer attached to the QDS session pipeline.
* **Detection Metrics**:
  * **Quantum Bit Error Rate ($QBER$)**: Proportion of incorrect measurement outcomes relative to expected outcomes.
  * **State Mismatch Rate ($\mu$)**: Degree of inner product deviation from unity ($1 - F$).
  * **Statistical Threshold Rules**: Trigger alert if $QBER > \tau_{QBER}$ (default 0.05) or $F < \tau_{fidelity}$ (default 0.95).
  * **Protocol Audit Rules**: Nonce cache verification (anti-replay), timestamp delta check $\Delta t < T_{max}$, sender public key HMAC validation.
  * **Rate Limit Rules**: Counter of verification attempts per session ID.

### 2.6 Persistence Layer (Database)
* **ORM**: SQLAlchemy 2.0 with asynchronous driver.
* **Database**: PostgreSQL (Production) / SQLite (Local Development).
* **Entities**: Users, QDS Sessions, Qubit States, Threat Logs, System Metrics.

---

## 3. Data & Sequence Flow Diagram

```
User          Frontend (React)         Backend API (FastAPI)     QDS & Quantum Engine       Threat Engine
 │                   │                          │                         │                      │
 │── Enter Message ─►│                          │                         │                      │
 │   "Pay ₹100"      │── POST /qds/encode ────►│                         │                      │
 │                   │                          │── Create Qubit States ─►│                      │
 │                   │                          │◄─ Qubit Sequence ───────│                      │
 │                   │◄─ Session ID & Hash ─────│                         │                      │
 │                   │                          │                         │                      │
 │── Initiate        │                          │                         │                      │
 │   Teleportation ─►│── POST /qds/teleport ───►│                         │                      │
 │                   │                          │── Bell Pair & Alice H/CNOT ─►                   │
 │                   │                          │◄─ Measurement Bits (m1m2) ────                   │
 │                   │                          │                         │                      │
 │── Run Attack      │                          │                         │                      │
 │   Simulation ────►│── POST /threats/simulate►│                         │                      │
 │                   │   (Inject Forgery/Noise) │── Inject Anomaly ──────►│                      │
 │                   │                          │                         │                      │
 │── Verify          │                          │                         │                      │
 │   Signature ─────►│── POST /qds/verify ─────►│                         │                      │
 │                   │                          │── Bob Pauli Correction ─►│                      │
 │                   │                          │── Projective Measurement►│                      │
 │                   │                          │◄─ Observed Qubits ──────│                      │
 │                   │                          │                                                │
 │                   │                          │── Analyze Metrics (F, QBER, Nonce) ───────────►│
 │                   │                          │◄─ Threat Assessment (ACCEPT / REJECT + ALERT) ─│
 │                   │◄─ Verification Result ───│                                                │
 │                   │   + Threat Audit Metrics │                                                │
```

---

## 4. Security Architecture & Threat Boundary

* **Authentication Boundary**: Protected API endpoints enforce HTTP Bearer JWT tokens.
* **Role-Based Access Control (RBAC)**:
  * `USER`: Can create messages, generate QDS signatures, and execute teleportation.
  * `SECURITY_ANALYST`: Can access threat logs, run attack simulations, and view security analytics.
  * `ADMIN`: Can manage users, modify security thresholds ($\tau_{QBER}$, $\tau_{fidelity}$), and configure system parameters.
* **Anti-Replay Safeguards**:
  * Redis/In-Memory active nonce cache with TTL.
  * Strict timestamp check ensuring requests arrive within $\pm 300$ seconds.
* **Quantum Channel Boundary**:
  * Teleportation protocol enforces classical transmission of *only* measurement bits $m_1 m_2$, preventing no-cloning theorem violations.

---

## 5. Non-Functional Requirements & Performance Targets

* **Teleportation Latency**: $< 50\text{ ms}$ for simulated signature sizes up to 256 qubits.
* **Threat Engine Execution**: $< 10\text{ ms}$ evaluation overhead per signature verification.
* **Database Query Performance**: Indexed lookups on `session_id` and `nonce` under $5\text{ ms}$.
* **Frontend Responsiveness**: Smooth 60 FPS rendering of quantum circuit animations and dynamic charts.
