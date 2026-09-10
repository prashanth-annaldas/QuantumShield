# Database Design & Schema Specification

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. Database Architecture & Technology Stack

* **ORM Framework**: SQLAlchemy 2.0 (Declarative Mapping with AsyncIO).
* **Database Management System**:
  * **Production**: PostgreSQL 15+
  * **Development / Testing**: SQLite (In-Memory or File-backed) / PostgreSQL via Docker.
* **Migration Strategy**: Alembic schema migrations.

---

## 2. Entity Relationship Diagram (ERD)

```
┌──────────────────────────┐               ┌──────────────────────────┐
│          users           │               │       qds_sessions       │
├──────────────────────────┤               ├──────────────────────────┤
│ id (PK)                  │1             *│ id (PK)                  │
│ username                 ├───────────────┤ session_id (UNIQUE)      │
│ email                    │               │ sender_id (FK -> users)  │
│ password_hash            │               │ message                  │
│ role (ENUM)              │               │ message_hash             │
│ created_at               │               │ nonce (INDEX)            │
└──────────────────────────┘               │ status (ENUM)            │
                                           │ timestamp                │
                                           └────────────┬─────────────┘
                                                        │1
                                                        │
                                    ┌───────────────────┴───────────────────┐
                                   *│                                       │*
                      ┌─────────────┴────────────┐             ┌────────────┴─────────────┐
                      │      qubit_states        │             │       threat_logs        │
                      ├──────────────────────────┤             ├──────────────────────────┤
                      │ id (PK)                  │             │ id (PK)                  │
                      │ session_id (FK)          │             │ session_id (FK)          │
                      │ qubit_index              │             │ threat_type (ENUM)       │
                      │ expected_alpha           │             │ decision (ENUM)          │
                      │ expected_beta            │             │ qber_percent             │
                      │ classical_bits           │             │ state_fidelity           │
                      │ reconstructed_alpha      │             │ mismatch_rate            │
                      │ reconstructed_beta       │             │ details_json             │
                      │ fidelity                 │             │ created_at               │
                      └──────────────────────────┘             └──────────────────────────┘
```

---

## 3. Detailed Table Schemas

### 3.1 `users` Table
Stores authenticated user and analyst credentials with Role-Based Access Control (RBAC).

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique user ID (UUIDv4) |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | User identifier |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | User contact email |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `role` | VARCHAR(20) | NOT NULL | ENUM: `USER`, `SECURITY_ANALYST`, `ADMIN` |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | User creation timestamp |

---

### 3.2 `qds_sessions` Table
Tracks signature creation, message hash, anti-replay nonces, and teleportation status.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Internal table primary key |
| `session_id` | VARCHAR(64) | UNIQUE, INDEX, NOT NULL | Protocol Session Identifier |
| `sender_id` | VARCHAR(36) | FOREIGN KEY (`users.id`) | ID of user creating signature |
| `message` | TEXT | NOT NULL | Plaintext user message |
| `message_hash` | VARCHAR(64) | NOT NULL | SHA-256 hex digest of message |
| `nonce` | VARCHAR(64) | INDEX, NOT NULL | 128-bit anti-replay random hex |
| `status` | VARCHAR(20) | NOT NULL | ENUM: `PENDING`, `TELEPORTED`, `VERIFIED`, `REJECTED` |
| `verification_attempts`| INTEGER | DEFAULT 0 | Counter for verification rate limiting |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Session initialization timestamp |

---

### 3.3 `qubit_states` Table
Stores simulated quantum state vectors ($\alpha, \beta$), classical teleportation bits ($m_1 m_2$), and reconstructed states.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | PRIMARY KEY, AUTO_INCREMENT | Unique row ID |
| `session_id` | VARCHAR(64) | FOREIGN KEY (`qds_sessions.session_id`) | Associated session ID |
| `qubit_index` | INTEGER | NOT NULL | Bit position (0 to N-1) |
| `expected_alpha_real` | DOUBLE PRECISION | NOT NULL | Real component of original $\alpha$ |
| `expected_alpha_imag` | DOUBLE PRECISION | NOT NULL | Imaginary component of original $\alpha$ |
| `expected_beta_real` | DOUBLE PRECISION | NOT NULL | Real component of original $\beta$ |
| `expected_beta_imag` | DOUBLE PRECISION | NOT NULL | Imaginary component of original $\beta$ |
| `classical_bits` | VARCHAR(2) | NOT NULL | Measurement bits $m_1 m_2 \in \{00, 01, 10, 11\}$ |
| `reconstructed_alpha_real` | DOUBLE PRECISION | NOT NULL | Reconstructed $\alpha$ real |
| `reconstructed_alpha_imag` | DOUBLE PRECISION | NOT NULL | Reconstructed $\alpha$ imag |
| `reconstructed_beta_real` | DOUBLE PRECISION | NOT NULL | Reconstructed $\beta$ real |
| `reconstructed_beta_imag` | DOUBLE PRECISION | NOT NULL | Reconstructed $\beta$ imag |
| `fidelity` | DOUBLE PRECISION | NOT NULL | State inner product fidelity $F_k$ |

---

### 3.4 `threat_logs` Table
Audit trail logging all security evaluations, anomaly scores, and decisions.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique log ID |
| `session_id` | VARCHAR(64) | FOREIGN KEY (`qds_sessions.session_id`) | Associated session ID |
| `threat_type` | VARCHAR(32) | NOT NULL | ENUM: `NONE`, `FORGERY`, `IMPERSONATION`, `REPLAY`, `CHANNEL_NOISE`, `UNAUTHORIZED` |
| `decision` | VARCHAR(16) | NOT NULL | ENUM: `LEGITIMATE`, `SUSPICIOUS`, `MALICIOUS` |
| `qber_percent` | DOUBLE PRECISION | NOT NULL | Quantum bit error rate percentage |
| `state_fidelity` | DOUBLE PRECISION | NOT NULL | Mean state fidelity $\bar{F}$ |
| `mismatch_rate` | DOUBLE PRECISION | NOT NULL | Mismatch rate $\mu$ |
| `details_json` | JSON / TEXT | NOT NULL | Structured metrics, alerts, and parameters |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit log creation timestamp |

---

## 4. Indexing & Security Constraints

1. **Anti-Replay Nonce Index**: `CREATE UNIQUE INDEX idx_qds_nonce ON qds_sessions(nonce);` ensures instant $O(1)$ lookup for duplicate nonces.
2. **Session Lookup Index**: `CREATE INDEX idx_qds_session ON qds_sessions(session_id);`
3. **Threat Logs Time Index**: `CREATE INDEX idx_threat_logs_time ON threat_logs(created_at DESC);` for fast dashboard history pagination.
