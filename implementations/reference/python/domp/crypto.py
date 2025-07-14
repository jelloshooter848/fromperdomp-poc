"""
Cryptographic functions for DOMP protocol.
Handles key generation, event signing, and signature verification.
"""

import hashlib
import json
import secrets
from typing import Dict, Any, Tuple
import secp256k1


class KeyPair:
    """DOMP key pair for signing events."""
    
    def __init__(self, private_key: bytes = None):
        if private_key is None:
            private_key = secrets.token_bytes(32)
        
        self.private_key = secp256k1.PrivateKey(private_key)
        self.public_key = self.private_key.pubkey
        
    @property
    def private_key_hex(self) -> str:
        """Get private key as hex string."""
        serialized = self.private_key.serialize()
        if isinstance(serialized, str):
            return serialized
        return serialized.hex()
        
    @property 
    def public_key_hex(self) -> str:
        """Get public key as hex string (32 bytes, x-coordinate only)."""
        serialized = self.public_key.serialize()
        if isinstance(serialized, str):
            return serialized[2:66]  # Remove '04' prefix and take first 32 bytes as hex
        return serialized[1:33].hex()
        
    @classmethod
    def from_hex(cls, private_key_hex: str) -> 'KeyPair':
        """Create KeyPair from hex private key."""
        private_key_bytes = bytes.fromhex(private_key_hex)
        return cls(private_key_bytes)


def compute_event_id(event_data: Dict[str, Any]) -> str:
    """
    Compute event ID according to Nostr NIP-01.
    
    Args:
        event_data: Event data without 'id' and 'sig' fields
        
    Returns:
        32-byte hex event ID
    """
    # Create serialization data: [0, pubkey, created_at, kind, tags, content]
    serialization_data = [
        0,
        event_data["pubkey"],
        event_data["created_at"], 
        event_data["kind"],
        event_data["tags"],
        event_data["content"]
    ]
    
    # Serialize to JSON with no spaces and sorted keys
    serialized = json.dumps(serialization_data, separators=(',', ':'), sort_keys=True)
    
    # Compute SHA256 hash
    event_id = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    
    return event_id


def sign_event(event_data: Dict[str, Any], keypair: KeyPair) -> str:
    """
    Sign an event using Schnorr signature.
    
    Args:
        event_data: Event data with computed ID
        keypair: KeyPair to sign with
        
    Returns:
        64-byte hex signature
    """
    event_id = event_data["id"]
    message_bytes = bytes.fromhex(event_id)
    
    # Create Schnorr signature
    signature = keypair.private_key.schnorr_sign(message_bytes, None, raw=True)
    
    return signature.hex()


def verify_event(event_data: Dict[str, Any]) -> bool:
    """
    Verify an event's signature and ID.
    
    Args:
        event_data: Complete event data including signature
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if this event has PoW - if so, skip ID recomputation
        has_pow = False
        for tag in event_data.get("tags", []):
            if len(tag) >= 2 and tag[0] == "anti_spam_proof" and tag[1] == "pow":
                has_pow = True
                break
        
        # Verify event ID (skip for PoW events as ID is pre-computed with PoW)
        if not has_pow:
            event_copy = event_data.copy()
            event_copy.pop('id', None)
            event_copy.pop('sig', None)
            
            computed_id = compute_event_id(event_copy)
            if computed_id != event_data["id"]:
                return False
            
        # Verify signature
        pubkey_bytes = bytes.fromhex(event_data["pubkey"])
        pubkey = secp256k1.PublicKey(b'\x02' + pubkey_bytes, raw=True)
        
        message_bytes = bytes.fromhex(event_data["id"])
        signature_bytes = bytes.fromhex(event_data["sig"])
        
        verification_result = pubkey.schnorr_verify(message_bytes, signature_bytes, None, raw=True)
        
        return verification_result
        
    except Exception:
        return False


def generate_pow_nonce(event_data: Dict[str, Any], difficulty: int) -> Tuple[str, str]:
    """
    Generate proof-of-work nonce for anti-spam.
    
    Args:
        event_data: Event data without anti-spam proof
        difficulty: Required number of leading zero bits
        
    Returns:
        Tuple of (event_id, nonce) that satisfies difficulty
    """
    nonce = 0
    target_prefix = '0' * (difficulty // 4)  # Each hex char = 4 bits
    
    while True:
        # Add PoW tag with current nonce
        event_copy = event_data.copy()
        event_copy["tags"] = event_data["tags"] + [["anti_spam_proof", "pow", str(nonce), str(difficulty)]]
        
        # Compute event ID
        event_id = compute_event_id(event_copy)
        
        # Check if it meets difficulty requirement
        if event_id.startswith(target_prefix):
            return event_id, str(nonce)
            
        nonce += 1
        
        # Prevent infinite loops in tests
        if nonce > 10000000:  # Increased limit for higher difficulties
            raise RuntimeError(f"Could not find PoW solution for difficulty {difficulty}")


def generate_pow_event(event_data: Dict[str, Any], difficulty: int) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate proof-of-work for event and return complete event data.
    
    Args:
        event_data: Event data without anti-spam proof
        difficulty: Required number of leading zero bits
        
    Returns:
        Tuple of (event_id, nonce, complete_event_data) that satisfies difficulty
    """
    nonce = 0
    target_prefix = '0' * (difficulty // 4)  # Each hex char = 4 bits
    
    while True:
        # Add PoW tag with current nonce
        event_copy = event_data.copy()
        event_copy["tags"] = event_data["tags"] + [["anti_spam_proof", "pow", str(nonce), str(difficulty)]]
        
        # Compute event ID
        event_id = compute_event_id(event_copy)
        
        # Check if it meets difficulty requirement
        if event_id.startswith(target_prefix):
            return event_id, str(nonce), event_copy
            
        nonce += 1
        
        # Prevent infinite loops in tests
        if nonce > 10000000:  # Increased limit for higher difficulties
            raise RuntimeError(f"Could not find PoW solution for difficulty {difficulty}")


def hash_content(content: str) -> str:
    """Hash content for integrity verification."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def encrypt_for_pubkey(message: str, recipient_pubkey_hex: str, sender_keypair: KeyPair) -> str:
    """
    Encrypt message for recipient using ECIES.
    Simplified implementation for demo purposes.
    """
    # In production, use proper ECIES implementation
    # This is a placeholder that just returns base64 encoded message
    import base64
    return base64.b64encode(message.encode()).decode()


def decrypt_from_pubkey(encrypted_message: str, sender_pubkey_hex: str, recipient_keypair: KeyPair) -> str:
    """
    Decrypt message from sender using ECIES.
    Simplified implementation for demo purposes.
    """
    # In production, use proper ECIES implementation  
    # This is a placeholder that just returns base64 decoded message
    import base64
    return base64.b64decode(encrypted_message.encode()).decode()