"""
Attack Injection Simulator for QDS framework.
Used to inject forgery, impersonation, replay, quantum channel noise, and rate limit violations.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from app.quantum import QubitState, X, Z
from app.qds import QDSSession

class AttackType(str):
    NONE = "NONE"
    SIGNATURE_FORGERY = "SIGNATURE_FORGERY"
    IMPERSONATION_ATTACK = "IMPERSONATION_ATTACK"
    REPLAY_ATTACK = "REPLAY_ATTACK"
    QUANTUM_CHANNEL_MANIPULATION = "QUANTUM_CHANNEL_MANIPULATION"
    UNAUTHORIZED_VERIFICATION = "UNAUTHORIZED_VERIFICATION"

class AttackSimulator:
    """
    Injects synthetic security attacks into a QDSSession payload for observation testing.
    """
    @staticmethod
    def inject_forgery(session: QDSSession, tamper_ratio: float = 0.15) -> Dict[str, Any]:
        """
        Tampers with a fraction of Bob's reconstructed qubits to simulate forgery/tampering.
        """
        n_tamper = max(1, int(len(session.reconstructed_qubits) * tamper_ratio))
        tamper_indices = np.random.choice(len(session.reconstructed_qubits), size=n_tamper, replace=False)
        
        for idx in tamper_indices:
            # Apply bit-flip X gate to simulate state alteration
            session.reconstructed_qubits[idx] = session.reconstructed_qubits[idx].apply_gate(X)
            
        return {
            "attack_type": AttackType.SIGNATURE_FORGERY,
            "tamper_count": n_tamper,
            "tamper_indices": tamper_indices.tolist()
        }

    @staticmethod
    def inject_quantum_channel_noise(session: QDSSession, error_rate: float = 0.12) -> Dict[str, Any]:
        """
        Applies random bit flips or phase flips to simulate decoherence/eavesdropping noise.
        """
        n_noisy = max(1, int(len(session.reconstructed_qubits) * error_rate))
        noisy_indices = np.random.choice(len(session.reconstructed_qubits), size=n_noisy, replace=False)

        for idx in noisy_indices:
            gate = X if np.random.rand() > 0.5 else Z
            session.reconstructed_qubits[idx] = session.reconstructed_qubits[idx].apply_gate(gate)

        return {
            "attack_type": AttackType.QUANTUM_CHANNEL_MANIPULATION,
            "noise_count": n_noisy,
            "error_rate": error_rate
        }

    @staticmethod
    def inject_impersonation(session: QDSSession) -> Dict[str, Any]:
        """
        Simulates an impersonated sender by corrupting sender ID signature token.
        """
        session.sender_id = "usr-impostor-999"
        return {
            "attack_type": AttackType.IMPERSONATION_ATTACK,
            "fake_sender": "usr-impostor-999"
        }

    @staticmethod
    def inject_replay_attack(session: QDSSession, time_offset_seconds: float = 600.0) -> Dict[str, Any]:
        """
        Simulates replay attack by setting expired timestamp or re-using active nonce.
        """
        from datetime import timedelta
        if hasattr(session.timestamp, "timestamp"):
            session.timestamp = session.timestamp - timedelta(seconds=time_offset_seconds)
        else:
            session.timestamp -= int(time_offset_seconds * 1000)
            
        return {
            "attack_type": AttackType.REPLAY_ATTACK,
            "time_offset_seconds": time_offset_seconds
        }

    @staticmethod
    def inject_unauthorized_attempts(session: QDSSession, extra_attempts: int = 5) -> Dict[str, Any]:
        """
        Exceeds maximum allowable verification attempts.
        """
        session.verification_attempt_count += extra_attempts
        return {
            "attack_type": AttackType.UNAUTHORIZED_VERIFICATION,
            "attempt_count": session.verification_attempt_count
        }
