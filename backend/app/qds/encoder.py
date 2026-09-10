"""
QDS Signature State Encoder module.
Maps binary bit sequences into independent simulated single-qubit quantum states.
"""
from typing import List, Union
from app.quantum import QubitState

class SignatureStateEncoder:
    """
    Encodes binary bit lists (e.g. 256-bit SHA-256 digest) into a sequence of 
    independent simulated QubitState objects in computational basis {|0⟩, |1⟩}.
    
    Computational Efficiency:
    To prevent exponential memory explosion (O(2^256)), the signature is represented
    as an ordered list of 256 independent 2-dimensional single-qubit state vectors.
    """
    @staticmethod
    def encode_bit(bit: int) -> QubitState:
        """
        Maps single bit integer into QubitState:
        0 -> |0⟩ = [1, 0]ᵀ
        1 -> |1⟩ = [0, 1]ᵀ
        """
        if bit == 0:
            return QubitState.state_0()
        elif bit == 1:
            return QubitState.state_1()
        else:
            raise ValueError(f"Invalid bit value '{bit}'. Expected 0 or 1.")

    @classmethod
    def encode_bits_to_qubits(cls, bits: List[int]) -> List[QubitState]:
        """
        Encodes list of 256 binary bits into 256 QubitState objects.
        """
        if not bits or not isinstance(bits, list):
            raise ValueError("Input bits must be a non-empty list of integers.")
        
        qubits = []
        for i, bit in enumerate(bits):
            if bit not in (0, 1):
                raise ValueError(f"Invalid bit at index {i}: '{bit}'. Only 0 and 1 are supported.")
            qubits.append(cls.encode_bit(bit))
            
        return qubits

    @staticmethod
    def decode_qubit(qubit: QubitState) -> int:
        """
        Decodes a reconstructed single-qubit state into its computational basis bit (0 or 1).
        """
        p0, p1 = qubit.probabilities()
        return 0 if p0 >= p1 else 1

    @classmethod
    def decode_qubits_to_bits(cls, qubits: List[QubitState]) -> List[int]:
        """
        Decodes sequence of reconstructed qubits into list of integers {0, 1}.
        """
        return [cls.decode_qubit(q) for q in qubits]

    @classmethod
    def bits_to_hash_hex(cls, bits: List[int]) -> str:
        """
        Converts a 256-element list of bits back into a 64-character hexadecimal digest string.
        """
        if len(bits) % 8 != 0:
            raise ValueError("Bit length must be a multiple of 8 to convert to hex.")

        byte_list = []
        for i in range(0, len(bits), 8):
            byte_val = 0
            for b in bits[i:i+8]:
                byte_val = (byte_val << 1) | b
            byte_list.append(byte_val)

        return bytes(byte_list).hex()

# Backward compatibility alias
SignatureEncoder = SignatureStateEncoder

