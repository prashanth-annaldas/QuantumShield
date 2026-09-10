"""
Cryptographic Message Processing and SHA-256 Digest Encoding.
"""
import hashlib
from typing import Dict, Any, List

class MessageHasher:
    """
    Computes SHA-256 digest of input message and converts digest into binary bit representations.
    
    Security Role in QDS Protocol:
    Binds input message content deterministically to a 256-bit signature state sequence.
    """
    @staticmethod
    def hash_message(message: str) -> Dict[str, Any]:
        """
        Hashes input message and returns message processing payload containing:
        - original message
        - SHA-256 hex string (64 characters)
        - binary bit string (exactly 256 characters)
        - binary bit list (256 integers in {0, 1})
        """
        if not message or not isinstance(message, str) or len(message.strip()) == 0:
            raise ValueError("Input message cannot be empty or whitespace-only.")

        message_bytes = message.encode("utf-8")
        digest_bytes = hashlib.sha256(message_bytes).digest()
        hash_hex = hashlib.sha256(message_bytes).hexdigest()

        # Convert 32 raw digest bytes to a 256-character binary string
        hash_bits = "".join(f"{byte:08b}" for byte in digest_bytes)
        bit_list = [int(b) for b in hash_bits]

        if len(hash_bits) != 256 or len(bit_list) != 256:
            raise ValueError(f"Expected exactly 256 hash bits, got {len(hash_bits)}")

        return {
            "message": message,
            "hash_hex": hash_hex,
            "hash_bits": hash_bits,
            "bit_list": bit_list
        }

# Alias for backward compatibility
QDSMessageHasher = MessageHasher
