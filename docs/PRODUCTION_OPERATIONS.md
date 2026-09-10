# Production Operations Runbook & Disaster Recovery Protocol
**Project**: Quantum-Inspired Cyber Threat Detection for Digital Signature Security (`QDS-Framework`)  
**Phase**: 9 — Enterprise Resilience, Security Audit & Production Reliability

---

## 1. System Architecture & Topology

The QDS-Framework comprises:
- **FastAPI Core Application**: Asynchronous REST backend running under Uvicorn/Gunicorn.
- **Quantum Simulation Subsystem**: Strict mathematical linear algebra (NumPy) operating on 256-qubit quantum state vectors.
- **Deterministic Threat Decision Engine**: Rule-based detection computing State Fidelity, QBER, Mismatch Rate, and Forgery Probability without probabilistic AI models.
- **Security Audit Logger**: Structured JSON logging and relational audit event persistence with automated secret redaction.
- **Real-Time SOC Gateway**: WebSocket broadcast hub with incident correlation.
- **React + Vite Frontend**: Pure TypeScript/Tailwind SPA with RBAC-gated dashboard views.

---

## 2. Environment Configuration

Production configurations must be loaded via environment variables or secure secret managers (e.g. AWS Secrets Manager, Vault):

| Variable | Recommended Production Value | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Disables `/docs`, `/redoc`, and debug logs |
| `DEBUG` | `false` | Prevents detailed traceback outputs |
| `SECRET_KEY` | *High-entropy 256-bit string* | Used for HMAC-SHA256 JWT signature verification |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/qds_db` | Production PostgreSQL connection string |
| `CORS_ORIGINS` | `["https://soc.company.com"]` | Explicitly allowed origins |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | `20` | Brute-force mitigation threshold |
| `RATE_LIMIT_VERIFY_PER_MINUTE` | `60` | QDS verification rate limit |
| `RATE_LIMIT_THREAT_PER_MINUTE` | `30` | Threat simulation throttle |

---

## 3. Database Migration Procedures

### Applying Migrations
Alembic manages all schema revisions:
```bash
# Upgrade database to latest revision
cd backend
alembic upgrade head

# Verify current revision
alembic current
```

### Rollback Migration
```bash
# Rollback single revision
alembic downgrade -1
```

---

## 4. Backup & Disaster Recovery

### Automated Logical Backup (`pg_dump`)
Run scheduled logical backups via cron or container sidecars:
```bash
# Export compressed PostgreSQL database dump
pg_dump -U postgres -h db -Fc -d qds_db -f /backups/qds_db_$(date +%Y%m%d_%H%M%S).dump
```

### Restoration Protocol
In the event of database failure or corrupted state:
```bash
# 1. Terminate active application connections
docker compose stop backend

# 2. Re-create clean target database
dropdb -U postgres -h db qds_db --if-exists
createdb -U postgres -h db qds_db

# 3. Restore from verified dump
pg_restore -U postgres -h db -d qds_db -v /backups/qds_db_LATEST.dump

# 4. Run Alembic schema check
alembic upgrade head

# 5. Restart application
docker compose start backend
```

---

## 5. System Health & Readiness Verification

### Automated Health Probes
- **Liveness Probe**: `GET /health` (Returns HTTP 200 `{"status": "healthy"}`)
- **Readiness Probe**: `GET /api/v1/system/readiness`
  - Subsystems checked: Database, Quantum Simulation Engine, Threat Engine, WebSocket Manager.
  - Return states: `READY` (all healthy), `DEGRADED` (minor degradation), `NOT_READY` (critical dependency down).
  - Guarantees zero credentials or stack traces in response payload.

### Performance & Latency Telemetry
- **Endpoint**: `GET /api/v1/monitoring/performance` (Requires `SECURITY_ANALYST` or `ADMIN`)
  - Provides bounded p50, p95, and p99 request latency percentiles.
  - Monitors authentication failure spikes and rate-limit violations.

---

## 6. Incident Escalation & Response Flowchart

```text
[ Threat / Security Event Detected ]
                │
                ▼
[ Deterministic Correlation Engine ]
                │
         ┌──────┴──────┐
         ▼             ▼
   [ Severity < HIGH ]  [ Severity >= HIGH (CRITICAL) ]
         │             │
         ▼             ▼
  [ Record Audit Log ]  [ Auto-Create Incident (e.g. INC-FORGERY) ]
                       │
                       ▼
               [ WebSocket SOC Alert ]
                       │
                       ▼
            [ Security Analyst Triage ]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
  [ Revoke Session Nonce ]    [ Rotate Sender Qubit Keys ]
```

---

## 7. Security Hardening Checklist

- [x] ContextVar-based Request ID propagation (`X-Request-ID`) on all responses.
- [x] Mandatory Security Headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
- [x] In-memory idempotency cache on signature generation & threat injection (`Idempotency-Key` header).
- [x] Non-leaking global error handlers returning structured domain error codes.
- [x] Strict non-AI deterministic threat analysis.
- [x] Recursive redaction of sensitive credentials (`password`, `token`, `secret`, `jwt`) from all audit logs.
