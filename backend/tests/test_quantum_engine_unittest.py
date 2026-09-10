"""
Comprehensive Unit Test Suite for Phase 2 — Mathematical Quantum Simulation Engine.
Contains all 18 mandatory test cases matching Task 9 requirements.
"""
import unittest
import numpy as np
from app.quantum import (
    EPSILON, is_equal_approx, QubitState,
    I, X, Y, Z, H, XZ, CNOT, tensor_product, is_unitary,
    BellPair, BellType, measure_single_qubit,
    calculate_state_fidelity
)

class TestQuantumEnginePhase2(unittest.TestCase):

    # -------------------------------------------------------------
    # 1. |0⟩ Normalization
    # -------------------------------------------------------------
    def test_01_state_0_normalization(self):
        s0 = QubitState.state_0()
        norm_sq = np.abs(s0.alpha)**2 + np.abs(s0.beta)**2
        self.assertTrue(np.isclose(norm_sq, 1.0, atol=EPSILON))
        self.assertEqual(s0.alpha, 1.0)
        self.assertEqual(s0.beta, 0.0)

    # -------------------------------------------------------------
    # 2. |1⟩ Normalization
    # -------------------------------------------------------------
    def test_02_state_1_normalization(self):
        s1 = QubitState.state_1()
        norm_sq = np.abs(s1.alpha)**2 + np.abs(s1.beta)**2
        self.assertTrue(np.isclose(norm_sq, 1.0, atol=EPSILON))
        self.assertEqual(s1.alpha, 0.0)
        self.assertEqual(s1.beta, 1.0)

    # -------------------------------------------------------------
    # 3. |+⟩ Normalization
    # -------------------------------------------------------------
    def test_03_state_plus_normalization(self):
        s_plus = QubitState.state_plus()
        norm_sq = np.abs(s_plus.alpha)**2 + np.abs(s_plus.beta)**2
        self.assertTrue(np.isclose(norm_sq, 1.0, atol=EPSILON))
        self.assertTrue(np.isclose(s_plus.alpha, 1.0 / np.sqrt(2.0), atol=EPSILON))
        self.assertTrue(np.isclose(s_plus.beta, 1.0 / np.sqrt(2.0), atol=EPSILON))

    # -------------------------------------------------------------
    # 4. Invalid Qubit Rejection
    # -------------------------------------------------------------
    def test_04_invalid_qubit_rejection(self):
        # Zero vector rejection
        with self.assertRaises(ValueError):
            QubitState(0.0, 0.0)

        # Unnormalized state vector rejection
        with self.assertRaises(ValueError):
            QubitState(2.0, 3.0, validate_normalization=True)

    # -------------------------------------------------------------
    # 5. Pauli-X Transformations
    # -------------------------------------------------------------
    def test_05_pauli_x_transformations(self):
        s0 = QubitState.state_0()
        s1 = QubitState.state_1()

        # X|0⟩ = |1⟩
        x_s0 = s0.apply_gate(X)
        self.assertTrue(np.isclose(x_s0.alpha, 0.0, atol=EPSILON))
        self.assertTrue(np.isclose(x_s0.beta, 1.0, atol=EPSILON))

        # X|1⟩ = |0⟩
        x_s1 = s1.apply_gate(X)
        self.assertTrue(np.isclose(x_s1.alpha, 1.0, atol=EPSILON))
        self.assertTrue(np.isclose(x_s1.beta, 0.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 6. Pauli-Y Transformations
    # -------------------------------------------------------------
    def test_06_pauli_y_transformations(self):
        s0 = QubitState.state_0()
        s1 = QubitState.state_1()

        # Y|0⟩ = i|1⟩ = [0, i]ᵀ
        y_s0 = s0.apply_gate(Y)
        self.assertTrue(np.isclose(y_s0.alpha, 0.0, atol=EPSILON))
        self.assertTrue(np.isclose(y_s0.beta, 1.0j, atol=EPSILON))

        # Y|1⟩ = -i|0⟩ = [-i, 0]ᵀ
        y_s1 = s1.apply_gate(Y)
        self.assertTrue(np.isclose(y_s1.alpha, -1.0j, atol=EPSILON))
        self.assertTrue(np.isclose(y_s1.beta, 0.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 7. Pauli-Z Transformations
    # -------------------------------------------------------------
    def test_07_pauli_z_transformations(self):
        s0 = QubitState.state_0()
        s1 = QubitState.state_1()

        # Z|0⟩ = |0⟩
        z_s0 = s0.apply_gate(Z)
        self.assertTrue(np.isclose(z_s0.alpha, 1.0, atol=EPSILON))
        self.assertTrue(np.isclose(z_s0.beta, 0.0, atol=EPSILON))

        # Z|1⟩ = -|1⟩
        z_s1 = s1.apply_gate(Z)
        self.assertTrue(np.isclose(z_s1.alpha, 0.0, atol=EPSILON))
        self.assertTrue(np.isclose(z_s1.beta, -1.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 8. Hadamard Transformations
    # -------------------------------------------------------------
    def test_08_hadamard_transformations(self):
        s0 = QubitState.state_0()
        s1 = QubitState.state_1()

        # H|0⟩ = |+⟩
        h_s0 = s0.apply_gate(H)
        inv_sqrt2 = 1.0 / np.sqrt(2.0)
        self.assertTrue(np.isclose(h_s0.alpha, inv_sqrt2, atol=EPSILON))
        self.assertTrue(np.isclose(h_s0.beta, inv_sqrt2, atol=EPSILON))

        # H|1⟩ = |−⟩
        h_s1 = s1.apply_gate(H)
        self.assertTrue(np.isclose(h_s1.alpha, inv_sqrt2, atol=EPSILON))
        self.assertTrue(np.isclose(h_s1.beta, -inv_sqrt2, atol=EPSILON))

    # -------------------------------------------------------------
    # 9. Gate Unitarity Checks
    # -------------------------------------------------------------
    def test_09_gate_unitarity_checks(self):
        for gate_matrix, gate_name in [(I, "I"), (X, "X"), (Y, "Y"), (Z, "Z"), (H, "H"), (XZ, "XZ"), (CNOT, "CNOT")]:
            self.assertTrue(is_unitary(gate_matrix, atol=EPSILON), f"Gate {gate_name} failed unitarity test.")

    # -------------------------------------------------------------
    # 10. Tensor Product Correctness
    # -------------------------------------------------------------
    def test_10_tensor_product_correctness(self):
        # |0⟩ ⊗ |1⟩ = [1, 0]ᵀ ⊗ [0, 1]ᵀ = [0, 1, 0, 0]ᵀ = |01⟩
        q0 = QubitState.state_0().vector
        q1 = QubitState.state_1().vector
        prod = tensor_product(q0, q1)
        expected_01 = np.array([[0.0], [1.0], [0.0], [0.0]], dtype=complex)
        self.assertTrue(is_equal_approx(prod, expected_01, atol=EPSILON))

    # -------------------------------------------------------------
    # 11. CNOT Truth Table
    # -------------------------------------------------------------
    def test_11_cnot_truth_table(self):
        v00 = np.array([[1.0], [0.0], [0.0], [0.0]], dtype=complex) # |00⟩
        v01 = np.array([[0.0], [1.0], [0.0], [0.0]], dtype=complex) # |01⟩
        v10 = np.array([[0.0], [0.0], [1.0], [0.0]], dtype=complex) # |10⟩
        v11 = np.array([[0.0], [0.0], [0.0], [1.0]], dtype=complex) # |11⟩

        # |00⟩ -> |00⟩
        self.assertTrue(is_equal_approx(CNOT @ v00, v00, atol=EPSILON))
        # |01⟩ -> |01⟩
        self.assertTrue(is_equal_approx(CNOT @ v01, v01, atol=EPSILON))
        # |10⟩ -> |11⟩
        self.assertTrue(is_equal_approx(CNOT @ v10, v11, atol=EPSILON))
        # |11⟩ -> |10⟩
        self.assertTrue(is_equal_approx(CNOT @ v11, v10, atol=EPSILON))

    # -------------------------------------------------------------
    # 12. Bell Pair Normalization
    # -------------------------------------------------------------
    def test_12_bell_pair_normalization(self):
        bp = BellPair(BellType.PHI_PLUS)
        norm = np.linalg.norm(bp.vector)
        self.assertTrue(np.isclose(norm, 1.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 13. Bell Pair Probabilities
    # -------------------------------------------------------------
    def test_13_bell_pair_probabilities(self):
        bp = BellPair(BellType.PHI_PLUS)
        probs = bp.probabilities()
        self.assertTrue(np.isclose(probs["00"], 0.5, atol=EPSILON))
        self.assertTrue(np.isclose(probs["11"], 0.5, atol=EPSILON))
        self.assertTrue(np.isclose(probs["01"], 0.0, atol=EPSILON))
        self.assertTrue(np.isclose(probs["10"], 0.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 14. Measurement Probabilities
    # -------------------------------------------------------------
    def test_14_measurement_probabilities(self):
        # Arbitrary normalized state: α=0.6, β=0.8
        state = QubitState(0.6, 0.8)
        _, prob_dist, _ = measure_single_qubit(state, seed=42)
        self.assertTrue(np.isclose(prob_dist["P(0)"], 0.36, atol=EPSILON))
        self.assertTrue(np.isclose(prob_dist["P(1)"], 0.64, atol=EPSILON))

    # -------------------------------------------------------------
    # 15. Measurement Reproducibility Using Seeds
    # -------------------------------------------------------------
    def test_15_measurement_reproducibility_using_seeds(self):
        state = QubitState.state_plus() # P(0)=0.5, P(1)=0.5
        
        # Run measurements with seed 12345
        outcome1, _, _ = measure_single_qubit(state, seed=12345)
        outcome2, _, _ = measure_single_qubit(state, seed=12345)
        self.assertEqual(outcome1, outcome2)

    # -------------------------------------------------------------
    # 16. Fidelity of Identical States
    # -------------------------------------------------------------
    def test_16_fidelity_identical_states(self):
        s0 = QubitState.state_0()
        s_plus = QubitState.state_plus()
        self.assertTrue(np.isclose(calculate_state_fidelity(s0, s0), 1.0, atol=EPSILON))
        self.assertTrue(np.isclose(calculate_state_fidelity(s_plus, s_plus), 1.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 17. Fidelity of Orthogonal States
    # -------------------------------------------------------------
    def test_17_fidelity_orthogonal_states(self):
        s0 = QubitState.state_0()
        s1 = QubitState.state_1()
        s_plus = QubitState.state_plus()
        s_minus = QubitState.state_minus()

        # F(|0⟩, |1⟩) = 0
        self.assertTrue(np.isclose(calculate_state_fidelity(s0, s1), 0.0, atol=EPSILON))
        # F(|+⟩, |−⟩) = 0
        self.assertTrue(np.isclose(calculate_state_fidelity(s_plus, s_minus), 0.0, atol=EPSILON))

    # -------------------------------------------------------------
    # 18. Fidelity Under Global Phase
    # -------------------------------------------------------------
    def test_18_fidelity_global_phase(self):
        # |ψ⟩ = |+⟩
        psi = QubitState.state_plus()

        # Apply global phase e^(iθ) where θ = π/3
        theta = np.pi / 3.0
        phase_factor = np.exp(1.0j * theta)
        phi = QubitState(psi.alpha * phase_factor, psi.beta * phase_factor, validate_normalization=False)

        fidelity = calculate_state_fidelity(psi, phi)
        self.assertTrue(np.isclose(fidelity, 1.0, atol=EPSILON))

if __name__ == "__main__":
    unittest.main()
