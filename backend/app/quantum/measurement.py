"""
Simulated Projective Measurement Operations for Single and Multi-Qubit Systems.
"""
from typing import Tuple, Dict, Any, Optional
import numpy as np
from app.quantum.constants import EPSILON
from app.quantum.qubit import QubitState

def measure_single_qubit(
    state: QubitState,
    seed: Optional[int] = None,
    rng: Optional[np.random.RandomState] = None
) -> Tuple[int, Dict[str, float], QubitState]:
    """
    Performs projective measurement on a single qubit state |ψ⟩ = α|0⟩ + β|1⟩ in computational basis.
    
    Calculation:
    P(0) = |α|²
    P(1) = |β|²

    Verification:
    Validates P(0) + P(1) ≈ 1.0 within numerical tolerance EPSILON.

    Returns:
    (outcome_bit, probability_distribution_dict, post_measurement_collapsed_state)
    """
    p0, p1 = state.probabilities()

    # Validate sum of probabilities
    prob_sum = p0 + p1
    if not np.isclose(prob_sum, 1.0, atol=EPSILON):
        raise ValueError(f"Measurement probabilities do not sum to 1.0: P(0)+P(1) = {prob_sum}")

    # Controlled random generator for reproducible testing
    if rng is None:
        if seed is not None:
            local_rng = np.random.RandomState(seed)
        else:
            local_rng = np.random.RandomState()
    else:
        local_rng = rng

    outcome_bit = int(local_rng.choice([0, 1], p=[p0, p1]))
    collapsed_state = QubitState.state_0() if outcome_bit == 0 else QubitState.state_1()

    prob_dist = {
        "P(0)": p0,
        "P(1)": p1
    }

    return outcome_bit, prob_dist, collapsed_state

def simulate_alice_teleportation_measurement(
    signature_state: QubitState,
    deterministic: bool = True
) -> Tuple[str, QubitState]:
    """
    Simulates Alice's joint 2-qubit CNOT(S, A) + Hadamard(S) joint Bell measurement on (Signature S, Bell A).
    
    Mathematical breakdown for initial state |ψ⟩_S ⊗ |Φ+⟩_AB:
    (1/2) [ |00⟩_SA (α|0⟩_B + β|1⟩_B) +
            |01⟩_SA (α|1⟩_B + β|0⟩_B) +
            |10⟩_SA (α|0⟩_B - β|1⟩_B) +
            |11⟩_SA (α|1⟩_B - β|0⟩_B) ]
            
    Returns:
    (m1m2_classical_bits, uncorrected_bob_qubit)
    """
    alpha = signature_state.alpha
    beta = signature_state.beta

    bob_pre_correction_states = {
        "00": QubitState(alpha, beta, validate_normalization=False),
        "01": QubitState(beta, alpha, validate_normalization=False),
        "10": QubitState(alpha, -beta, validate_normalization=False),
        "11": QubitState(beta, -alpha, validate_normalization=False)
    }

    possible_bits = ["00", "01", "10", "11"]
    if deterministic:
        selected_bits = "00"
    else:
        selected_bits = str(np.random.choice(possible_bits))

    uncorrected_bob_state = bob_pre_correction_states[selected_bits]
    return selected_bits, uncorrected_bob_state
