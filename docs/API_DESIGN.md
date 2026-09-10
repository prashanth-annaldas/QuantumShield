# REST API Design Specification

**Project Title**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (QDS-Framework)  
**Document Version**: 1.0.0  
**Phase**: Phase 1 — Planning & Specification  

---

## 1. Overview & API Standards

The backend REST API is built with **FastAPI** adhering to OpenAPI 3.0 standards.
* **Base URL**: `/api/v1`
* **Data Format**: JSON (`application/json`)
* **Authentication**: HTTP Bearer Token (`Authorization: Bearer <JWT_TOKEN>`)
* **Response Envelope Structure**:
  ```json
  {
    "success": true,
    "data": { ... },
    "error": null,
    "timestamp": "2026-09-09T00:45:00Z"
  }
  ```

---

## 2. Authentication & Authorization Endpoints (`/api/v1/auth`)

### 2.1 User Login
* **Endpoint**: `POST /api/v1/auth/login`
* **Description**: Authenticates user and returns JWT access token with role information.
* **Request Body**:
  ```json
  {
    "username": "analyst_bob",
    "password": "SecurePassword123!"
  }
  ```
* **Response Body (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "user": {
        "id": "usr-101",
        "username": "analyst_bob",
        "email": "bob@qds-security.org",
        "role": "SECURITY_ANALYST"
      }
    }
  }
  ```

### 2.2 User Registration
* **Endpoint**: `POST /api/v1/auth/register`
* **Request Body**:
  ```json
  {
    "username": "alice_user",
    "email": "alice@qds-security.org",
    "password": "SecurePassword123!",
    "role": "USER"
  }
  ```

---

## 3. Quantum & QDS Signature Endpoints (`/api/v1/qds`)

### 3.1 Encode Message & Generate QDS States
* **Endpoint**: `POST /api/v1/qds/encode`
* **Description**: Hashes input message using SHA-256 and generates initial qubit states.
* **Request Body**:
  ```json
  {
    "message": "Pay ₹100 to Bob",
    "sender_id": "usr-101"
  }
  ```
* **Response Body (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "session_id": "qds-sess-9021",
      "message": "Pay ₹100 to Bob",
      "message_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
      "nonce": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "qubit_count": 256,
      "qubit_states_sample": [
        {"index": 0, "bit": 1, "alpha": [0.0, 0.0], "beta": [1.0, 0.0]},
        {"index": 1, "bit": 0, "alpha": [1.0, 0.0], "beta": [0.0, 0.0]}
      ],
      "created_at": 1788828300000
    }
  }
  ```

### 3.2 Execute Teleportation Simulation
* **Endpoint**: `POST /api/v1/qds/teleport`
* **Description**: Generates Bell pairs, executes Alice's joint CNOT/Hadamard operations, and extracts classical measurement bits $m_1 m_2$.
* **Request Body**:
  ```json
  {
    "session_id": "qds-sess-9021"
  }
  ```
* **Response Body (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "session_id": "qds-sess-9021",
      "teleportation_status": "COMPLETED",
      "classical_measurement_bits": ["00", "11", "01", "10"],
      "bell_pair_count": 256,
      "transmission_timestamp": 1788828302000
    }
  }
  ```

### 3.3 Verify Signature State
* **Endpoint**: `POST /api/v1/qds/verify`
* **Description**: Applies Bob's Pauli corrections ($I, X, Z, XZ$), performs projective measurement, and computes state fidelity and QBER.
* **Request Body**:
  ```json
  {
    "session_id": "qds-sess-9021"
  }
  ```
* **Response Body (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "session_id": "qds-sess-9021",
      "decision": "LEGITIMATE",
      "action": "ACCEPT",
      "state_fidelity": 1.0,
      "qber_percent": 0.0,
      "mismatch_rate": 0.0,
      "nonce_valid": true,
      "time_delta_seconds": 2.0,
      "attempt_count": 1,
      "threat_alerts": []
    }
  }
  ```

---

## 4. Threat Simulation & Analytics Endpoints (`/api/v1/threats`)

### 4.1 Inject Threat Simulation
* **Endpoint**: `POST /api/v1/threats/simulate`
* **Description**: Simulates active cyber attacks on a QDS session.
* **Request Body**:
  ```json
  {
    "session_id": "qds-sess-9021",
    "threat_type": "SIGNATURE_FORGERY",
    "parameters": {
      "tamper_bit_indices": [0, 4, 12, 19],
      "noise_level": 0.15
    }
  }
  ```
* **Response Body (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "simulation_id": "sim-4091",
      "session_id": "qds-sess-9021",
      "injected_threat": "SIGNATURE_FORGERY",
      "status": "INJECTED",
      "message": "Signature bits tampered at 4 index locations."
    }
  }
  ```

### 4.2 Fetch Threat Detection Logs
* **Endpoint**: `GET /api/v1/threats/logs`
* **Query Parameters**:
  * `threat_type`: Optional string filter (`FORGERY`, `REPLAY`, `CHANNEL_NOISE`, etc.)
  * `decision`: Optional filter (`LEGITIMATE`, `MALICIOUS`, `SUSPICIOUS`)
  * `limit`: Integer (default 50)
* **Response Body (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "logs": [
        {
          "log_id": "log-89f4b12c",
          "session_id": "qds-sess-9021",
          "threat_type": "SIGNATURE_FORGERY",
          "decision": "MALICIOUS",
          "qber_percent": 18.75,
          "state_fidelity": 0.8125,
          "timestamp": "2026-09-09T00:45:00Z"
        }
      ],
      "total_count": 1
    }
  }
  ```

### 4.3 System Security Analytics Summary
* **Endpoint**: `GET /api/v1/analytics/dashboard`
* **Response Body (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "total_sessions": 1420,
      "legitimate_sessions": 1310,
      "malicious_sessions": 110,
      "threat_breakdown": {
        "SIGNATURE_FORGERY": 45,
        "IMPERSONATION_ATTACK": 20,
        "REPLAY_ATTACK": 30,
        "QUANTUM_CHANNEL_MANIPULATION": 10,
        "UNAUTHORIZED_VERIFICATION": 5
      },
      "average_qber_percent": 1.42,
      "average_state_fidelity": 0.985,
      "system_health_status": "OPTIMAL"
    }
  }
  ```
