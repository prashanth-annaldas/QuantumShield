"""
Comprehensive Unit Test Suite for Phase 3 — Teleportation-Based QDS Protocol.
Contains all 20 mandatory test cases matching Task 11 requirements.
"""
import unittest
from datetime import timezone
import numpy as np

from app.quantum import QubitState, EPSILON, get_pauli_correction
from app.qds import (
    MessageHasher, SignatureStateEncoder, QDSSession,
    QDSVerifier, QDSStatus, TeleportationProcessor
)

class TestQDSProtocolPhase3(unittest.TestCase):

    # -------------------------------------------------------------
    # 1. Same message produces same SHA-256 hash
    # -------------------------------------------------------------
    def test_01_same_message_same_hash(self):
        msg = "Pay ₹100 to Bob"
        h1 = MessageHasher.hash_message(msg)
        h2 = MessageHasher.hash_message(msg)
        self.assertEqual(h1["hash_hex"], h2["hash_hex"])
        self.assertEqual(h1["hash_bits"], h2["hash_bits"])

    # -------------------------------------------------------------
    # 2. Different messages produce different hashes
    # -------------------------------------------------------------
    def test_02_different_messages_different_hashes(self):
        h1 = MessageHasher.hash_message("Pay ₹100 to Bob")
        h2 = MessageHasher.hash_message("Pay ₹100 to Alice")
        self.assertNotEqual(h1["hash_hex"], h2["hash_hex"])

    # -------------------------------------------------------------
    # 3. Hash binary representation contains exactly 256 bits
    # -------------------------------------------------------------
    def test_03_hash_binary_exactly_256_bits(self):
        h = MessageHasher.hash_message("Pay ₹100 to Bob")
        self.assertEqual(len(h["hash_bits"]), 256)
        self.assertEqual(len(h["bit_list"]), 256)
        for bit in h["bit_list"]:
            self.assertIn(bit, (0, 1))

    # -------------------------------------------------------------
    # 4. Bit 0 correctly encodes to |0⟩
    # -------------------------------------------------------------
    def test_04_bit_0_encodes_to_state_0(self):
        state = SignatureStateEncoder.encode_bit(0)
        self.assertEqual(state.alpha, 1.0)
        self.assertEqual(state.beta, 0.0)

    # -------------------------------------------------------------
    # 5. Bit 1 correctly encodes to |1⟩
    # -------------------------------------------------------------
    def test_05_bit_1_encodes_to_state_1(self):
        state = SignatureStateEncoder.encode_bit(1)
        self.assertEqual(state.alpha, 0.0)
        self.assertEqual(state.beta, 1.0)

    # -------------------------------------------------------------
    # 6. Invalid bits are rejected
    # -------------------------------------------------------------
    def test_06_invalid_bits_rejected(self):
        with self.assertRaises(ValueError):
            SignatureStateEncoder.encode_bit(2)
        with self.assertRaises(ValueError):
            SignatureStateEncoder.encode_bits_to_qubits([0, 1, 9])

    # -------------------------------------------------------------
    # 7. QDS session generates a unique session ID
    # -------------------------------------------------------------
    def test_07_unique_session_id(self):
        s1 = QDSSession("Pay ₹100")
        s2 = QDSSession("Pay ₹100")
        self.assertNotEqual(s1.session_id, s2.session_id)
        self.assertTrue(s1.session_id.startswith("qds-sess-"))

    # -------------------------------------------------------------
    # 8. QDS session generates a nonce
    # -------------------------------------------------------------
    def test_08_session_nonce_generation(self):
        s = QDSSession("Pay ₹100")
        self.assertIsNotNone(s.nonce)
        self.assertEqual(len(s.nonce), 32) # 16 bytes = 32 hex chars

    # -------------------------------------------------------------
    # 9. QDS session contains a timezone-aware timestamp
    # -------------------------------------------------------------
    def test_09_timezone_aware_timestamp(self):
        s = QDSSession("Pay ₹100")
        self.assertIsNotNone(s.timestamp.tzinfo)
        self.assertEqual(s.timestamp.tzinfo, timezone.utc)

    # -------------------------------------------------------------
    # 10. Teleport |0⟩ successfully
    # -------------------------------------------------------------
    def test_10_teleport_state_0(self):
        s0 = QubitState.state_0()
        res = TeleportationProcessor.teleport_single_qubit(0, s0, deterministic=True)
        self.assertTrue(np.isclose(res["fidelity"], 1.0, atol=EPSILON))
        rec = res["reconstructed_state"]
        self.assertEqual(SignatureStateEncoder.decode_qubit(rec), 0)

    # -------------------------------------------------------------
    # 11. Teleport |1⟩ successfully
    # -------------------------------------------------------------
    def test_11_teleport_state_1(self):
        s1 = QubitState.state_1()
        res = TeleportationProcessor.teleport_single_qubit(0, s1, deterministic=True)
        self.assertTrue(np.isclose(res["fidelity"], 1.0, atol=EPSILON))
        rec = res["reconstructed_state"]
        self.assertEqual(SignatureStateEncoder.decode_qubit(rec), 1)

    # -------------------------------------------------------------
    # 12. Teleport |+⟩ successfully
    # -------------------------------------------------------------
    def test_12_teleport_state_plus(self):
        s_plus = QubitState.state_plus()
        res = TeleportationProcessor.teleport_single_qubit(0, s_plus, deterministic=True)
        self.assertTrue(np.isclose(res["fidelity"], 1.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 13. Teleport |−⟩ successfully
    # -------------------------------------------------------------
    def test_13_teleport_state_minus(self):
        s_minus = QubitState.state_minus()
        res = TeleportationProcessor.teleport_single_qubit(0, s_minus, deterministic=True)
        self.assertTrue(np.isclose(res["fidelity"], 1.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 14. Reconstructed state has fidelity approximately 1
    # -------------------------------------------------------------
    def test_14_reconstructed_state_fidelity(self):
        session = QDSSession("Pay ₹100 to Bob")
        TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
        for res in session.per_qubit_results:
            self.assertTrue(np.isclose(res["fidelity"], 1.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 15. All valid measurement outcomes map to a correction
    # -------------------------------------------------------------
    def test_15_measurement_outcomes_mapping(self):
        for bits in ["00", "01", "10", "11"]:
            gate = get_pauli_correction(bits)
            self.assertEqual(gate.shape, (2, 2))

    # -------------------------------------------------------------
    # 16. Teleportation correction mapping is mathematically verified
    # -------------------------------------------------------------
    def test_16_teleportation_correction_math_verified(self):
        state = QubitState(0.6, 0.8) # arbitrary state
        for bits in ["00", "01", "10", "11"]:
            # Test all 4 measurement outcomes
            bob_pre_states = {
                "00": QubitState(state.alpha, state.beta, validate_normalization=False),
                "01": QubitState(state.beta, state.alpha, validate_normalization=False),
                "10": QubitState(state.alpha, -state.beta, validate_normalization=False),
                "11": QubitState(state.beta, -state.alpha, validate_normalization=False)
            }
            uncorrected = bob_pre_states[bits]
            corr = get_pauli_correction(bits)
            reconstructed = uncorrected.apply_gate(corr)
            fidelity = state.inner_product(reconstructed)
            self.assertTrue(np.isclose(np.abs(fidelity)**2, 1.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 17. A multi-bit signature sequence is reconstructed correctly
    # -------------------------------------------------------------
    def test_17_multibit_sequence_reconstructed(self):
        session = QDSSession("Pay ₹100 to Bob")
        TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
        rec_bits = SignatureStateEncoder.decode_qubits_to_bits(session.reconstructed_qubits)
        self.assertEqual(rec_bits, session.expected_bits)

    # -------------------------------------------------------------
    # 18. Original hash equals reconstructed hash
    # -------------------------------------------------------------
    def test_18_original_equals_reconstructed_hash(self):
        session = QDSSession("Pay ₹100 to Bob")
        TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
        rec_bits = SignatureStateEncoder.decode_qubits_to_bits(session.reconstructed_qubits)
        rec_hash = SignatureStateEncoder.bits_to_hash_hex(rec_bits)
        self.assertEqual(session.message_hash, rec_hash)

    # -------------------------------------------------------------
    # 19. Ideal channel verification returns VERIFIED
    # -------------------------------------------------------------
    def test_19_ideal_channel_verification_returns_verified(self):
        session = QDSSession("Pay ₹100 to Bob")
        TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
        v_result = QDSVerifier.verify_session(session)
        
        self.assertTrue(v_result["hash_match"])
        self.assertEqual(v_result["total_signature_elements"], 256)
        self.assertEqual(v_result["correctly_reconstructed_elements"], 256)
        self.assertEqual(v_result["verification_accuracy"], 100.0)
        self.assertEqual(v_result["average_fidelity"], 1.0)
        self.assertEqual(v_result["verification_status"], QDSStatus.VERIFIED.value)

    # -------------------------------------------------------------
    # 20. Protocol errors produce explicit failures
    # -------------------------------------------------------------
    def test_20_protocol_errors_produce_explicit_failures(self):
        # Empty message error
        with self.assertRaises(ValueError):
            MessageHasher.hash_message("")

        # Unencoded session verification error
        session = QDSSession("Pay ₹100 to Bob")
        with self.assertRaises(ValueError):
            QDSVerifier.verify_session(session)

if __name__ == "__main__":
    unittest.main()
