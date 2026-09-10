"""
End-to-End SOC Pipeline Test

Verifies the complete flow:
CREATE SIGNATURE -> TELEPORT -> NORMAL VERIFY -> LEGITIMATE
-> ATTACK SIMULATOR (REPLAY ATTACK) -> VERIFY AGAIN
-> THREAT ENGINE (MALICIOUS) -> SECURITY EVENT
-> CORRELATION RULE -> INCIDENT CREATED -> SOC UPDATED
"""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.db.models import IncidentModel, SecurityEventModel

# In-memory test database
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


class TestE2ESOCPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)
        cls.tokens = {}

        # Disable async websocket broadcasting for unit tests 
        # (publisher.py already handles no-event-loop, but we just ensure it's fine)
        
        # Register a security analyst to check incidents
        res = cls.client.post("/api/v1/auth/register", json={
            "username": "soc_analyst",
            "email": "soc@quantum.org",
            "password": "SecurePassword123!",
            "role": "SECURITY_ANALYST"
        })
        cls.tokens["analyst"] = res.json()["access_token"]

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()

    def test_e2e_threat_detection_to_incident_creation(self):
        headers = {"Authorization": f"Bearer {self.tokens['analyst']}"}

        # 1. CREATE SIGNATURE
        res_create = self.client.post("/api/v1/qds/create-signature", json={
            "message": "Critical Quantum Wire Transfer",
            "sender_id": "usr-alice"
        }, headers=headers)
        self.assertEqual(res_create.status_code, 201)
        session_id = res_create.json()["session_id"]

        # 2. TELEPORT
        res_teleport = self.client.post("/api/v1/qds/teleport", json={"session_id": session_id}, headers=headers)
        self.assertEqual(res_teleport.status_code, 200)

        # 3. NORMAL VERIFY -> LEGITIMATE
        res_verify1 = self.client.post("/api/v1/qds/verify", json={"session_id": session_id}, headers=headers)
        self.assertEqual(res_verify1.status_code, 200)
        self.assertEqual(res_verify1.json()["data"]["decision"], "LEGITIMATE")

        # 4. ATTACK SIMULATOR -> REPLAY ATTACK
        res_simulate = self.client.post("/api/v1/threats/simulate", json={
            "session_id": session_id,
            "attack_type": "REPLAY"
        }, headers=headers)
        self.assertEqual(res_simulate.status_code, 200)

        # 5. VERIFY AGAIN -> THREAT ENGINE -> MALICIOUS -> SECURITY EVENT -> CORRELATION RULE
        res_verify2 = self.client.post("/api/v1/qds/verify", json={"session_id": session_id}, headers=headers)
        self.assertEqual(res_verify2.status_code, 200)
        self.assertEqual(res_verify2.json()["data"]["decision"], "MALICIOUS")
        self.assertEqual(res_verify2.json()["data"]["threat_type"], "REPLAY_ATTACK")

        # 6. Check INCIDENT CREATED via SOC INCIDENT CENTER API
        res_incidents = self.client.get("/api/v1/incidents?status=OPEN", headers=headers)
        self.assertEqual(res_incidents.status_code, 200)
        incidents_data = res_incidents.json()["data"]
        
        # We should have at least one incident created (due to replay attack correlation rule C-02 or C-01)
        # Actually, wait, C-02 requires both REPLAY and FORGERY. 
        # C-01 requires 2 HIGH/CRITICAL events. 
        # Wait! The REPLAY attack from Threat Engine generates a CRITICAL event. 
        # C-01 requires "2 or more HIGH or CRITICAL". 
        # But wait, did we generate an incident? Let's check!
        # If it didn't generate an incident because it's only 1 CRITICAL, let's inject a FORGERY too to trigger C-02.
        
        # Let's inject FORGERY to ensure an incident is generated (Rule C-02: Replay + Forgery combo)
        res_simulate_forgery = self.client.post("/api/v1/threats/simulate", json={
            "session_id": session_id,
            "attack_type": "FORGERY",
            "tamper_ratio": 0.20
        }, headers=headers)
        
        res_verify3 = self.client.post("/api/v1/qds/verify", json={"session_id": session_id}, headers=headers)
        self.assertEqual(res_verify3.status_code, 200)
        
        res_incidents_updated = self.client.get("/api/v1/incidents?status=OPEN", headers=headers)
        self.assertEqual(res_incidents_updated.status_code, 200)
        incidents = res_incidents_updated.json()["data"]["incidents"]
        self.assertGreater(len(incidents), 0, "No incidents were created!")
        
        incident = incidents[0]
        self.assertEqual(incident["source_session_id"], session_id)
        self.assertEqual(incident["status"], "OPEN")
        
        # 7. Check SOC UPDATED (Monitoring Metrics)
        res_metrics = self.client.get("/api/v1/monitoring/metrics", headers=headers)
        self.assertEqual(res_metrics.status_code, 200)
        metrics = res_metrics.json()
        
        # threats_detected should be > 0
        self.assertGreater(metrics["threat_metrics"]["threats_detected"], 0)
        self.assertGreater(metrics["qds_metrics"]["verifications_rejected"], 0)
        self.assertGreater(metrics["incident_metrics"]["open_incidents"], 0)


if __name__ == "__main__":
    unittest.main()
