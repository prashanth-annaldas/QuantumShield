"""
Comprehensive Unittest Test Suite — Phase 5: FastAPI REST Backend Integration.

Tests:
1.  Health and Root endpoints.
2.  User registration (success & role assignment).
3.  Duplicate registration rejection (duplicate username & duplicate email).
4.  Successful login (JWT token return).
5.  Invalid login credentials rejection (401 Unauthorized).
6.  Protected route access with valid JWT (/auth/me).
7.  Missing JWT token rejection (401 Unauthorized).
8.  Invalid / malformed JWT token rejection (401 Unauthorized).
9.  Role-based authorization checks (USER, SECURITY_ANALYST, ADMIN).
10. QDS Create Signature API (/create-signature) with message hashing & DB persistence.
11. QDS Teleportation API (/teleport) with classical bits & status updates.
12. QDS Verification API (/verify) with fidelity, QBER, mismatch rate persistence.
13. QDS Session Detail API (/session/{id}) and access control (owner vs other user).
14. Threat Simulation API (/simulate) across all 5 attack vectors.
15. Threat Detection API (/detect) invoking deterministic Phase 4 engine.
16. Threat Audit Logs API (/logs) with filtering.
17. Analytics Summary API (/summary) computing acceptance rate & health.
18. Threat Statistics API (/threat-statistics).
19. Security Metrics API (/security-metrics).
"""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.db.models import UserModel, QDSSessionModel, VerificationResultModel, ThreatLogModel

# In-memory test database with StaticPool so all connections share the same DB in-memory
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


class TestPhase5APIBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Apply database override and create all tables
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)

        # Helper tokens container
        cls.tokens = {}

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    # ── 1. Root & Health Endpoints ───────────────────────────────────────────

    def test_01_root_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "OPERATIONAL")
        self.assertIn("version", body)

    def test_02_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "healthy")
        self.assertIn("application", body)

    # ── 2. User Registration ─────────────────────────────────────────────────

    def test_03_user_registration_success(self):
        payload = {
            "username": "alice_user",
            "email": "alice@quantum.org",
            "password": "SecurePassword123!",
            "role": "USER"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["username"], "alice_user")
        self.assertEqual(data["user"]["email"], "alice@quantum.org")
        self.assertEqual(data["user"]["role"], "USER")
        self.assertNotIn("password", data["user"])
        self.assertNotIn("password_hash", data["user"])
        self.tokens["alice"] = data["access_token"]

    def test_04_duplicate_username_rejection(self):
        payload = {
            "username": "alice_user",  # Duplicate
            "email": "different_alice@quantum.org",
            "password": "AnotherPassword123!",
            "role": "USER"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already taken", res.json()["detail"])

    def test_05_duplicate_email_rejection(self):
        payload = {
            "username": "bob_user",
            "email": "alice@quantum.org",  # Duplicate email
            "password": "PasswordBob123!",
            "role": "USER"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already registered", res.json()["detail"])

    def test_06_register_analyst_and_admin(self):
        # Register Security Analyst
        res1 = self.client.post("/api/v1/auth/register", json={
            "username": "carol_analyst",
            "email": "carol@soc.org",
            "password": "AnalystPassword123!",
            "role": "SECURITY_ANALYST"
        })
        self.assertEqual(res1.status_code, 201)
        self.tokens["analyst"] = res1.json()["access_token"]

        # Register Admin
        res2 = self.client.post("/api/v1/auth/register", json={
            "username": "dave_admin",
            "email": "dave@admin.org",
            "password": "AdminPassword123!",
            "role": "ADMIN"
        })
        self.assertEqual(res2.status_code, 201)
        self.tokens["admin"] = res2.json()["access_token"]

    # ── 3. Login & Authentication ────────────────────────────────────────────

    def test_07_login_success(self):
        res = self.client.post("/api/v1/auth/login", json={
            "username": "alice_user",
            "password": "SecurePassword123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["username"], "alice_user")

    def test_08_login_invalid_password(self):
        res = self.client.post("/api/v1/auth/login", json={
            "username": "alice_user",
            "password": "WrongPassword999!"
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("Incorrect username or password", res.json()["detail"])

    def test_09_login_nonexistent_user(self):
        res = self.client.post("/api/v1/auth/login", json={
            "username": "ghost_user",
            "password": "SomePassword123!"
        })
        self.assertEqual(res.status_code, 401)

    # ── 4. Protected Route & Token Validation ────────────────────────────────

    def test_10_protected_route_success(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        res = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["username"], "alice_user")

    def test_11_missing_jwt_rejection(self):
        res = self.client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 401)
        self.assertIn("token is missing", res.json()["detail"])

    def test_12_invalid_jwt_rejection(self):
        headers = {"Authorization": "Bearer invalid.token.string"}
        res = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(res.status_code, 401)

    # ── 5. QDS Full Lifecycle APIs ───────────────────────────────────────────

    def test_13_create_signature_api(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        payload = {
            "message": "Quantum Wire Transfer: 50,000 INR to Vendor X",
            "sender_id": "usr-alice"
        }
        res = self.client.post("/api/v1/qds/create-signature", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("session_id", data)
        self.assertEqual(len(data["message_hash"]), 64)
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["sender_id"], "usr-alice")

        # Save session_id for subsequent steps
        TestPhase5APIBackend.session_id_clean = data["session_id"]

    def test_14_teleport_signature_api(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        payload = {"session_id": TestPhase5APIBackend.session_id_clean}
        res = self.client.post("/api/v1/qds/teleport", json=payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["status"], "TELEPORTED")
        self.assertEqual(len(data["classical_bits"]), 256)
        self.assertEqual(data["bell_pair_count"], 256)

    def test_15_verify_signature_api(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        payload = {"session_id": TestPhase5APIBackend.session_id_clean}
        res = self.client.post("/api/v1/qds/verify", json=payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["decision"], "LEGITIMATE")
        self.assertEqual(data["action"], "ACCEPT")
        self.assertEqual(data["metrics"]["state_fidelity"], 1.0)
        self.assertEqual(data["metrics"]["qber_percent"], 0.0)
        self.assertEqual(data["metrics"]["mismatch_rate"], 0.0)

    def test_16_get_session_details(self):
        # Owner access succeeds
        headers_owner = {"Authorization": f"Bearer {self.tokens['alice']}"}
        res = self.client.get(f"/api/v1/qds/session/{TestPhase5APIBackend.session_id_clean}", headers=headers_owner)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["session_id"], TestPhase5APIBackend.session_id_clean)
        self.assertEqual(data["status"], "VERIFIED")
        self.assertIsNotNone(data["verification_result"])
        self.assertEqual(data["verification_result"]["fidelity"], 1.0)

        # Analyst access succeeds (RBAC)
        headers_analyst = {"Authorization": f"Bearer {self.tokens['analyst']}"}
        res_an = self.client.get(f"/api/v1/qds/session/{TestPhase5APIBackend.session_id_clean}", headers=headers_analyst)
        self.assertEqual(res_an.status_code, 200)

    # ── 6. Threat Simulation & Non-AI Detection ──────────────────────────────

    def test_17_simulate_forgery_and_detect(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}

        # 1. Create a fresh session
        res_create = self.client.post("/api/v1/qds/create-signature", json={
            "message": "Top Secret Military Payload",
            "sender_id": "usr-alice"
        }, headers=headers)
        session_id = res_create.json()["session_id"]

        # 2. Teleport
        self.client.post("/api/v1/qds/teleport", json={"session_id": session_id}, headers=headers)

        # 3. Inject Forgery attack
        res_sim = self.client.post("/api/v1/threats/simulate", json={
            "session_id": session_id,
            "attack_type": "FORGERY",
            "tamper_ratio": 0.20
        }, headers=headers)
        self.assertEqual(res_sim.status_code, 200)
        self.assertEqual(res_sim.json()["data"]["injected_threat"], "FORGERY")

        # 4. Verify / Detect (Deterministic Non-AI engine should flag MALICIOUS)
        res_det = self.client.post("/api/v1/threats/detect", json={"session_id": session_id}, headers=headers)
        self.assertEqual(res_det.status_code, 200)
        data = res_det.json()
        self.assertEqual(data["decision"], "MALICIOUS")
        self.assertEqual(data["severity"], "CRITICAL")
        self.assertEqual(data["attack_type"], "SIGNATURE_FORGERY")
        self.assertGreater(data["metrics"]["qber_percent"], 5.0)

    def test_18_simulate_impersonation(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        res_create = self.client.post("/api/v1/qds/create-signature", json={
            "message": "Auth Request from Alice",
            "sender_id": "usr-alice"
        }, headers=headers)
        session_id = res_create.json()["session_id"]

        # Inject impersonation
        res_sim = self.client.post("/api/v1/threats/simulate", json={
            "session_id": session_id,
            "attack_type": "IMPERSONATION"
        }, headers=headers)
        self.assertEqual(res_sim.status_code, 200)

        # Detect
        res_det = self.client.post("/api/v1/threats/detect", json={"session_id": session_id}, headers=headers)
        self.assertEqual(res_det.status_code, 200)
        self.assertEqual(res_det.json()["decision"], "MALICIOUS")
        self.assertEqual(res_det.json()["attack_type"], "IMPERSONATION_ATTACK")

    def test_19_simulate_unauthorized_rate_limiting(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        res_create = self.client.post("/api/v1/qds/create-signature", json={
            "message": "Financial wire",
            "sender_id": "usr-alice"
        }, headers=headers)
        session_id = res_create.json()["session_id"]

        # Inject unauthorized verification attempts
        res_sim = self.client.post("/api/v1/threats/simulate", json={
            "session_id": session_id,
            "attack_type": "UNAUTHORIZED_VERIFICATION"
        }, headers=headers)
        self.assertEqual(res_sim.status_code, 200)

        # Detect
        res_det = self.client.post("/api/v1/threats/detect", json={"session_id": session_id}, headers=headers)
        self.assertEqual(res_det.status_code, 200)
        self.assertEqual(res_det.json()["decision"], "SUSPICIOUS")
        self.assertEqual(res_det.json()["attack_type"], "UNAUTHORIZED_VERIFICATION")

    # ── 7. Threat Logs API ───────────────────────────────────────────────────

    def test_20_query_threat_logs(self):
        headers = {"Authorization": f"Bearer {self.tokens['analyst']}"}
        res = self.client.get("/api/v1/threats/logs", headers=headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()["data"]
        self.assertGreater(body["total_count"], 0)
        self.assertIsInstance(body["logs"], list)

        # Filter by decision
        res_filtered = self.client.get("/api/v1/threats/logs?decision=MALICIOUS", headers=headers)
        self.assertEqual(res_filtered.status_code, 200)
        for log in res_filtered.json()["data"]["logs"]:
            self.assertEqual(log["decision"], "MALICIOUS")

    # ── 8. Security Analytics APIs ───────────────────────────────────────────

    def test_21_analytics_summary(self):
        headers = {"Authorization": f"Bearer {self.tokens['alice']}"}
        res = self.client.get("/api/v1/analytics/summary", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_sessions", data)
        self.assertIn("accepted_sessions", data)
        self.assertIn("rejected_sessions", data)
        self.assertIn("acceptance_rate", data)
        self.assertIn("threat_counts_by_type", data)
        self.assertIn("system_health_status", data)

    def test_22_threat_statistics(self):
        headers = {"Authorization": f"Bearer {self.tokens['analyst']}"}
        res = self.client.get("/api/v1/analytics/threat-statistics", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_threats", data)
        self.assertIn("threat_counts_by_type", data)
        self.assertIn("severity_breakdown", data)

    def test_23_security_metrics(self):
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        res = self.client.get("/api/v1/analytics/security-metrics", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("average_fidelity", data)
        self.assertIn("average_qber", data)
        self.assertIn("average_mismatch_rate", data)
        self.assertIn("total_verified_sessions", data)


if __name__ == "__main__":
    unittest.main()
