"""
Quantum unitary gate operators and multi-qubit tensor product mechanics.

QUBIT ORDERING CONVENTION:
State vectors follow the most-significant-qubit-first (MSB) convention:
|q0 q1 ... qN-1⟩ = |q0⟩ ⊗ |q1⟩ ⊗ ... ⊗ |qN-1⟩
where q0 is the first / most significant qubit (Control for CNOT)
and q1 is the second / least significant qubit (Target for CNOT).

Basis Ordering for 2-Qubit System:
|00⟩ = |0⟩ ⊗ |0⟩ = [1, 0, 0, 0]ᵀ
|01⟩ = |0⟩ ⊗ |1⟩ = [0, 1, 0, 0]ᵀ
|10⟩ = |1⟩ ⊗ |0⟩ = [0, 0, 1, 0]ᵀ
|11⟩ = |1⟩ ⊗ |1⟩ = [0, 0, 0, 1]ᵀ
"""
import numpy as np
from app.quantum.constants import EPSILON, is_equal_approx

# 1-Qubit Identity Matrix
I = np.array([[1.0, 0.0],
              [0.0, 1.0]], dtype=complex)

# Pauli-X (Bit Flip / NOT Gate): X = [[0, 1], [1, 0]]
X = np.array([[0.0, 1.0],
              [1.0, 0.0]], dtype=complex)

# Pauli-Y (Bit & Phase Flip): Y = [[0, -i], [i, 0]]
Y = np.array([[0.0, -1.0j],
              [1.0j, 0.0]], dtype=complex)

# Pauli-Z (Phase Flip): Z = [[1, 0], [0, -1]]
Z = np.array([[1.0, 0.0],
              [0.0, -1.0]], dtype=complex)

# Hadamard Gate H = (1/√2) [[1, 1], [1, -1]]
H = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0],
                                    [1.0, -1.0]], dtype=complex)

# Pauli XZ Operator: Matrix multiplication order X @ Z
# Note: Z is applied first, then X.
# X @ Z = [[0, 1], [1, 0]] @ [[1, 0], [0, -1]] = [[0, -1], [1, 0]]
XZ = X @ Z

# Standard 2-Qubit Controlled-NOT (CNOT) Gate (4x4 Matrix)
# Control qubit = q0 (first qubit), Target qubit = q1 (second qubit)
# Matrix transformation mapping:
# |00⟩ -> |00⟩
# |01⟩ -> |01⟩
# |10⟩ -> |11⟩
# |11⟩ -> |10⟩
CNOT = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 0.0]
], dtype=complex)

def tensor_product(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Computes the Kronecker tensor product A ⊗ B using numpy.kron.
    Used to construct composite multi-qubit state vectors or composite gates.
    """
    return np.kron(a, b)

def is_unitary(matrix: np.ndarray, atol: float = EPSILON) -> bool:
    """
    Verifies that matrix U is unitary: U^† @ U = I.
    """
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        return False
    u_dagger = np.conj(matrix.T)
    identity = np.eye(matrix.shape[0], dtype=complex)
    return is_equal_approx(u_dagger @ matrix, identity, atol=atol)

def get_pauli_correction(measurement_bits: str) -> np.ndarray:
    """
    Returns the corresponding 2x2 Pauli correction matrix for teleportation.
    00 -> Identity (I)
    01 -> Bit Flip (X)
    10 -> Phase Flip (Z)
    11 -> Bit & Phase Flip (XZ)
    """
    mapping = {
        "00": I,
        "01": X,
        "10": Z,
        "11": XZ
    }
    if measurement_bits not in mapping:
        raise ValueError(f"Invalid measurement bits '{measurement_bits}'. Expected '00', '01', '10', or '11'.")
    return mapping[measurement_bits]
