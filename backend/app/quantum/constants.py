"""
Shared numerical constants and tolerance configurations for Quantum Simulation Engine.
"""
import numpy as np

# Shared numerical floating point tolerance
EPSILON: float = 1e-10
ATOL: float = 1e-10

def is_normalized(vector: np.ndarray, atol: float = ATOL) -> bool:
    """
    Checks if a state vector norm satisfies ||v||^2 = 1.0 within tolerance.
    """
    norm_sq = np.sum(np.abs(vector) ** 2)
    return bool(np.isclose(norm_sq, 1.0, atol=atol))

def is_equal_approx(a: np.ndarray, b: np.ndarray, atol: float = ATOL) -> bool:
    """
    Tolerance-aware array equality comparison using numpy.allclose.
    """
    return bool(np.allclose(a, b, atol=atol))
