"""
Bell pair state vector generator for quantum entanglement resource allocation.

TELEPORTATION RESOURCE ROLE:
The maximally entangled Bell state |Φ⁺⟩ = (|00⟩ + |11⟩) / √2 serves as the shared 
quantum resource between Alice and Bob. Alice holds qubit A and Bob holds qubit B.
Without physical transmission of qubit state |ψ⟩ across the channel, joint measurement 
on (Signature S, Bell A) and classical transmission of measurement bits m1m2 allows 
Bob to reconstruct state |ψ⟩ at qubit B via Pauli correction.
"""
from enum import Enum
from typing import Dict
import numpy as np
from app.quantum.constants import EPSILON, is_normalized

class BellType(str, Enum):
    PHI_PLUS = "PHI_PLUS"   # |Φ+⟩ = (|00⟩ + |11⟩) / √2
    PHI_MINUS = "PHI_MINUS" # |Φ-⟩ = (|00⟩ - |11⟩) / √2
    PSI_PLUS = "PSI_PLUS"   # |Ψ+⟩ = (|01⟩ + |10⟩) / √2
    PSI_MINUS = "PSI_MINUS" # |Ψ-⟩ = (|01⟩ - |10⟩) / √2

class BellPair:
    """
    Represents a 2-qubit maximally entangled Bell state vector (4x1 column vector).
    Basis order: |00⟩, |01⟩, |10⟩, |11⟩.
    """
    def __init__(self, bell_type: BellType = BellType.PHI_PLUS):
        inv_sqrt2 = 1.0 / np.sqrt(2.0)
        self.bell_type = bell_type

        if bell_type == BellType.PHI_PLUS:
            # |Φ+⟩ = (|00⟩ + |11⟩) / √2 -> [1/√2, 0, 0, 1/√2]ᵀ
            vec = np.array([[inv_sqrt2], [0.0], [0.0], [inv_sqrt2]], dtype=complex)
        elif bell_type == BellType.PHI_MINUS:
            # |Φ-⟩ = (|00⟩ - |11⟩) / √2 -> [1/√2, 0, 0, -1/√2]ᵀ
            vec = np.array([[inv_sqrt2], [0.0], [0.0], [-inv_sqrt2]], dtype=complex)
        elif bell_type == BellType.PSI_PLUS:
            # |Ψ+⟩ = (|01⟩ + |10⟩) / √2 -> [0, 1/√2, 1/√2, 0]ᵀ
            vec = np.array([[0.0], [inv_sqrt2], [inv_sqrt2], [0.0]], dtype=complex)
        elif bell_type == BellType.PSI_MINUS:
            # |Ψ-⟩ = (|01⟩ - |10⟩) / √2 -> [0, 1/√2, -1/√2, 0]ᵀ
            vec = np.array([[0.0], [inv_sqrt2], [-inv_sqrt2], [0.0]], dtype=complex)
        else:
            raise ValueError(f"Unknown BellType {bell_type}")

        if not is_normalized(vec):
            raise ValueError("Generated Bell pair state is not normalized.")

        self._vector = vec

    @property
    def vector(self) -> np.ndarray:
        """Returns 4x1 complex column vector."""
        return self._vector.copy()

    @property
    def flat_vector(self) -> np.ndarray:
        """Returns 1D complex vector of shape (4,)."""
        return self._vector.flatten()

    def probabilities(self) -> Dict[str, float]:
        """
        Returns basis state probabilities for |00⟩, |01⟩, |10⟩, |11⟩.
        For |Φ+⟩: P(|00⟩) = 0.5, P(|11⟩) = 0.5, P(|01⟩) = 0.0, P(|10⟩) = 0.0.
        """
        probs = np.abs(self.flat_vector) ** 2
        return {
            "00": float(probs[0]),
            "01": float(probs[1]),
            "10": float(probs[2]),
            "11": float(probs[3])
        }

    def __repr__(self) -> str:
        return f"BellPair({self.bell_type.value})"
