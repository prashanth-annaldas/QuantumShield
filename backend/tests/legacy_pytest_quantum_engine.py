"""
Pytest Unit Test Suite for Phase 2 — Mathematical Quantum Simulation Engine.
Contains all 18 mandatory test cases matching Task 9 requirements.
"""
import pytest
import numpy as np
from app.quantum import (
    EPSILON, is_equal_approx, QubitState,
    I, X, Y, Z, H, XZ, CNOT, tensor_product, is_unitary,
    BellPair, BellType, measure_single_qubit,
    calculate_state_fidelity
)

def test_01_state_0_normalization():
    s0 = QubitState.state_0()
    norm_sq = np.abs(s0.alpha)**2 + np.abs(s0.beta)**2
    assert np.isclose(norm_sq, 1.0, atol=EPSILON)
    assert s0.alpha == 1.0 and s0.beta == 0.0

def test_02_state_1_normalization():
    s1 = QubitState.state_1()
    norm_sq = np.abs(s1.alpha)**2 + np.abs(s1.beta)**2
    assert np.isclose(norm_sq, 1.0, atol=EPSILON)
    assert s1.alpha == 0.0 and s1.beta == 1.0

def test_03_state_plus_normalization():
    s_plus = QubitState.state_plus()
    norm_sq = np.abs(s_plus.alpha)**2 + np.abs(s_plus.beta)**2
    assert np.isclose(norm_sq, 1.0, atol=EPSILON)
    assert np.isclose(s_plus.alpha, 1.0 / np.sqrt(2.0), atol=EPSILON)
    assert np.isclose(s_plus.beta, 1.0 / np.sqrt(2.0), atol=EPSILON)

def test_04_invalid_qubit_rejection():
    with pytest.raises(ValueError):
        QubitState(0.0, 0.0)
    with pytest.raises(ValueError):
        QubitState(2.0, 3.0, validate_normalization=True)

def test_05_pauli_x_transformations():
    s0 = QubitState.state_0()
    s1 = QubitState.state_1()
    x_s0 = s0.apply_gate(X)
    assert np.isclose(x_s0.alpha, 0.0, atol=EPSILON) and np.isclose(x_s0.beta, 1.0, atol=EPSILON)
    x_s1 = s1.apply_gate(X)
    assert np.isclose(x_s1.alpha, 1.0, atol=EPSILON) and np.isclose(x_s1.beta, 0.0, atol=EPSILON)

def test_06_pauli_y_transformations():
    s0 = QubitState.state_0()
    s1 = QubitState.state_1()
    y_s0 = s0.apply_gate(Y)
    assert np.isclose(y_s0.alpha, 0.0, atol=EPSILON) and np.isclose(y_s0.beta, 1.0j, atol=EPSILON)
    y_s1 = s1.apply_gate(Y)
    assert np.isclose(y_s1.alpha, -1.0j, atol=EPSILON) and np.isclose(y_s1.beta, 0.0, atol=EPSILON)

def test_07_pauli_z_transformations():
    s0 = QubitState.state_0()
    s1 = QubitState.state_1()
    z_s0 = s0.apply_gate(Z)
    assert np.isclose(z_s0.alpha, 1.0, atol=EPSILON) and np.isclose(z_s0.beta, 0.0, atol=EPSILON)
    z_s1 = s1.apply_gate(Z)
    assert np.isclose(z_s1.alpha, 0.0, atol=EPSILON) and np.isclose(z_s1.beta, -1.0, atol=EPSILON)

def test_08_hadamard_transformations():
    s0 = QubitState.state_0()
    s1 = QubitState.state_1()
    inv_sqrt2 = 1.0 / np.sqrt(2.0)
    h_s0 = s0.apply_gate(H)
    assert np.isclose(h_s0.alpha, inv_sqrt2, atol=EPSILON) and np.isclose(h_s0.beta, inv_sqrt2, atol=EPSILON)
    h_s1 = s1.apply_gate(H)
    assert np.isclose(h_s1.alpha, inv_sqrt2, atol=EPSILON) and np.isclose(h_s1.beta, -inv_sqrt2, atol=EPSILON)

def test_09_gate_unitarity_checks():
    for gate_matrix in [I, X, Y, Z, H, XZ, CNOT]:
        assert is_unitary(gate_matrix, atol=EPSILON)

def test_10_tensor_product_correctness():
    q0 = QubitState.state_0().vector
    q1 = QubitState.state_1().vector
    prod = tensor_product(q0, q1)
    expected_01 = np.array([[0.0], [1.0], [0.0], [0.0]], dtype=complex)
    assert is_equal_approx(prod, expected_01, atol=EPSILON)

def test_11_cnot_truth_table():
    v00 = np.array([[1.0], [0.0], [0.0], [0.0]], dtype=complex)
    v01 = np.array([[0.0], [1.0], [0.0], [0.0]], dtype=complex)
    v10 = np.array([[0.0], [0.0], [1.0], [0.0]], dtype=complex)
    v11 = np.array([[0.0], [0.0], [0.0], [1.0]], dtype=complex)

    assert is_equal_approx(CNOT @ v00, v00, atol=EPSILON)
    assert is_equal_approx(CNOT @ v01, v01, atol=EPSILON)
    assert is_equal_approx(CNOT @ v10, v11, atol=EPSILON)
    assert is_equal_approx(CNOT @ v11, v10, atol=EPSILON)

def test_12_bell_pair_normalization():
    bp = BellPair(BellType.PHI_PLUS)
    norm = np.linalg.norm(bp.vector)
    assert np.isclose(norm, 1.0, atol=EPSILON)

def test_13_bell_pair_probabilities():
    bp = BellPair(BellType.PHI_PLUS)
    probs = bp.probabilities()
    assert np.isclose(probs["00"], 0.5, atol=EPSILON)
    assert np.isclose(probs["11"], 0.5, atol=EPSILON)
    assert np.isclose(probs["01"], 0.0, atol=EPSILON)
    assert np.isclose(probs["10"], 0.0, atol=EPSILON)

def test_14_measurement_probabilities():
    state = QubitState(0.6, 0.8)
    _, prob_dist, _ = measure_single_qubit(state, seed=42)
    assert np.isclose(prob_dist["P(0)"], 0.36, atol=EPSILON)
    assert np.isclose(prob_dist["P(1)"], 0.64, atol=EPSILON)

def test_15_measurement_reproducibility_using_seeds():
    state = QubitState.state_plus()
    outcome1, _, _ = measure_single_qubit(state, seed=12345)
    outcome2, _, _ = measure_single_qubit(state, seed=12345)
    assert outcome1 == outcome2

def test_16_fidelity_identical_states():
    s0 = QubitState.state_0()
    s_plus = QubitState.state_plus()
    assert np.isclose(calculate_state_fidelity(s0, s0), 1.0, atol=EPSILON)
    assert np.isclose(calculate_state_fidelity(s_plus, s_plus), 1.0, atol=EPSILON)

def test_17_fidelity_orthogonal_states():
    s0 = QubitState.state_0()
    s1 = QubitState.state_1()
    assert np.isclose(calculate_state_fidelity(s0, s1), 0.0, atol=EPSILON)

def test_18_fidelity_global_phase():
    psi = QubitState.state_plus()
    phase_factor = np.exp(1.0j * (np.pi / 3.0))
    phi = QubitState(psi.alpha * phase_factor, psi.beta * phase_factor, validate_normalization=False)
    fidelity = calculate_state_fidelity(psi, phi)
    assert np.isclose(fidelity, 1.0, atol=EPSILON)
