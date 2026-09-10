# ACTUAL IMPLEMENTATION STATUS

Based strictly on the current repository files as of the latest inspection:

- **Phase 1 (Project Setup):** Implemented (Python, FastAPI, React, Vite)
- **Phase 2 (Quantum Simulation Engine):** Implemented (`backend/app/quantum/`)
- **Phase 3 (QDS Protocol):** Implemented (`backend/app/qds/` including encoding, hashing, and teleportation)
- **Phase 4 (Deterministic Threat Detection):** Implemented (`backend/app/threats/`)
- **Phase 5 (FastAPI, JWT Auth, Database):** Implemented (`backend/app/api/`, `backend/app/db/`)
- **Phase 6 (React Frontend):** Implemented (`frontend/src/`)
- **Phase 7 (Docker & Deployment):** Implemented (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`)
- **Phase 8 (Real-Time SOC & Metrics):** Implemented (`backend/app/realtime/`, `backend/app/incidents/`, `frontend/src/pages/SecurityOperations.tsx`)
- **Phase 9 (Security Audit & Cleanup):** Implemented (Audit logs added in `backend/app/audit/`, frontend decorative UI removed, roots rerouted)

---

# PART 1 — COMPLETE PROJECT STRUCTURE

## 1. Backend (`/backend`)
### Core & DB
- **`app/main.py`**: FastAPI application entry point. Sets up CORS, exception handlers, and mounts API routers.
- **`app/core/`**: Configuration (`config.py`), database engine (`database.py`), rate limiter (`rate_limiter.py`), auth/security functions (`security.py`).
- **`app/db/models.py`**: SQLAlchemy ORM definitions (`UserModel`, `QDSSessionModel`, `VerificationResultModel`, `ThreatLogModel`, `IncidentModel`, `AuditLogModel`).
- **`app/db/schemas.py`**: Pydantic models for request validation and response serialization.

### Quantum Engine
- **`app/quantum/qubit.py`**: Defines `QubitState` (2x1 complex vector).
- **`app/quantum/gates.py`**: Defines unitary matrices (`X`, `Y`, `Z`, `H`, `CNOT`) and tensor products.
- **`app/quantum/bell_pair.py`**: Defines `BellPair` generating maximally entangled state |Φ⁺⟩.
- **`app/quantum/measurement.py`**: Projective measurement simulations and teleportation joint-measurements.
- **`app/quantum/fidelity.py`**: Complex inner-product based state fidelity calculations.

### QDS Protocol
- **`app/qds/hasher.py`**: Computes SHA-256 and converts to 256 bits.
- **`app/qds/encoder.py`**: Maps binary bits to initial `QubitState` states.
- **`app/qds/session.py`**: Tracks state of a transmission (expected qubits, reconstructed qubits, classical bits).
- **`app/qds/teleportation.py`**: The teleportation processor executing CNOT, Hadamard, measurement, and Bob's Pauli correction.

### Threat Detection
- **`app/threats/engine.py`**: `ThreatDecisionEngine` evaluating deterministic thresholds (Fidelity, QBER, Timestamps, Nonces).
- **`app/threats/metrics.py`**: `calculate_forgery_probability` and statistical deviations based on pure math.
- **`app/threats/simulator.py`**: `AttackSimulator` used for injecting noise, flipping bits, replaying nonces.

### API Services
- **`app/api/auth.py`**: Login/registration routes.
- **`app/api/qds.py`**: Signature creation, teleportation, and verification endpoints.
- **`app/api/threats.py`**: Simulation and detection endpoints.
- **`app/api/monitoring.py`**, **`app/api/incidents.py`**, **`app/api/audit.py`**: SOC and Phase 8/9 endpoints.

## 2. Frontend (`/frontend`)
- **`src/App.tsx`**: Main router. Enforces `ProtectedRoute`.
- **`src/main.tsx`**: React entry point binding to DOM.
- **`src/components/`**: Reusable UI (e.g., `Sidebar.tsx`, `Navbar.tsx`, `CircuitDiagram.tsx`).
- **`src/pages/`**: View components (e.g., `CreateSignature.tsx`, `TeleportationSim.tsx`, `SignatureVerification.tsx`, `SecurityOperations.tsx`).
- **`src/services/api.ts`**: Axios HTTP client configuration and interceptors for JWT.
- **`src/context/AuthContext.tsx`**: Manages global authentication state.

## 3. Tests (`/backend/tests`)
- **`test_api_unittest.py`**, **`test_quantum_engine_unittest.py`**, **`test_threat_engine_unittest.py`**: Unit tests verifying deterministic logic.
- **`test_e2e_unittest.py`**: End-to-end integration tests.

## 4. Docker
- **`docker-compose.yml`**: Spins up Postgres, Backend, and Frontend.

---

# PART 2 — ACTUAL TECHNOLOGY STACK

**Frontend:**
- Framework: React 18.2.0
- Language: TypeScript 5.2
- Build tool: Vite 5.1
- CSS framework: Tailwind CSS 3.4
- Routing: React Router DOM 6.22
- Charts: Recharts 2.12
- HTTP client: Axios 1.6.8
- Icons: Lucide React

**Backend:**
- Python version: 3.11 (based on Dockerfile)
- Framework: FastAPI
- Data Validation: Pydantic
- Database ORM: SQLAlchemy
- Authentication: Python-JOSE (JWT)
- Password hashing: Passlib (Bcrypt)
- Server: Uvicorn

**Quantum simulation:**
- NumPy (`np.array`, `np.kron`, matrix multiplication `@`)

**Database:**
- Type: PostgreSQL 15
- Tables: `users`, `qds_sessions`, `verification_results`, `threat_logs`, `security_events`, `incidents`, `audit_logs`

**Testing:**
- Framework: `unittest` (invoked via `pytest` or native runner).

**Deployment:**
- Docker & Docker Compose. Port 8000 (FastAPI), Port 3000 (React Nginx container), Port 5432 (Postgres).

---

# PART 3 — HOW TO RUN THE WEBSITE

### DOCKER MODE (Recommended)
1. Ensure Docker Desktop is running.
2. At the project root, run:
   ```bash
   docker-compose up --build -d
   ```
3. Backend runs at `http://localhost:8000`
4. Frontend runs at `http://localhost:3000`
5. API Docs run at `http://localhost:8000/docs`

### DEVELOPMENT MODE
**Backend Setup:**
1. `cd backend`
2. `python -m venv venv` and activate it.
3. `pip install -r requirements.txt`
4. Create `.env` or export: `DATABASE_URL=sqlite:///./qds.db` (or Postgres), `JWT_SECRET_KEY=secret`.
5. Start: `uvicorn app.main:app --reload --port 8000`

**Frontend Setup:**
1. `cd frontend`
2. `npm install`
3. Start: `npm run dev`
4. Access at `http://localhost:5173`

---

# PART 4 — COMPLETE SYSTEM ARCHITECTURE

```text
  [ Browser / User ]
         ↓
  [ React Frontend (Vite) ]  <-- AuthContext, React Router
         ↓ (Axios HTTP via JWT Bearer Token)
  [ FastAPI Backend ]        <-- Rate Limiter, Auth Dependency
         ↓
  [ API Routers (qds.py, threats.py) ]
         ↓
  [ QDS Session & Encoding (encoder.py) ]
         ↓
  [ Quantum Engine (qubit.py, teleportation.py) ]  <-- NumPy Linear Algebra
         ↓
  [ Threat Engine (engine.py) ] <-- Deterministic rules
         ↓
  [ SQLAlchemy ORM (models.py) ]
         ↓
  [ PostgreSQL Database ]
```

---

# PART 5 — USER LOGIN FLOW

1. **User enters username & password** in `Login.tsx`.
2. **React Form Submission**: Triggers `login(username, password)` in `AuthContext.tsx`.
3. **API Service**: Calls `authApi.login()` in `api.ts` (sending `application/x-www-form-urlencoded`).
4. **FastAPI Route**: Hits `@router.post("/login")` in `app/api/auth.py`.
5. **Database Lookup**: Queries `UserModel` by username.
6. **Password Verification**: `verify_password()` compares the Bcrypt hash.
7. **JWT Creation**: `create_access_token()` mints a JWT with user ID and role.
8. **Response**: Backend returns `{"access_token": "ey...", "token_type": "bearer", "user": {...}}`.
9. **Frontend Storage**: `AuthContext` saves the token to `localStorage.getItem('qds_token')`.
10. **Authenticated Requests**: Axios interceptor in `api.ts` injects `Authorization: Bearer <token>` into all subsequent headers.

---

# PART 6 — COMPLETE QDS WORKFLOW

**Example: "Pay ₹100 to Bob"**

1. **Message Entry**: User types in `CreateSignature.tsx`.
2. **Hashing**: API calls `QDSMessageHasher.hash_message()`.
3. **SHA-256 Generation**: `hashlib.sha256()` outputs 32 bytes.
4. **Bits Creation**: Converted to 256 bits (e.g., `0110...`).
5. **QubitState Encoding**: `SignatureStateEncoder.encode_bits_to_qubits()` maps `0` to |0⟩, `1` to |1⟩.
6. **Session Creation**: `QDSSession` initialized.
7. **Session ID**: Generated via `uuid.uuid4()`.
8. **Nonce Generation**: 64-char hex string created automatically.
9. **Timestamp Generation**: `time.time()` saved.
10. **Bell Pair Creation**: `TeleportationProcessor` initializes `BellPair(BellType.PHI_PLUS)` for each bit.
11. **Teleportation**: Called via `/qds/teleport`.
12. **Alice Measurement (CNOT + H)**: `simulate_alice_teleportation_measurement()` mathematically collapses state.
13. **Measurement Bits**: Yields classical string like `"01"`.
14. **Bob Correction**: `get_pauli_correction("01")` returns `X` matrix. Applied via `uncorrected_bob_state.apply_gate(X)`.
15. **Reconstructed State**: Bob obtains exactly |0⟩ or |1⟩.
16. **Fidelity**: `calculate_state_fidelity()` computes |⟨ψ | φ⟩|² (yielding `1.0` if no attack).
17. **Verification**: User clicks verify. Engine checks nonces, fidelity, QBER.
18. **Returned to Frontend**: JSON with `decision: "LEGITIMATE"`, `fidelity: 1.0`.
19. **Database Storage**: Saved to `VerificationResultModel`.

---

# PART 7 — QUANTUM ENGINE IMPLEMENTATION

- **QubitState**: Implemented in `qubit.py` as a NumPy 2x1 complex array `[[α], [β]]`.
- **Pauli Gates (X, Y, Z)**: Implemented in `gates.py` as NumPy 2x2 complex arrays.
- **Hadamard (H)**: Matrix `(1/√2) [[1, 1], [1, -1]]`.
- **CNOT**: 4x4 unitary matrix in `gates.py`.
- **Bell Pair**: Implemented in `bell_pair.py`. `BellType.PHI_PLUS` returns 4x1 vector `[1/√2, 0, 0, 1/√2]ᵀ`.
- **Measurement**: `measurement.py` uses `np.random.choice([0, 1], p=[|α|², |β|²])`.
- **Fidelity**: `fidelity.py`. Calculates `np.abs(state_a.inner_product(state_b)) ** 2`.

---

# PART 8 — TELEPORTATION IMPLEMENTATION

Located in `app/qds/teleportation.py`.
- **Order**: Signature (q0), Alice Bell (q1), Bob Bell (q2).
- **Actual Implementation**: Rather than computing a massive 8x8 Kronecker tensor product for the entire 3-qubit system which is mathematically heavy, the implementation in `measurement.py` (`simulate_alice_teleportation_measurement`) analytically models the outcome of the joint measurement and returns Bob's collapsed pre-correction state deterministically (or probabilistically).
- **Pauli Mapping**: 
  - `00` -> `I`
  - `01` -> `X`
  - `10` -> `Z`
  - `11` -> `X @ Z` (Matrix multiply)

---

# PART 9 — THREAT DETECTION IMPLEMENTATION

Implemented in `app/threats/simulator.py` and `app/threats/engine.py`.

1. **Signature Forgery**: Flips expected bit values randomly based on `tamper_ratio`. Detected by Mismatch Rate and Fidelity drops.
2. **Impersonation**: Changes `sender_id` string in the request payload. Detected by identity mismatch rule.
3. **Replay Attack**: Copies an existing `nonce` and resubmits the session. Detected by in-memory `_nonce_cache`.
4. **Channel Manipulation**: Applies random Pauli gates (X, Z) to signature qubits simulating noise. Detected by elevated QBER.
5. **Unauthorized Verification**: Submits verification > 3 times. Detected by `verification_attempts` counter limit.

---

# PART 10 — SECURITY METRICS

Implemented in `app/threats/metrics.py` and `app/quantum/fidelity.py`.

- **State Fidelity**: |⟨ψ_exp | ψ_rec⟩|². Ideal = 1.0. Minimum allowed: 0.95.
- **QBER**: (Mismatches / Total Bits) * 100. Maximum allowed: 5.0%.
- **Mismatch Rate**: `1.0 - mean_fidelity`. Maximum allowed: 0.05.
- **Statistical Deviation**: `(Mismatched Bits / Total Bits)`. Range `[0, 1]`.
- **Forgery Probability**: Weighted penalty score: `0.40(Fidelity) + 0.35(QBER) + 0.15(Mismatch) + 0.10(Deviation)`.

---

# PART 11 — THREAT DECISION ENGINE

Trace from `app/threats/engine.py`:
1. Check `session.nonce` in `self._nonce_cache`. (Triggers `REPLAY_ATTACK` -> CRITICAL).
2. Check `session_age_sec > 300.0`. (Triggers `REPLAY_ATTACK` -> HIGH).
3. Check `session.sender_id != authorized_sender_id`. (Triggers `IMPERSONATION` -> CRITICAL).
4. Check `verification_attempt_count > 3`. (Triggers `UNAUTHORIZED` -> MEDIUM).
5. Check `mean_fidelity < 0.95`. (Triggers `FORGERY` -> CRITICAL).
6. Check `qber_percent > 5.0`. (Triggers `CHANNEL_MANIPULATION` -> HIGH).

**Decision Math:**
- If ANY CRITICAL alert exists -> `MALICIOUS` (REJECT)
- Else if ANY HIGH/MEDIUM alert exists -> `SUSPICIOUS` (REJECT)
- Else -> `LEGITIMATE` (ACCEPT)

---

# PART 12 — DATABASE

**Tables in `models.py`:**
- `users`: Core identity. (Cols: id, username, email, password_hash, role)
- `qds_sessions`: Track QDS workflow. (Cols: id, session_id, user_id (FK), message_hash, nonce, status).
- `verification_results`: Metrics. (Cols: qds_session_id (FK), fidelity, qber, decision).
- `threat_logs`: Audit trails for attacks. (Cols: qds_session_id (FK), attack_type, severity, decision).
- `security_events`: Phase 8 websocket logging.
- `incidents`: Phase 8 SOC incident tickets.
- `audit_logs`: Phase 9 compliance auditing.

---

# PART 13 — API DOCUMENTATION

| METHOD | ENDPOINT | AUTH REQUIRED | ROLE | INPUT | OUTPUT | PURPOSE |
|--------|----------|---------------|------|-------|--------|---------|
| POST | `/auth/login` | No | ALL | OAuth Form | `{access_token, user}` | Auth |
| POST | `/qds/create-signature` | Yes | ALL | `{message}` | `QDSSessionResponse` | Hash & Encode |
| POST | `/qds/teleport` | Yes | ALL | `{session_id}` | `{classical_bits...}` | Run CNOT/H |
| POST | `/qds/verify` | Yes | ALL | `{session_id}` | `ThreatDetectionResponse` | Run Threat Engine |
| POST | `/threats/simulate` | Yes | ALL | `{session_id, attack_type}` | `{injected_threat}` | Inject Attack |

---

# PART 14 — FRONTEND ARCHITECTURE

- **Routing**: Handled by `App.tsx` using `react-router-dom`. `ProtectedRoute` guards authenticated routes.
- **Layout**: `AppLayout` contains the `Sidebar` and `Navbar`.
- **Navigation Flow**:
  1. `CreateSignature.tsx` -> Calls `/qds/create-signature`. Routes to `/teleportation`.
  2. `TeleportationSim.tsx` -> Calls `/qds/teleport`. Routes to `/verification`.
  3. `SignatureVerification.tsx` -> Calls `/qds/verify`. Shows metrics.

**DOCUMENTATION vs IMPLEMENTATION DIFFERENCE**:
The traditional "Dashboard" page (`Dashboard.tsx`) was completely removed in Phase 9 to strip away marketing UI. The root route `/` now actively redirects to `/create-signature` to enforce a strict QDS functional workflow.

---

# PART 15 — DASHBOARD

*DOCUMENTATION vs IMPLEMENTATION DIFFERENCE:*
As noted above, `Dashboard.tsx` does not exist. However, `SecurityOperations.tsx` (SOC) acts as the operational dashboard.
**Flow:**
1. User opens `/soc`.
2. React mounts `LiveMetricsPanel`.
3. `useEffect` polls `monitoringApi.getMetrics()`.
4. FastAPI hits `/monitoring/metrics`.
5. DB queries counts from `VerificationResultModel` and `IncidentModel`.
6. React state updates `setMetrics()`.
7. `LiveMetricsPanel` explicitly renders true metrics.

---

# PART 16 — ATTACK SIMULATOR UI

1. User opens `AttackSimulator.tsx`.
2. Selects "Replay Attack", clicks Submit.
3. React calls `threatsApi.simulateAttack()`.
4. FastAPI `/threats/simulate` endpoint is hit.
5. `AttackSimulator.inject_replay_attack(session)` is called, extracting an old nonce.
6. User clicks "Verify Security".
7. Hits `/qds/verify`.
8. `ThreatDecisionEngine` sees the nonce in `_nonce_cache`.
9. Appends CRITICAL alert. Returns `MALICIOUS`.
10. Frontend renders red `ThreatAlert` banner.

---

# PART 17 — COMPLETE END-TO-END EXAMPLE

**Normal Flow:**
Alice -> "Pay ₹100" -> Hashed to `0110...` -> Qubits Encoded -> Bell Pairs Generated -> Teleported via CNOT/H -> Classical bits sent -> Bob applies Pauli -> Bob reconstructs state -> Fidelity = 1.0 -> Verification Engine sees Fidelity > 0.95 -> Database logs LEGITIMATE -> UI shows "Secure".

**Attack Flow (Signature Forgery):**
Attacker hits `/threats/simulate` with `FORGERY` -> `AttackSimulator` applies Pauli X to 15% of qubits -> Qubits flipped -> Alice clicks Verify -> Bob reconstructs state -> Fidelity drops to 0.75 (below 0.95 threshold) -> Threat Engine sees low fidelity -> Database logs MALICIOUS -> UI shows "Signature Forgery Detected".

---

# PART 18 — TESTING

Found in `/backend/tests`.
- `test_quantum_engine_unittest.py`: Tests `qubit.py` normalization, Gate unitary validation, and Bell pair generations.
- `test_threat_engine_unittest.py`: Ensures `ThreatDecisionEngine` correctly flags Replay, Forgery, and limits.
- `test_api_unittest.py`: Tests `/qds/create-signature` and Auth endpoints.
- `test_e2e_unittest.py`: Tests the full pipeline from create -> teleport -> simulate -> verify.

---

# PART 19 — DOCKER

**docker-compose.yml:**
- **postgres**: Uses `postgres:15-alpine`. Volumes mapped to persist data. Healthcheck configured.
- **backend**: Uses `backend/Dockerfile`. Exposes `8000`. Environment vars passed (DB URL, JWT Secret). Connects to Postgres via `qds_network`.
- **frontend**: Uses `frontend/Dockerfile`. Multi-stage build (Node builder -> Nginx serving static files). Exposes `3000`. Depends on `backend`.

```text
Browser -> [Nginx :3000] -> [FastAPI :8000] -> [PostgreSQL :5432]
```

---

# PART 20 — CURRENT PROJECT LIMITATIONS

A. **Implementation Limitations:** The quantum operations are simulated sequentially on classical hardware using NumPy. Exponential state space of full 256 entangled qubits is avoided by treating them as 256 separate 2-qubit systems.
B. **Security Limitations:** JWT secret key and DB passwords are hardcoded in env fallbacks.
C. **Quantum Limitations:** Emulates perfect coherence. Realistic decoherence models are not deeply simulated beyond raw bit-flip injection.

---

# PART 21 — IMPORTANT "WHAT TO SAY IN VIVA"

1. **What is this project?** A quantum-inspired digital signature framework ensuring cryptographic non-repudiation using simulated quantum teleportation.
2. **Why quantum-inspired?** Classical signatures (RSA/ECC) are vulnerable to Shor's Algorithm on future quantum computers. This explores post-quantum paradigms.
3. **What is teleportation?** Transferring quantum information without moving the physical particle using Bell pair entanglement and classical channels.
4. **Why Bell states?** They provide maximum entanglement, enabling the correlation required for teleportation.
5. **What is Fidelity?** A mathematical measure of how identical two quantum states are. 1.0 means perfectly identical.
6. **Why no AI/ML?** Security requires determinism. AI hallucination or statistical false-positives are unacceptable in cryptography.
7. **What is simulated?** The quantum states (represented as 2D complex vectors) and unitary operations (matrix multiplication).
8. **Why FastAPI & React?** FastAPI provides ultra-fast async Python APIs ideal for NumPy. React offers a modular, state-driven UI.

---

# PART 22 — FILE-TO-FLOW MAPPING

| SYSTEM STEP | ACTUAL FILE | ACTUAL FUNCTION/CLASS | NEXT COMPONENT |
|-------------|-------------|-----------------------|----------------|
| Hash Message | `app/qds/hasher.py` | `MessageHasher.hash_message()` | Encoder |
| Encode Qubits | `app/qds/encoder.py` | `SignatureStateEncoder.encode_bits_to_qubits()` | Session |
| Teleportation | `app/qds/teleportation.py` | `TeleportationProcessor.teleport_single_qubit()` | Threat Engine |
| Fidelity Check | `app/quantum/fidelity.py` | `calculate_sequence_fidelity()` | Threat Engine |
| Decision Engine | `app/threats/engine.py` | `ThreatDecisionEngine.evaluate_session()` | API Response |

---

# FINAL PROJECT FLOW

**HOW THE WEBSITE WORKS FROM USER CLICK TO DATABASE:**
1. **User Action:** Clicks "Generate Signature" on React UI.
2. **Axios Client:** Sends POST request with JWT token to FastAPI.
3. **FastAPI Route (`qds.py`):** Receives request, hashes message via `hasher.py`.
4. **Quantum Engine:** Encodes hash into `QubitState` vectors.
5. **Database (`models.py`):** Saves session metadata to PostgreSQL via SQLAlchemy.
6. **Teleportation:** User clicks "Transmit". `teleportation.py` mathematically simulates CNOT, Hadamard, and Pauli corrections using NumPy matrices.
7. **Threat Audit:** User clicks "Verify". `engine.py` checks nonces, computes fidelity, and deterministically scores the transaction.
8. **Logging:** Threat telemetry stored in `ThreatLogModel`.
9. **UI Update:** React receives decision JSON and renders Pass/Fail badges.
