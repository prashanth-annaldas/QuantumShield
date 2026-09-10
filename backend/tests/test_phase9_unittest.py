"""
Phase 9 Unit Test Suite: Enterprise Resilience, Security Audit, CI/CD & Production Reliability.
Canonical test runner: python -m unittest discover -s backend/tests -p "*_unittest.py"
No pytest dependencies. Pure Python standard library unittest.
"""
import os
import sys
import json
import time
import uuid
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.core.request_context import (
    request_id_ctx,
    actor_user_id_ctx,
    actor_role_ctx,
    get_request_id,
    get_actor_user_id,
    get_actor_role,
)
from app.core.idempotency import idempotency_manager, IdempotencyManager
from app.core.exceptions import (
    QDSBaseException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    RateLimitError,
    IdempotencyConflictError,
)
from app.audit.logger import sanitize_audit_metadata
from app.audit.service import record_audit_event, get_audit_logs
from app.monitoring.metrics import metrics_collector, MetricsCollector
from app.db.models import UserModel, AuditLogModel, QDSSessionModel


class TestPhase9EnterpriseSuite(unittest.TestCase):
    """37 Comprehensive tests for Phase 9 Enterprise Resilience & Reliability."""

    @classmethod
    def setUpClass(cls):
        # Create an isolated in-memory test database
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Seed test users
        cls.db = cls.TestingSessionLocal()
        cls.admin_user = UserModel(
            id="usr-p9-admin",
            username="p9_admin",
            email="p9_admin@qds.local",
            password_hash=get_password_hash("AdminPass123!"),
            role="ADMIN",
            is_active=True,
        )
        cls.analyst_user = UserModel(
            id="usr-p9-analyst",
            username="p9_analyst",
            email="p9_analyst@qds.local",
            password_hash=get_password_hash("AnalystPass123!"),
            role="SECURITY_ANALYST",
            is_active=True,
        )
        cls.regular_user = UserModel(
            id="usr-p9-user",
            username="p9_user",
            email="p9_user@qds.local",
            password_hash=get_password_hash("UserPass123!"),
            role="USER",
            is_active=True,
        )
        cls.db.add_all([cls.admin_user, cls.analyst_user, cls.regular_user])
        cls.db.commit()

        # Generate tokens
        cls.admin_token = create_access_token({"sub": cls.admin_user.username, "user_id": cls.admin_user.id, "role": cls.admin_user.role})
        cls.analyst_token = create_access_token({"sub": cls.analyst_user.username, "user_id": cls.analyst_user.id, "role": cls.analyst_user.role})
        cls.user_token = create_access_token({"sub": cls.regular_user.username, "user_id": cls.regular_user.id, "role": cls.regular_user.role})

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        app.dependency_overrides.clear()

    def setUp(self):
        idempotency_manager.reset()
        metrics_collector.reset()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Request Context & Correlation ID (Tests 1-4)
    # ─────────────────────────────────────────────────────────────────────────

    def test_01_request_id_middleware_generates_uuid(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        req_id = resp.headers.get("X-Request-ID")
        self.assertIsNotNone(req_id)
        self.assertTrue(req_id.startswith("req-") or len(req_id) >= 12)

    def test_02_request_id_middleware_preserves_inbound_header(self):
        custom_id = "req-client-custom-trace-1234"
        resp = self.client.get("/health", headers={"X-Request-ID": custom_id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Request-ID"), custom_id)

    def test_03_request_id_sanitizes_malicious_characters(self):
        malicious_id = "req-bad<script>alert(1)</script>;DROP TABLE"
        resp = self.client.get("/health", headers={"X-Request-ID": malicious_id})
        self.assertEqual(resp.status_code, 200)
        returned_id = resp.headers.get("X-Request-ID")
        self.assertNotIn("<script>", returned_id)
        self.assertNotIn(";", returned_id)

    def test_04_request_context_variables_isolation(self):
        token = request_id_ctx.set("req-test-ctx-1")
        self.assertEqual(get_request_id(), "req-test-ctx-1")
        request_id_ctx.reset(token)

        token_user = actor_user_id_ctx.set("usr-actor-test")
        token_role = actor_role_ctx.set("ADMIN")
        self.assertEqual(get_actor_user_id(), "usr-actor-test")
        self.assertEqual(get_actor_role(), "ADMIN")
        actor_user_id_ctx.reset(token_user)
        actor_role_ctx.reset(token_role)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Security Headers (Tests 5-9)
    # ─────────────────────────────────────────────────────────────────────────

    def test_05_security_headers_middleware_nosniff(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")

    def test_06_security_headers_middleware_xframe_options(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")

    def test_07_security_headers_middleware_referrer_policy(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_08_security_headers_middleware_xss_protection(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.headers.get("X-XSS-Protection"), "1; mode=block")

    def test_09_security_headers_middleware_hsts(self):
        resp = self.client.get("/health")
        hsts = resp.headers.get("Strict-Transport-Security")
        self.assertIsNotNone(hsts)
        self.assertIn("max-age=31536000", hsts)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Idempotency Manager & Header Validation (Tests 10-15)
    # ─────────────────────────────────────────────────────────────────────────

    def test_10_idempotency_manager_stores_and_returns_cached_response(self):
        key = "idem-test-key-10"
        payload = {"message": "Test Quantum Message"}
        resp_data = {"status": "SUCCESS", "data": 42}

        idempotency_manager.set(key, payload, resp_data, status_code=200)
        cached = idempotency_manager.get(key, payload)
        self.assertEqual(cached, resp_data)

    def test_11_idempotency_manager_detects_payload_hash_conflict(self):
        key = "idem-conflict-key"
        payload_1 = {"message": "Original Message"}
        payload_2 = {"message": "Tampered Message"}

        idempotency_manager.set(key, payload_1, {"result": "ok"})
        with self.assertRaises(Exception) as ctx:
            idempotency_manager.get(key, payload_2)
        self.assertTrue("409" in str(ctx.exception) or "Conflict" in str(ctx.exception))

    def test_12_idempotency_manager_handles_expiration_ttl(self):
        mgr = IdempotencyManager(default_ttl_seconds=1)
        mgr.set("key-exp", {"a": 1}, {"data": "cached"}, ttl_seconds=1)
        # Verify valid immediately
        self.assertIsNotNone(mgr.get("key-exp", {"a": 1}))
        # Wait for expiration
        time.sleep(1.1)
        self.assertIsNone(mgr.get("key-exp", {"a": 1}))

    def test_13_idempotency_key_header_create_signature(self):
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Idempotency-Key": "idem-create-sig-999",
        }
        payload = {"message": "Deterministic Message 1"}

        resp1 = self.client.post("/api/v1/qds/create-signature", json=payload, headers=headers)
        self.assertEqual(resp1.status_code, 201)
        sess_id = resp1.json()["session_id"]

        # Re-send same request with same Idempotency-Key
        resp2 = self.client.post("/api/v1/qds/create-signature", json=payload, headers=headers)
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp2.json()["session_id"], sess_id)

    def test_14_idempotency_key_header_verify_signature(self):
        # Create session
        create_resp = self.client.post(
            "/api/v1/qds/create-signature",
            json={"message": "Verification Idempotency Test"},
            headers={"Authorization": f"Bearer {self.user_token}"},
        )
        session_id = create_resp.json()["session_id"]

        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Idempotency-Key": "idem-verify-sig-888",
        }
        payload = {"session_id": session_id}

        resp1 = self.client.post("/api/v1/qds/verify", json=payload, headers=headers)
        self.assertEqual(resp1.status_code, 200)

        # Re-send
        resp2 = self.client.post("/api/v1/qds/verify", json=payload, headers=headers)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["data"]["decision"], resp1.json()["data"]["decision"])

    def test_15_idempotency_key_header_simulate_threat(self):
        create_resp = self.client.post(
            "/api/v1/qds/create-signature",
            json={"message": "Threat Sim Idempotency Test"},
            headers={"Authorization": f"Bearer {self.user_token}"},
        )
        session_id = create_resp.json()["session_id"]

        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Idempotency-Key": "idem-threat-sim-777",
        }
        payload = {"session_id": session_id, "attack_type": "FORGERY", "tamper_ratio": 0.2}

        resp1 = self.client.post("/api/v1/threats/simulate", json=payload, headers=headers)
        self.assertEqual(resp1.status_code, 200)

        resp2 = self.client.post("/api/v1/threats/simulate", json=payload, headers=headers)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["data"]["injected_threat"], "FORGERY")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Security Audit Logging & Sanitization (Tests 16-20)
    # ─────────────────────────────────────────────────────────────────────────

    def test_16_audit_metadata_sanitization_removes_passwords(self):
        raw = {"username": "alice", "password": "superSecretPassword123!", "pass": "abc"}
        sanitized = sanitize_audit_metadata(raw)
        self.assertEqual(sanitized["password"], "[REDACTED]")
        self.assertEqual(sanitized["pass"], "[REDACTED]")
        self.assertEqual(sanitized["username"], "alice")

    def test_17_audit_metadata_sanitization_removes_tokens_and_secrets(self):
        raw = {
            "jwt": "eyJhbGciOi...",
            "access_token": "bearer-token-123",
            "api_key": "qds_live_key_999",
            "secret_key": "raw_symmetric_secret",
            "safe_metric": 99.4,
        }
        sanitized = sanitize_audit_metadata(raw)
        self.assertEqual(sanitized["jwt"], "[REDACTED]")
        self.assertEqual(sanitized["access_token"], "[REDACTED]")
        self.assertEqual(sanitized["api_key"], "[REDACTED]")
        self.assertEqual(sanitized["secret_key"], "[REDACTED]")
        self.assertEqual(sanitized["safe_metric"], 99.4)

    def test_18_audit_metadata_sanitization_recursive_nested_structures(self):
        raw = {
            "user": {
                "profile": {
                    "token": "nested_secret_token",
                    "id": "usr-1",
                },
                "credentials": ["secret1", "secret2"],
            }
        }
        sanitized = sanitize_audit_metadata(raw)
        self.assertEqual(sanitized["user"]["profile"]["token"], "[REDACTED]")
        self.assertEqual(sanitized["user"]["profile"]["id"], "usr-1")

    def test_19_record_audit_event_persists_to_db(self):
        entry = record_audit_event(
            db=self.db,
            action="TEST_PERSISTENCE_EVENT",
            outcome="SUCCESS",
            severity="INFO",
            resource_type="QDS_SESSION",
            resource_id="sess-test-99",
            actor_user_id=self.admin_user.id,
            actor_role="ADMIN",
            metadata={"test_key": "test_val"},
        )
        self.assertIsNotNone(entry)
        self.assertEqual(entry.action, "TEST_PERSISTENCE_EVENT")

        queried = self.db.query(AuditLogModel).filter(AuditLogModel.id == entry.id).first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.outcome, "SUCCESS")

    def test_20_record_audit_event_failure_never_crashes_caller(self):
        # Mocking db to raise an exception during commit
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("Database connection failure")

        # Must NOT raise exception
        result = record_audit_event(
            db=mock_db,
            action="UNCRASHABLE_EVENT",
            outcome="FAILURE",
            severity="HIGH",
        )
        self.assertIsNone(result)

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Security Audit API & RBAC (Tests 21-25)
    # ─────────────────────────────────────────────────────────────────────────

    def test_21_audit_logs_query_api_rbac_admin_full_access(self):
        resp = self.client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("audit_logs", data)
        self.assertIn("total_count", data)

    def test_22_audit_logs_query_api_rbac_analyst_access(self):
        resp = self.client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

    def test_23_audit_logs_query_api_rbac_user_restricted(self):
        resp = self.client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        for log in resp.json()["data"]["audit_logs"]:
            self.assertEqual(log["actor_user_id"], self.regular_user.id)

    def test_24_audit_logs_query_api_filters_by_action_and_severity(self):
        record_audit_event(
            db=self.db,
            action="UNIQUE_FILTER_ACTION",
            outcome="SUCCESS",
            severity="CRITICAL",
        )
        resp = self.client.get(
            "/api/v1/audit/logs?action=UNIQUE_FILTER_ACTION&severity=CRITICAL",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        logs = resp.json()["data"]["audit_logs"]
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "UNIQUE_FILTER_ACTION")
        self.assertEqual(logs[0]["severity"], "CRITICAL")

    def test_25_audit_logs_query_api_pagination(self):
        resp = self.client.get(
            "/api/v1/audit/logs?limit=5&skip=0",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["limit"], 5)
        self.assertEqual(data["skip"], 0)
        self.assertLessEqual(len(data["audit_logs"]), 5)

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Global Domain Exception Hierarchy & Sanitization (Tests 26-30)
    # ─────────────────────────────────────────────────────────────────────────

    def test_26_global_exception_hierarchy_qds_base_exception(self):
        exc = QDSBaseException("Base error", details={"k": "v"})
        self.assertEqual(exc.status_code, 500)
        self.assertEqual(exc.error_code, "INTERNAL_SERVER_ERROR")

    def test_27_global_exception_hierarchy_authentication_error(self):
        exc = AuthenticationError("Auth invalid")
        self.assertEqual(exc.status_code, 401)
        self.assertEqual(exc.error_code, "AUTHENTICATION_FAILED")

    def test_28_global_exception_hierarchy_rate_limit_error(self):
        exc = RateLimitError("Rate limit exceeded")
        self.assertEqual(exc.status_code, 429)
        self.assertEqual(exc.error_code, "RATE_LIMIT_EXCEEDED")

    def test_29_global_exception_handler_sanitizes_internal_errors(self):
        # Trigger an invalid route or deliberate error
        resp = self.client.get("/api/v1/qds/session/non_existent_sess_123456", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(resp.status_code, 404)
        body = resp.json()
        self.assertFalse(body.get("success", True))
        self.assertIn("error", body)
        self.assertNotIn("Traceback", json.dumps(body))
        self.assertNotIn("SELECT", json.dumps(body))

    def test_30_global_exception_handler_includes_correlation_request_id(self):
        resp = self.client.get("/api/v1/qds/session/missing_test_id", headers={"Authorization": f"Bearer {self.admin_token}"})
        body = resp.json()
        self.assertIn("request_id", body.get("error", {}))
        self.assertTrue(len(body["error"]["request_id"]) > 0)

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Performance Metrics, Latency Percentiles & System Health (Tests 31-35)
    # ─────────────────────────────────────────────────────────────────────────

    def test_31_metrics_collector_latency_percentiles_calculation(self):
        collector = MetricsCollector()
        for lat in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]:
            collector.record_latency(lat)

        percentiles = collector.get_latency_percentiles()
        self.assertEqual(percentiles["sample_count"], 10)
        self.assertEqual(percentiles["average_ms"], 55.0)
        self.assertGreaterEqual(percentiles["p50_ms"], 50.0)
        self.assertGreaterEqual(percentiles["p95_ms"], 90.0)
        self.assertGreaterEqual(percentiles["p99_ms"], 90.0)

    def test_32_metrics_collector_bounded_memory_buffer(self):
        collector = MetricsCollector()
        # Feed 1500 latencies (buffer limit is 1000)
        for i in range(1500):
            collector.record_latency(float(i))

        percentiles = collector.get_latency_percentiles()
        self.assertEqual(percentiles["sample_count"], 1000)

    def test_33_monitoring_performance_endpoint_percentiles(self):
        resp = self.client.get(
            "/api/v1/monitoring/performance",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("requests_total", data)
        self.assertIn("latency", data)
        self.assertIn("p50_ms", data["latency"])
        self.assertIn("p95_ms", data["latency"])
        self.assertIn("p99_ms", data["latency"])

    def test_34_system_readiness_endpoint_states(self):
        resp = self.client.get("/api/v1/system/readiness")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["status"], ["READY", "DEGRADED"])
        self.assertIn("database", data)
        self.assertIn("qds_engine", data)
        self.assertIn("threat_engine", data)
        self.assertIn("realtime", data)

    def test_35_system_readiness_zero_credentials_in_output(self):
        resp = self.client.get("/api/v1/system/readiness")
        raw_text = json.dumps(resp.json())
        self.assertNotIn("password", raw_text.lower())
        self.assertNotIn("secret", raw_text.lower())
        self.assertNotIn("token", raw_text.lower())

    # ─────────────────────────────────────────────────────────────────────────
    # 8. CI/CD & Migration Artifact Integrity (Tests 36-37)
    # ─────────────────────────────────────────────────────────────────────────

    def test_36_alembic_migration_files_integrity(self):
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        alembic_ini = os.path.join(workspace_root, "backend", "alembic.ini")
        alembic_env = os.path.join(workspace_root, "backend", "alembic", "env.py")
        alembic_rev = os.path.join(workspace_root, "backend", "alembic", "versions", "0001_initial_schema.py")

        self.assertTrue(os.path.exists(alembic_ini), "alembic.ini missing")
        self.assertTrue(os.path.exists(alembic_env), "alembic/env.py missing")
        self.assertTrue(os.path.exists(alembic_rev), "0001_initial_schema.py missing")

    def test_37_ci_cd_workflow_files_integrity(self):
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        backend_ci = os.path.join(workspace_root, ".github", "workflows", "backend-tests.yml")
        frontend_ci = os.path.join(workspace_root, ".github", "workflows", "frontend-build.yml")
        docker_ci = os.path.join(workspace_root, ".github", "workflows", "docker-build.yml")
        ops_doc = os.path.join(workspace_root, "docs", "PRODUCTION_OPERATIONS.md")

        self.assertTrue(os.path.exists(backend_ci), "backend-tests.yml missing")
        self.assertTrue(os.path.exists(frontend_ci), "frontend-build.yml missing")
        self.assertTrue(os.path.exists(docker_ci), "docker-build.yml missing")
        self.assertTrue(os.path.exists(ops_doc), "PRODUCTION_OPERATIONS.md missing")


if __name__ == "__main__":
    unittest.main()
