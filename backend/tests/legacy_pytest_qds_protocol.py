"""
Pytest Unit Test Suite for Phase 3 — Teleportation-Based QDS Protocol.
Contains all 20 mandatory test cases matching Task 11 requirements.
"""
import pytest
from datetime import timezone
import numpy as np

from app.quantum import QubitState, EPSILON, get_pauli_correction
from app.qds import (
    MessageHasher, SignatureStateEncoder, QDSSession,
    QDSVerifier, QDSStatus, TeleportationProcessor
)

def test_01_same_message_same_hash():
    msg = "Pay ₹100 to Bob"
    h1 = MessageHasher.hash_message(msg)
    h2 = MessageHasher.hash_message(msg)
    assert h1["hash_hex"] == h2["hash_hex"]
    assert h1["hash_bits"] == h2["hash_bits"]

def test_02_different_messages_different_hashes():
    h1 = MessageHasher.hash_message("Pay ₹100 to Bob")
    h2 = MessageHasher.hash_message("Pay ₹100 to Alice")
    assert h1["hash_hex"] != h2["hash_hex"]

def test_03_hash_binary_exactly_256_bits():
    h = MessageHasher.hash_message("Pay ₹100 to Bob")
    assert len(h["hash_bits"]) == 256
    assert len(h["bit_list"]) == 256

def test_04_bit_0_encodes_to_state_0():
    state = SignatureStateEncoder.encode_bit(0)
    assert state.alpha == 1.0 and state.beta == 0.0

def test_05_bit_1_encodes_to_state_1():
    state = SignatureStateEncoder.encode_bit(1)
    assert state.alpha == 0.0 and state.beta == 1.0

def test_06_invalid_bits_rejected():
    with pytest.raises(ValueError):
        SignatureStateEncoder.encode_bit(2)

def test_07_unique_session_id():
    s1 = QDSSession("Pay ₹100")
    s2 = QDSSession("Pay ₹100")
    assert s1.session_id != s2.session_id

def test_08_session_nonce_generation():
    s = QDSSession("Pay ₹100")
    assert s.nonce is not None and len(s.nonce) == 32

def test_09_timezone_aware_timestamp():
    s = QDSSession("Pay ₹100")
    assert s.timestamp.tzinfo == timezone.utc

def test_10_teleport_state_0():
    s0 = QubitState.state_0()
    res = TeleportationProcessor.teleport_single_qubit(0, s0, deterministic=True)
    assert np.isclose(res["fidelity"], 1.0, atol=EPSILON)

def test_11_teleport_state_1():
    s1 = QubitState.state_1()
    res = TeleportationProcessor.teleport_single_qubit(0, s1, deterministic=True)
    assert np.isclose(res["fidelity"], 1.0, atol=EPSILON)

def test_12_teleport_state_plus():
    s_plus = QubitState.state_plus()
    res = TeleportationProcessor.teleport_single_qubit(0, s_plus, deterministic=True)
    assert np.isclose(res["fidelity"], 1.0, atol=EPSILON)

def test_13_teleport_state_minus():
    s_minus = QubitState.state_minus()
    res = TeleportationProcessor.teleport_single_qubit(0, s_minus, deterministic=True)
    assert np.isclose(res["fidelity"], 1.0, atol=EPSILON)

def test_14_reconstructed_state_fidelity():
    session = QDSSession("Pay ₹100 to Bob")
    TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
    for res in session.per_qubit_results:
        assert np.isclose(res["fidelity"], 1.0, atol=EPSILON)

def test_15_measurement_outcomes_mapping():
    for bits in ["00", "01", "10", "11"]:
        gate = get_pauli_correction(bits)
        assert gate.shape == (2, 2)

def test_16_teleportation_correction_math_verified():
    state = QubitState(0.6, 0.8)
    for bits in ["00", "01", "10", "11"]:
        bob_pre = {
            "00": QubitState(state.alpha, state.beta, validate_normalization=False),
            "01": QubitState(state.beta, state.alpha, validate_normalization=False),
            "10": QubitState(state.alpha, -state.beta, validate_normalization=False),
            "11": QubitState(state.beta, -state.alpha, validate_normalization=False)
        }[bits]
        reconstructed = bob_pre.apply_gate(get_pauli_correction(bits))
        assert np.isclose(np.abs(state.inner_product(reconstructed))**2, 1.0, atol=EPSILON)

def test_17_multibit_sequence_reconstructed():
    session = QDSSession("Pay ₹100 to Bob")
    TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
    rec_bits = SignatureStateEncoder.decode_qubits_to_bits(session.reconstructed_qubits)
    assert rec_bits == session.expected_bits

def test_18_original_equals_reconstructed_hash():
    session = QDSSession("Pay ₹100 to Bob")
    TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
    rec_bits = SignatureStateEncoder.decode_qubits_to_bits(session.reconstructed_qubits)
    rec_hash = SignatureStateEncoder.bits_to_hash_hex(rec_bits)
    assert session.message_hash == rec_hash

def test_19_ideal_channel_verification_returns_verified():
    session = QDSSession("Pay ₹100 to Bob")
    TeleportationProcessor.execute_session_teleportation(session, deterministic=True)
    v_result = QDSVerifier.verify_session(session)
    assert v_result["hash_match"] is True
    assert v_result["verification_status"] == QDSStatus.VERIFIED.value

def test_20_protocol_errors_produce_explicit_failures():
    with pytest.raises(ValueError):
        MessageHasher.hash_message("")
