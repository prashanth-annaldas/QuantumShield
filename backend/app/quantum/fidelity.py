"""
Quantum State Fidelity and Error Metrics using Complex Inner Products.
"""
from typing import List, Tuple
import numpy as np
from app.quantum.constants import EPSILON
from app.quantum.qubit import QubitState

def calculate_state_fidelity(state_a: QubitState, state_b: QubitState) -> float:
    """
    Computes pure quantum state fidelity:
    F(|ψ⟩, |φ⟩) = |⟨ψ | φ⟩|²

    Mathematical Formulation:
    1. Inner Product ⟨ψ | φ⟩ = ψ^† @ φ = ∑_i ψ_i* φ_i
    2. Absolute magnitude squared: |⟨ψ | φ⟩|²

    Properties:
    - Identical states: F ≈ 1.0
    - Orthogonal states: F ≈ 0.0
    - Global phase equivalent states |φ⟩ = e^(iθ)|ψ⟩: F = |e^(iθ)|^2 * 1 = 1.0
    """
    inner_prod = state_a.inner_product(state_b) # Complex number
    fidelity = float(np.abs(inner_prod) ** 2)
    
    # Clip numerical floating point drift to range [0.0, 1.0]
    if np.isclose(fidelity, 1.0, atol=EPSILON):
        return 1.0
    if np.isclose(fidelity, 0.0, atol=EPSILON):
        return 0.0
    return min(1.0, max(0.0, fidelity))

def calculate_sequence_fidelity(expected_states: List[QubitState], observed_states: List[QubitState]) -> float:
    """
    Computes mean state fidelity F_mean across a list of N qubit states.
    """
    if len(expected_states) != len(observed_states):
        raise ValueError("Expected and observed state list lengths must match.")
    if not expected_states:
        return 1.0

    fidelities = [calculate_state_fidelity(exp, obs) for exp, obs in zip(expected_states, observed_states)]
    return float(np.mean(fidelities))

def calculate_qber(expected_bits: List[int], observed_bits: List[int]) -> Tuple[float, int]:
    """
    Computes Quantum Bit Error Rate (QBER) percentage.
    QBER = (Number of mismatched bits / Total bits) * 100%
    """
    if len(expected_bits) != len(observed_bits):
        raise ValueError("Expected and observed bit sequence lengths must match.")
    if not expected_bits:
        return 0.0, 0

    mismatches = sum(1 for exp, obs in zip(expected_bits, observed_bits) if exp != obs)
    qber_percent = (mismatches / len(expected_bits)) * 100.0
    return qber_percent, mismatches
