"""
Single-Qubit State Vector Representation in Hilbert space C^2.
"""
from typing import Tuple, Union
import numpy as np
from app.quantum.constants import EPSILON, is_normalized

class QubitState:
    """
    Represents a single qubit state vector in 2D complex Hilbert space C^2:
    |ψ⟩ = α|0⟩ + β|1⟩

    Stored as a 2x1 column vector:
    [ α ]
    [ β ]

    Satisfies normalization condition: |α|² + |β|² = 1.
    """
    def __init__(self, alpha: complex = 1.0, beta: complex = 0.0, validate_normalization: bool = True):
        # Convert input amplitudes to complex column vector shape (2, 1)
        a_comp = complex(alpha)
        b_comp = complex(beta)
        vector = np.array([[a_comp], [b_comp]], dtype=complex)

        # Validate vector shape and non-zero magnitude
        if vector.shape != (2, 1):
            raise ValueError(f"Qubit state vector must have shape (2, 1), got {vector.shape}")

        norm_sq = float(np.abs(a_comp)**2 + np.abs(b_comp)**2)
        if np.isclose(norm_sq, 0.0, atol=EPSILON):
            raise ValueError("Zero-vector cannot represent a valid physical qubit state.")

        # Validate normalization condition if requested
        if validate_normalization and not np.isclose(norm_sq, 1.0, atol=EPSILON):
            raise ValueError(
                f"State vector is not normalized: |α|² + |β|² = {norm_sq:.6f} != 1.0 (Tolerance: {EPSILON})"
            )

        self._vector = vector

    @property
    def alpha(self) -> complex:
        return self._vector[0, 0]

    @property
    def beta(self) -> complex:
        return self._vector[1, 0]

    @property
    def vector(self) -> np.ndarray:
        """
        Returns a copy of the 2x1 complex column vector.
        """
        return self._vector.copy()

    @property
    def flat_vector(self) -> np.ndarray:
        """
        Returns a 1D copy [α, β] of the state vector.
        """
        return self._vector.flatten()

    def apply_gate(self, gate_matrix: np.ndarray) -> "QubitState":
        """
        Applies a 2x2 unitary matrix operation to the qubit state vector: |ψ'⟩ = U |ψ⟩.
        """
        if gate_matrix.shape != (2, 2):
            raise ValueError(f"Gate matrix must be of shape (2, 2), got {gate_matrix.shape}")
        
        new_vec = gate_matrix @ self._vector
        # The result of unitary operation on a normalized state remains normalized
        new_state = QubitState(new_vec[0, 0], new_vec[1, 0], validate_normalization=False)
        return new_state

    def inner_product(self, other: "QubitState") -> complex:
        """
        Computes the complex inner product ⟨self | other⟩ = self^† @ other.
        """
        # conjugate transpose of self (bra vector)
        bra = np.conj(self._vector.T) # 1x2 row vector
        ket = other.vector            # 2x1 column vector
        prod = bra @ ket
        return complex(prod[0, 0])

    def probabilities(self) -> Tuple[float, float]:
        """
        Returns computational basis measurement probabilities:
        P(0) = |α|²
        P(1) = |β|²
        """
        p0 = float(np.abs(self.alpha) ** 2)
        p1 = float(np.abs(self.beta) ** 2)
        return p0, p1

    def to_dict(self) -> dict:
        p0, p1 = self.probabilities()
        return {
            "alpha": {"real": float(self.alpha.real), "imag": float(self.alpha.imag)},
            "beta": {"real": float(self.beta.real), "imag": float(self.beta.imag)},
            "p0": p0,
            "p1": p1
        }

    @classmethod
    def state_0(cls) -> "QubitState":
        """Basis state |0⟩ = [1, 0]ᵀ"""
        return cls(1.0, 0.0)

    @classmethod
    def state_1(cls) -> "QubitState":
        """Basis state |1⟩ = [0, 1]ᵀ"""
        return cls(0.0, 1.0)

    @classmethod
    def state_plus(cls) -> "QubitState":
        """Superposition state |+⟩ = (|0⟩ + |1⟩) / √2 = [1/√2, 1/√2]ᵀ"""
        inv_sqrt2 = 1.0 / np.sqrt(2.0)
        return cls(inv_sqrt2, inv_sqrt2)

    @classmethod
    def state_minus(cls) -> "QubitState":
        """Superposition state |−⟩ = (|0⟩ − |1⟩) / √2 = [1/√2, −1/√2]ᵀ"""
        inv_sqrt2 = 1.0 / np.sqrt(2.0)
        return cls(inv_sqrt2, -inv_sqrt2)

    @classmethod
    def create_normalized(cls, alpha: complex, beta: complex) -> "QubitState":
        """
        Utility constructor that automatically normalizes arbitrary non-zero complex input amplitudes.
        """
        norm = np.sqrt(np.abs(alpha)**2 + np.abs(beta)**2)
        if np.isclose(norm, 0.0, atol=EPSILON):
            raise ValueError("Zero-vector cannot be normalized.")
        return cls(alpha / norm, beta / norm, validate_normalization=False)

    def __repr__(self) -> str:
        return f"QubitState(α={self.alpha:.4f}, β={self.beta:.4f})"
