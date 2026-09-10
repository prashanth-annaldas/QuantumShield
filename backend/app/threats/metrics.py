"""
Quantum Threat Metrics — Deterministic, Non-AI Statistical Calculations.

Provides:
  - calculate_statistical_deviation   : Deviation of observed bits from expected
  - calculate_forgery_probability     : Deterministic estimate of signature forgery likelihood
  - compute_all_metrics               : Aggregated metrics dictionary for a QDS session

All calculations are purely mathematical (NumPy). No AI / ML / external models.
"""
from typing import List, Dict, Tuple
import numpy as np
from app.quantum import QubitState, calculate_state_fidelity


# ---------------------------------------------------------------------------
# Statistical Deviation
# ---------------------------------------------------------------------------

def calculate_statistical_deviation(
    expected_bits: List[int],
    observed_bits: List[int]
) -> float:
    """
    Computes the **normalised statistical deviation** between expected and observed
    bit sequences.

    Mathematical Formulation:
      Let N = number of bits.
      Let M = number of mismatched positions (Hamming distance).
      Let p_err = M / N          (observed bit-error proportion)
      Let p_expected = 0.0       (ideal noise-free channel has 0 errors)
      deviation = |p_err - p_expected| = p_err

    Return value is in [0.0, 1.0]:
      0.0 → perfect match (no deviation)
      1.0 → every bit differs (maximum deviation)

    Args:
        expected_bits: Ground-truth bit list (e.g. from SHA-256 hash).
        observed_bits: Observed/decoded bit list from reconstructed qubits.

    Returns:
        Normalised deviation in range [0.0, 1.0].

    Raises:
        ValueError: If list lengths differ.
    """
    if len(expected_bits) != len(observed_bits):
        raise ValueError(
            f"Bit list lengths must match. "
            f"Expected {len(expected_bits)}, got {len(observed_bits)}."
        )
    if not expected_bits:
        return 0.0

    expected_arr = np.array(expected_bits, dtype=np.int8)
    observed_arr = np.array(observed_bits, dtype=np.int8)

    n_mismatch = int(np.sum(expected_arr != observed_arr))
    deviation = n_mismatch / len(expected_bits)

    # Clip for floating-point safety
    return float(np.clip(deviation, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Forgery Probability
# ---------------------------------------------------------------------------

def calculate_forgery_probability(
    mean_fidelity: float,
    qber_percent: float,
    mismatch_rate: float,
    statistical_deviation: float,
    *,
    # Thresholds (match SecurityThresholds)
    min_fidelity: float = 0.95,
    max_qber_percent: float = 5.0,
    max_mismatch_rate: float = 0.05,
) -> float:
    """
    Computes a **deterministic, score-based forgery probability** in [0.0, 1.0].

    Algorithm (no AI/ML):
      Each metric contributes a weighted penalty score when it breaches a threshold:

      Fidelity penalty  = max(0, (min_fidelity - mean_fidelity) / min_fidelity)
                          Weighted by 0.40 — primary quantum integrity signal.

      QBER penalty      = min(1, qber_percent / 100.0) 
                          (QBER is already a percentage, normalise to [0,1])
                          Weighted by 0.35 — quantum bit-error signal.

      Mismatch penalty  = max(0, (mismatch_rate - max_mismatch_rate) / (1 - max_mismatch_rate))
                          Weighted by 0.15 — state-level agreement.

      Deviation penalty = statistical_deviation
                          Weighted by 0.10 — supplementary bit-sequence signal.

      forgery_probability = clip(Σ weighted_penalties, 0.0, 1.0)

    Interpretation:
      ≥ 0.50   → High probability of forgery.
      0.10–0.49 → Marginal / borderline anomaly.
      < 0.10   → Very unlikely to be a forged signature.

    Args:
        mean_fidelity:        Mean quantum state fidelity across all qubits [0.0, 1.0].
        qber_percent:         Quantum bit-error rate as a percentage [0.0, 100.0].
        mismatch_rate:        Fraction of mismatched qubit states [0.0, 1.0].
        statistical_deviation: Normalised bit-sequence deviation [0.0, 1.0].
        min_fidelity:         Minimum acceptable fidelity threshold.
        max_qber_percent:     Maximum acceptable QBER threshold (percent).
        max_mismatch_rate:    Maximum acceptable mismatch rate threshold.

    Returns:
        Forgery probability in [0.0, 1.0].
    """
    # --- Fidelity penalty (40% weight) ---
    if mean_fidelity >= min_fidelity:
        fidelity_penalty = 0.0
    else:
        fidelity_penalty = (min_fidelity - mean_fidelity) / min_fidelity

    # --- QBER penalty (35% weight) ---
    # Normalise raw percentage to [0, 1]; beyond 100% is impossible but clip for safety
    qber_norm = float(np.clip(qber_percent / 100.0, 0.0, 1.0))
    qber_penalty = qber_norm  # Full range contributes

    # --- Mismatch rate penalty (15% weight) ---
    if mismatch_rate <= max_mismatch_rate:
        mismatch_penalty = 0.0
    else:
        range_above = 1.0 - max_mismatch_rate
        mismatch_penalty = (mismatch_rate - max_mismatch_rate) / range_above if range_above > 0 else 1.0

    # --- Statistical deviation penalty (10% weight) ---
    deviation_penalty = float(np.clip(statistical_deviation, 0.0, 1.0))

    # --- Weighted sum ---
    forgery_prob = (
        0.40 * fidelity_penalty +
        0.35 * qber_penalty +
        0.15 * mismatch_penalty +
        0.10 * deviation_penalty
    )

    return float(np.clip(forgery_prob, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Convenience aggregator
# ---------------------------------------------------------------------------

def compute_all_metrics(
    expected_bits: List[int],
    observed_bits: List[int],
    mean_fidelity: float,
    qber_percent: float,
    mismatch_rate: float,
) -> Dict[str, float]:
    """
    Computes and returns all Phase 4 threat metrics as a dictionary.

    Args:
        expected_bits:   Ground-truth bit list.
        observed_bits:   Observed/decoded bit list.
        mean_fidelity:   Mean qubit state fidelity.
        qber_percent:    Quantum bit-error rate (%).
        mismatch_rate:   Fraction of mismatched states.

    Returns:
        Dictionary with keys:
          - 'statistical_deviation'  [0.0, 1.0]
          - 'forgery_probability'    [0.0, 1.0]
    """
    stat_dev = calculate_statistical_deviation(expected_bits, observed_bits)
    forgery_prob = calculate_forgery_probability(
        mean_fidelity=mean_fidelity,
        qber_percent=qber_percent,
        mismatch_rate=mismatch_rate,
        statistical_deviation=stat_dev,
    )
    return {
        "statistical_deviation": round(stat_dev, 4),
        "forgery_probability": round(forgery_prob, 4),
    }
