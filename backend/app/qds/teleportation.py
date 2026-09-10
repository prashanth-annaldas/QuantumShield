"""
Teleportation Processor for Quantum Digital Signature (QDS) Protocol.

THREE-QUBIT TELEPORTATION SYSTEM ORDER & MATHEMATICAL CONVENTION:
The composite 3-qubit state space is ordered as:
|q0 q1 q2⟩ = |q0⟩ ⊗ |q1⟩ ⊗ |q2⟩
where:
- q0 = Signature Qubit |ψ⟩_S (Held by Alice)
- q1 = Alice's Bell Pair Qubit |A⟩ (Held by Alice)
- q2 = Bob's Bell Pair Qubit |B⟩ (Held by Bob)

Resource State:
Alice and Bob share maximally entangled Bell Pair |Φ⁺⟩_AB = (|00⟩ + |11⟩) / √2.
Initial system state: |Ψ0⟩ = |ψ⟩_S ⊗ |Φ⁺⟩_AB.

Alice Operations:
Step 1: CNOT gate with Control = q0 (Signature) and Target = q1 (Alice Bell).
Step 2: Hadamard gate H on q0 (Signature).
Step 3: Projective measurement on (q0, q1) yielding classical bits m1m2 ∈ {00, 01, 10, 11}.

Bob Pauli Correction Mapping:
00 -> Identity (I)
01 -> Pauli-X (Bit Flip)
10 -> Pauli-Z (Phase Flip)
11 -> Pauli-XZ (Bit & Phase Flip, where XZ = X @ Z)
"""
from typing import List, Dict, Any, Optional
import numpy as np

from app.quantum import (
    QubitState, BellPair, BellType, get_pauli_correction,
    simulate_alice_teleportation_measurement, calculate_state_fidelity
)
from app.qds.session import QDSSession, QDSStatus

class TeleportationProcessor:
    """
    Simulates teleportation-based transmission of signature qubits from Alice to Bob.
    """
    @staticmethod
    def teleport_single_qubit(
        qubit_index: int,
        signature_state: QubitState,
        deterministic: bool = True
    ) -> Dict[str, Any]:
        """
        Executes 3-qubit teleportation for a single signature qubit |ψ⟩.
        Returns detailed execution record including classical bits, Pauli correction, reconstructed state, and fidelity.
        """
        if not isinstance(signature_state, QubitState):
            raise ValueError("Input signature state must be a valid QubitState instance.")

        # Step 1: Generate Bell pair entanglement resource |Φ⁺⟩
        bell_pair = BellPair(BellType.PHI_PLUS)

        # Step 2: Alice performs joint CNOT + Hadamard measurement on (q0, q1) -> classical bits m1m2
        m1m2, uncorrected_bob_state = simulate_alice_teleportation_measurement(
            signature_state, deterministic=deterministic
        )

        # Step 3: Bob receives m1m2 and applies designated Pauli correction U_B
        pauli_matrix = get_pauli_correction(m1m2)
        reconstructed_state = uncorrected_bob_state.apply_gate(pauli_matrix)

        # Step 4: Calculate state transfer fidelity F(|ψ_exp⟩, |ψ_rec⟩)
        fidelity = calculate_state_fidelity(signature_state, reconstructed_state)

        pauli_names = {
            "00": "I",
            "01": "X",
            "10": "Z",
            "11": "XZ"
        }

        return {
            "qubit_index": qubit_index,
            "original_state": signature_state,
            "measurement_bits": m1m2,
            "pauli_correction": pauli_names[m1m2],
            "reconstructed_state": reconstructed_state,
            "fidelity": round(fidelity, 6)
        }

    @classmethod
    def execute_session_teleportation(
        cls,
        session: QDSSession,
        deterministic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes sequential teleportation across all 256 signature qubits in a QDS session.
        """
        if not session or not isinstance(session, QDSSession):
            raise ValueError("Invalid QDS session provided.")

        session.status = QDSStatus.TELEPORTING
        classical_bits_list = []
        reconstructed_qubits = []
        per_qubit_results = []

        for idx, sig_qubit in enumerate(session.expected_qubits):
            result = cls.teleport_single_qubit(idx, sig_qubit, deterministic=deterministic)
            
            classical_bits_list.append(result["measurement_bits"])
            reconstructed_qubits.append(result["reconstructed_state"])
            per_qubit_results.append(result)

        session.classical_bits = classical_bits_list
        session.reconstructed_qubits = reconstructed_qubits
        session.per_qubit_results = per_qubit_results
        session.status = QDSStatus.TELEPORTED

        return per_qubit_results

    @classmethod
    def generate_teleportation_trace(
        cls,
        session: QDSSession,
        trace_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generates an explainable human-readable trace for demonstration subset of first N signature qubits.
        """
        if not session.per_qubit_results:
            cls.execute_session_teleportation(session, deterministic=True)

        trace = []
        limit = min(trace_count, len(session.per_qubit_results))

        for i in range(limit):
            res = session.per_qubit_results[i]
            bit_val = session.expected_bits[i]
            orig_state_str = "|0⟩" if bit_val == 0 else "|1⟩"
            rec_bit = 0 if res["reconstructed_state"].probabilities()[0] >= 0.5 else 1
            rec_state_str = "|0⟩" if rec_bit == 0 else "|1⟩"

            trace.append({
                "qubit_index": i,
                "message_bit": bit_val,
                "signature_state": orig_state_str,
                "bell_pair": "(|00⟩ + |11⟩)/√2",
                "alice_operations": ["CNOT(q0, q1)", "Hadamard(q0)", "Measurement(q0, q1)"],
                "measurement_bits": res["measurement_bits"],
                "bob_pauli_correction": res["pauli_correction"],
                "reconstructed_state": rec_state_str,
                "fidelity": res["fidelity"]
            })

        return trace
