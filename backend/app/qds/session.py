"""
QDS Protocol Session Management and Verification Engine.
"""
import uuid
import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional

from app.quantum import QubitState, calculate_sequence_fidelity
from app.qds.hasher import MessageHasher
from app.qds.encoder import SignatureStateEncoder

class QDSStatus(str, Enum):
    CREATED = "CREATED"
    ENCODED = "ENCODED"
    BELL_RESOURCE_READY = "BELL_RESOURCE_READY"
    TELEPORTING = "TELEPORTING"
    TELEPORTED = "TELEPORTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"

class QDSSession:
    """
    Encapsulates a Quantum Digital Signature transaction session and metadata binding:
    1. Message
    2. Cryptographic SHA-256 Digest & Hash Bits
    3. Signature Qubit States
    4. Sender & Receiver Identity
    5. Session UUID
    6. Cryptographically Secure Anti-Replay Nonce
    7. Timezone-aware UTC Timestamp
    8. Session Status State Machine
    """
    def __init__(
        self,
        message: str,
        sender_id: str = "usr-alice",
        receiver_id: str = "usr-bob"
    ):
        if not message or not isinstance(message, str) or len(message.strip()) == 0:
            raise ValueError("Session message cannot be empty or whitespace-only.")

        self.session_id = f"qds-sess-{uuid.uuid4().hex[:12]}"
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message = message
        
        # 1. Hasher
        hash_data = MessageHasher.hash_message(message)
        self.message_hash: str = hash_data["hash_hex"]
        self.hash_bits: str = hash_data["hash_bits"]
        self.expected_bits: List[int] = hash_data["bit_list"]

        # 2. Encoder
        self.expected_qubits: List[QubitState] = SignatureStateEncoder.encode_bits_to_qubits(self.expected_bits)

        # 3. Security Metadata
        self.timestamp: datetime = datetime.now(timezone.utc)
        self.nonce: str = secrets.token_hex(16) # 128-bit secure hex nonce

        # 4. Status Machine & Counters
        self.status: QDSStatus = QDSStatus.ENCODED
        self.verification_attempt_count: int = 0

        # 5. Teleportation Execution Results
        self.classical_bits: List[str] = []
        self.reconstructed_qubits: List[QubitState] = []
        self.per_qubit_results: List[Dict[str, Any]] = []

    def run_teleportation(self, deterministic: bool = True):
        """
        Helper method to execute teleportation on session qubits.
        """
        from app.qds.teleportation import TeleportationProcessor
        return TeleportationProcessor.execute_session_teleportation(self, deterministic=deterministic)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message": self.message,
            "message_hash": self.message_hash,
            "hash_bits": self.hash_bits,
            "nonce": self.nonce,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "total_signature_elements": len(self.expected_qubits),
            "qubit_sample": [q.to_dict() for q in self.expected_qubits[:4]]
        }

class QDSVerifier:
    """
    Evaluates QDS signature verification by comparing original hash vs reconstructed hash
    and evaluating quantum state fidelities.
    """
    @staticmethod
    def verify_session(session: QDSSession) -> Dict[str, Any]:
        """
        Executes verification across teleported signature states.
        """
        if session.status not in (QDSStatus.TELEPORTED, QDSStatus.VERIFIED, QDSStatus.FAILED):
            raise ValueError(f"Cannot verify session in status '{session.status}'. Must be TELEPORTED.")

        if len(session.reconstructed_qubits) != len(session.expected_qubits):
            session.status = QDSStatus.FAILED
            raise ValueError("Reconstructed qubit count does not match expected signature length.")

        # Decode reconstructed qubits to bits and compute reconstructed hash
        reconstructed_bits = SignatureStateEncoder.decode_qubits_to_bits(session.reconstructed_qubits)
        reconstructed_hash = SignatureStateEncoder.bits_to_hash_hex(reconstructed_bits)

        hash_match = (session.message_hash == reconstructed_hash)

        # Count correctly reconstructed bit elements
        correct_count = sum(1 for exp, rec in zip(session.expected_bits, reconstructed_bits) if exp == rec)
        total_elements = len(session.expected_qubits)
        accuracy = (correct_count / total_elements) * 100.0

        # Calculate average fidelity across all 256 qubits
        avg_fidelity = calculate_sequence_fidelity(session.expected_qubits, session.reconstructed_qubits)

        is_verified = hash_match and (accuracy == 100.0) and (avg_fidelity >= 0.99)
        session.status = QDSStatus.VERIFIED if is_verified else QDSStatus.FAILED

        return {
            "session_id": session.session_id,
            "hash_match": hash_match,
            "original_hash": session.message_hash,
            "reconstructed_hash": reconstructed_hash,
            "total_signature_elements": total_elements,
            "correctly_reconstructed_elements": correct_count,
            "average_fidelity": round(avg_fidelity, 6),
            "verification_accuracy": round(accuracy, 2),
            "verification_status": session.status.value
        }
