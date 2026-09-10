"""
Comprehensive End-to-End (E2E) Integration and Edge-Case Test Suite — Phase 7.

Tests the complete user journey and failure edge cases:
- E2E-01: Complete legitimate signature flow from user registration to verification & analytics.
- E2E-02: Adversarial forgery attack flow with deterministic non-AI detection & audit logging.
- E2E-03: Anti-replay security validation (nonce reuse and timestamp delta threshold).
- E2E-04: Role-based access control (USER vs SECURITY_ANALYST vs ADMIN).
- Edge Cases: Invalid JWT, missing auth header, nonexistent session, duplicate user registration,
  invalid credentials, cross-user session access rejection, unsupported attack vectors, empty payloads,
  and production health check endpoint behavior.
"""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.db.models import UserModel, QDSSessionModel, VerificationResultModel, ThreatLogModel

# Dedicated isolated in-memory test database with StaticPool
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestPhase7EndToEnd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)
        cls.tokens = {}

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    # ── E2E-01: Complete Legitimate Flow ─────────────────────────────────────
    def test_e2e_01_complete_legitimate_flow(self):
        """
        User Registration -> Login -> Receive JWT -> Create Signature ->
        Teleportation -> Verification -> DB Persistence -> Analytics Reflection.
        """
        # 1. Register User
        reg_payload = {
            "username": "e2e_alice",
            "email": "e2e_alice@qds.org",
            "password": "StrongPassword2026!",
            "role": "USER"
        }
        res_reg = self.client.post("/api/v1/auth/register", json=reg_payload)
        self.assertEqual(res_reg.status_code, 201)
        self.assertIn("access_token", res_reg.json())
        self.assertEqual(res_reg.json()["user"]["username"], "e2e_alice")
        self.assertNotIn("password_hash", res_reg.json()["user"])

        # 2. Login
        login_res = self.client.post("/api/v1/auth/login", json={
            "username": "e2e_alice",
            "password": "StrongPassword2026!"
        })
        self.assertEqual(login_res.status_code, 200)
        alice_token = login_res.json()["access_token"]
        self.tokens["alice"] = alice_token
        auth_headers = {"Authorization": f"Bearer {alice_token}"}

        # 3. Create Signature Session
        create_res = self.client.post("/api/v1/qds/create-signature", json={
            "message": "Wire transfer order: INR 5,00,000 to Bob Corp",
            "sender_id": "usr-e2e-alice"
        }, headers=auth_headers)
        self.assertEqual(create_res.status_code, 201)
        session_data = create_res.json()
        session_id = session_data["session_id"]
        self.assertEqual(session_data["status"], "PENDING")
        self.assertEqual(len(session_data["message_hash"]), 64)

        # 4. Teleport Signature
        tp_res = self.client.post("/api/v1/qds/teleport", json={"session_id": session_id}, headers=auth_headers)
        self.assertEqual(tp_res.status_code, 200)
        self.assertEqual(tp_res.json()["data"]["status"], "TELEPORTED")
        self.assertEqual(len(tp_res.json()["data"]["classical_bits"]), 256)

        # 5. Verify Signature
        ver_res = self.client.post("/api/v1/qds/verify", json={"session_id": session_id}, headers=auth_headers)
        self.assertEqual(ver_res.status_code, 200)
        eval_data = ver_res.json()["data"]
        self.assertEqual(eval_data["decision"], "LEGITIMATE")
        self.assertEqual(eval_data["action"], "ACCEPT")
        self.assertEqual(eval_data["metrics"]["state_fidelity"], 1.0)
        self.assertEqual(eval_data["metrics"]["qber_percent"], 0.0)

        # 6. Retrieve Session Details and Confirm DB Persistence
        get_res = self.client.get(f"/api/v1/qds/session/{session_id}", headers=auth_headers)
        self.assertEqual(get_res.status_code, 200)
        retrieved = get_res.json()
        self.assertEqual(retrieved["session_id"], session_id)
        self.assertEqual(retrieved["status"], "VERIFIED")
        self.assertIsNotNone(retrieved["verification_result"])
        self.assertEqual(retrieved["verification_result"]["fidelity"], 1.0)

        # 7. Confirm Analytics Reflects the Verified Session
        analytics_res = self.client.get("/api/v1/analytics/summary", headers=auth_headers)
        self.assertEqual(analytics_res.status_code, 200)
        summary = analytics_res.json()
        self.assertGreaterEqual(summary["total_sessions"], 1)
        self.assertGreaterEqual(summary["accepted_sessions"], 1)

    # ── E2E-02: Adversarial Forgery Attack Flow ──────────────────────────────
    def test_e2e_02_forgery_attack_flow(self):
        """
        Authenticate -> Create Signature -> Teleport -> Inject Forgery ->
        Deterministic Non-AI Threat Detection -> Confirm Malicious/Reject & Audit Log.
        """
        auth_headers = {"Authorization": f"Bearer {self.tokens['alice']}"}

        # 1. Create and Teleport
        create_res = self.client.post("/api/v1/qds/create-signature", json={
            "message": "Military clearance code ALPHA-NINER",
            "sender_id": "usr-e2e-alice"
        }, headers=auth_headers)
        session_id = create_res.json()["session_id"]
        self.client.post("/api/v1/qds/teleport", json={"session_id": session_id}, headers=auth_headers)

        # 2. Inject Forgery Attack
        sim_res = self.client.post("/api/v1/threats/simulate", json={
            "session_id": session_id,
            "attack_type": "FORGERY",
            "tamper_ratio": 0.20
        }, headers=auth_headers)
        self.assertEqual(sim_res.status_code, 200)
        self.assertEqual(sim_res.json()["data"]["injected_threat"], "FORGERY")

        # 3. Run Threat Detection
        det_res = self.client.post("/api/v1/threats/detect", json={"session_id": session_id}, headers=auth_headers)
        self.assertEqual(det_res.status_code, 200)
        det_data = det_res.json()
        self.assertEqual(det_data["decision"], "MALICIOUS")
        self.assertEqual(det_data["severity"], "CRITICAL")
        self.assertEqual(det_data["attack_type"], "SIGNATURE_FORGERY")
        self.assertGreater(det_data["metrics"]["qber_percent"], 5.0)

        # 4. Verify Audit Log Persistence
        log_res = self.client.get("/api/v1/threats/logs", headers=auth_headers)
        self.assertEqual(log_res.status_code, 200)
        logs = log_res.json()["data"]["logs"]
        matching = [l for l in logs if (l.get("qds_session_id") == session_id or l.get("session_id") == session_id)]
        self.assertGreater(len(matching), 0)
        self.assertEqual(matching[0]["decision"], "MALICIOUS")

    # ── E2E-03: Replay Attack Flow ───────────────────────────────────────────
    def test_e2e_03_replay_attack_flow(self):
        """
        Create session -> Nonce registered on first evaluation ->
        Second evaluation with same nonce triggers anti-replay rejection.
        """
        auth_headers = {"Authorization": f"Bearer {self.tokens['alice']}"}

        # 1. Create and Teleport
        create_res = self.client.post("/api/v1/qds/create-signature", json={
            "message": "One-time authorization token #8841",
            "sender_id": "usr-e2e-alice"
        }, headers=auth_headers)
        session_id = create_res.json()["session_id"]
        self.client.post("/api/v1/qds/teleport", json={"session_id": session_id}, headers=auth_headers)

        # 2. First evaluation (Legitimate)
        det1 = self.client.post("/api/v1/threats/detect", json={"session_id": session_id}, headers=auth_headers)
        self.assertEqual(det1.status_code, 200)
        self.assertEqual(det1.json()["decision"], "LEGITIMATE")

        # 3. Second evaluation (Replay / Nonce reuse triggered)
        det2 = self.client.post("/api/v1/threats/detect", json={"session_id": session_id}, headers=auth_headers)
        self.assertEqual(det2.status_code, 200)
        self.assertEqual(det2.json()["attack_type"], "REPLAY_ATTACK")
        self.assertIn(det2.json()["decision"], ("MALICIOUS", "SUSPICIOUS"))

    # ── E2E-04: Role-Based Access Control (RBAC) Flow ────────────────────────
    def test_e2e_04_rbac_flow(self):
        """
        Verify role separation:
        USER cannot access other users' sessions;
        SECURITY_ANALYST can inspect cross-user logs;
        ADMIN has unrestricted administrative oversight.
        """
        # Register User Bob
        reg_bob = self.client.post("/api/v1/auth/register", json={
            "username": "e2e_bob",
            "email": "e2e_bob@qds.org",
            "password": "PasswordBob123!",
            "role": "USER"
        })
        self.assertEqual(reg_bob.status_code, 201)
        bob_token = reg_bob.json()["access_token"]
        bob_headers = {"Authorization": f"Bearer {bob_token}"}

        # Register Security Analyst
        reg_analyst = self.client.post("/api/v1/auth/register", json={
            "username": "e2e_analyst",
            "email": "analyst@soc.qds.org",
            "password": "AnalystPassword123!",
            "role": "SECURITY_ANALYST"
        })
        self.assertEqual(reg_analyst.status_code, 201)
        analyst_token = reg_analyst.json()["access_token"]
        analyst_headers = {"Authorization": f"Bearer {analyst_token}"}

        # Register Admin
        reg_admin = self.client.post("/api/v1/auth/register", json={
            "username": "e2e_admin",
            "email": "admin@qds.org",
            "password": "AdminPassword123!",
            "role": "ADMIN"
        })
        self.assertEqual(reg_admin.status_code, 201)
        admin_token = reg_admin.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Bob creates a session
        bob_sess = self.client.post("/api/v1/qds/create-signature", json={
            "message": "Bob's private transaction",
            "sender_id": "usr-e2e-bob"
        }, headers=bob_headers)
        bob_session_id = bob_sess.json()["session_id"]

        # Alice attempts to access Bob's session -> Must be 403 FORBIDDEN
        alice_headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        alice_access = self.client.get(f"/api/v1/qds/session/{bob_session_id}", headers=alice_headers)
        self.assertEqual(alice_access.status_code, 403)
        self.assertIn("Access denied", alice_access.json()["detail"])

        # Analyst accesses Bob's session -> Must succeed
        analyst_access = self.client.get(f"/api/v1/qds/session/{bob_session_id}", headers=analyst_headers)
        self.assertEqual(analyst_access.status_code, 200)

        # Admin accesses Bob's session -> Must succeed
        admin_access = self.client.get(f"/api/v1/qds/session/{bob_session_id}", headers=admin_headers)
        self.assertEqual(admin_access.status_code, 200)

    # ── Failure & Edge Case Tests ────────────────────────────────────────────
    def test_edge_cases_and_security_failures(self):
        auth_headers = {"Authorization": f"Bearer {self.tokens['alice']}"}

        # 1. Missing Authorization Header on Protected Route
        res1 = self.client.get("/api/v1/auth/me")
        self.assertEqual(res1.status_code, 401)
        self.assertIn("token is missing", res1.json()["detail"])

        # 2. Invalid JWT Token
        res2 = self.client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt.signature"})
        self.assertEqual(res2.status_code, 401)

        # 3. Nonexistent QDS Session ID
        res3 = self.client.get("/api/v1/qds/session/nonexistent-session-id-9999", headers=auth_headers)
        self.assertEqual(res3.status_code, 404)

        # 4. Duplicate Registration
        res4 = self.client.post("/api/v1/auth/register", json={
            "username": "e2e_alice",  # Already exists
            "email": "different_email@qds.org",
            "password": "Password123!"
        })
        self.assertEqual(res4.status_code, 400)

        # 5. Invalid Login Credentials
        res5 = self.client.post("/api/v1/auth/login", json={
            "username": "e2e_alice",
            "password": "WrongPassword999!"
        })
        self.assertEqual(res5.status_code, 401)

        # 6. Empty Message Payload in Create Signature
        res6 = self.client.post("/api/v1/qds/create-signature", json={"message": "   "}, headers=auth_headers)
        self.assertEqual(res6.status_code, 400)

        # 7. Unsupported Attack Vector in Simulate
        sess_res = self.client.post("/api/v1/qds/create-signature", json={"message": "Security Validation Message"}, headers=auth_headers)
        self.assertEqual(sess_res.status_code, 201)
        valid_session_id = sess_res.json()["session_id"]

        res7 = self.client.post("/api/v1/threats/simulate", json={
            "session_id": valid_session_id,
            "attack_type": "UNKNOWN_ATTACK_VECTOR_XYZ"
        }, headers=auth_headers)
        self.assertEqual(res7.status_code, 400)

        # 8. Health Endpoint Behavior
        res8 = self.client.get("/health")
        self.assertEqual(res8.status_code, 200)
        body8 = res8.json()
        self.assertEqual(body8["status"], "healthy")
        self.assertIn("database", body8)
        self.assertEqual(body8["database"], "connected")
        self.assertNotIn("password", str(body8).lower())

        # 9. System Info Endpoint Behavior
        res9 = self.client.get("/api/v1/system/info")
        self.assertEqual(res9.status_code, 200)
        body9 = res9.json()
        self.assertEqual(body9["quantum_engine"]["status"], "OPERATIONAL")
        self.assertEqual(body9["threat_engine"]["status"], "OPERATIONAL")
        self.assertNotIn("secret", str(body9).lower())


if __name__ == "__main__":
    unittest.main()
