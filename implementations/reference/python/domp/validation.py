"""
Event validation for DOMP protocol.
Validates events against JSON schemas and protocol rules.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import jsonschema
from .crypto import verify_event


# Load JSON schemas
def load_schemas() -> Dict[int, Dict[str, Any]]:
    """Load event schemas from specs directory."""
    schemas = {}
    
    # Find specs directory (relative to this file)
    current_dir = Path(__file__).parent
    specs_dir = current_dir.parent.parent.parent.parent / "specs" / "event-schemas"
    
    if not specs_dir.exists():
        # Fallback to embedded schemas for distribution
        return _get_embedded_schemas()
    
    for schema_file in specs_dir.glob("kind-*.json"):
        kind = int(schema_file.stem.split('-')[1])
        with open(schema_file) as f:
            schemas[kind] = json.load(f)
    
    return schemas


def _get_embedded_schemas() -> Dict[int, Dict[str, Any]]:
    """Embedded schemas for when specs directory is not available."""
    return {
        300: {
            "type": "object",
            "required": ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"],
            "properties": {
                "kind": {"const": 300},
                "tags": {
                    "type": "array",
                    "contains": {
                        "type": "array",
                        "items": [{"const": "anti_spam_proof"}],
                        "minItems": 2
                    }
                }
            }
        },
        301: {
            "type": "object", 
            "required": ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"],
            "properties": {
                "kind": {"const": 301}
            }
        },
        303: {
            "type": "object",
            "required": ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"], 
            "properties": {
                "kind": {"const": 303}
            }
        },
        311: {
            "type": "object",
            "required": ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"],
            "properties": {
                "kind": {"const": 311}
            }
        },
        313: {
            "type": "object",
            "required": ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"],
            "properties": {
                "kind": {"const": 313}
            }
        }
    }


SCHEMAS = load_schemas()


class ValidationError(Exception):
    """Event validation error."""
    pass


def validate_event(event_data: Dict[str, Any], check_signature: bool = True) -> bool:
    """
    Validate a DOMP event.
    
    Args:
        event_data: Event data to validate
        check_signature: Whether to verify cryptographic signature
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If event is invalid
    """
    try:
        # Basic structure validation
        _validate_event_structure(event_data)
        
        # Schema validation
        _validate_event_schema(event_data)
        
        # Content validation
        _validate_event_content(event_data)
        
        # Anti-spam validation
        _validate_anti_spam(event_data)
        
        # Cryptographic validation
        if check_signature:
            _validate_signature(event_data)
            
        return True
        
    except Exception as e:
        raise ValidationError(f"Event validation failed: {str(e)}")


def _validate_event_structure(event_data: Dict[str, Any]) -> None:
    """Validate basic event structure."""
    required_fields = ["id", "pubkey", "created_at", "kind", "tags", "content", "sig"]
    
    for field in required_fields:
        if field not in event_data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate field types
    if not isinstance(event_data["id"], str) or len(event_data["id"]) != 64:
        raise ValidationError("Invalid event ID format")
        
    if not isinstance(event_data["pubkey"], str) or len(event_data["pubkey"]) != 64:
        raise ValidationError("Invalid pubkey format")
        
    if not isinstance(event_data["created_at"], int):
        raise ValidationError("created_at must be integer timestamp")
        
    if not isinstance(event_data["kind"], int):
        raise ValidationError("kind must be integer")
        
    if not isinstance(event_data["tags"], list):
        raise ValidationError("tags must be array")
        
    if not isinstance(event_data["content"], str):
        raise ValidationError("content must be string")
        
    if not isinstance(event_data["sig"], str) or len(event_data["sig"]) != 128:
        raise ValidationError("Invalid signature format")


def _validate_event_schema(event_data: Dict[str, Any]) -> None:
    """Validate event against JSON schema."""
    kind = event_data["kind"]
    
    if kind not in SCHEMAS:
        raise ValidationError(f"Unsupported event kind: {kind}")
        
    try:
        jsonschema.validate(event_data, SCHEMAS[kind])
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Schema validation failed: {e.message}")


def _validate_event_content(event_data: Dict[str, Any]) -> None:
    """Validate event content field."""
    try:
        content = json.loads(event_data["content"])
    except json.JSONDecodeError:
        raise ValidationError("Content must be valid JSON")
    
    kind = event_data["kind"]
    
    if kind == 300:  # Product Listing
        _validate_product_listing_content(content)
    elif kind == 301:  # Bid Submission
        _validate_bid_submission_content(content)
    elif kind == 303:  # Bid Acceptance
        _validate_bid_acceptance_content(content)
    elif kind == 311:  # Payment Confirmation
        _validate_payment_confirmation_content(content)
    elif kind == 313:  # Receipt Confirmation
        _validate_receipt_confirmation_content(content)


def _validate_product_listing_content(content: Dict[str, Any]) -> None:
    """Validate product listing content."""
    required = ["product_name", "description", "price_satoshis"]
    for field in required:
        if field not in content:
            raise ValidationError(f"Missing required content field: {field}")
    
    if content["price_satoshis"] <= 0:
        raise ValidationError("Price must be positive")
        
    if len(content["product_name"]) > 100:
        raise ValidationError("Product name too long")


def _validate_bid_submission_content(content: Dict[str, Any]) -> None:
    """Validate bid submission content."""
    required = ["product_ref", "bid_amount_satoshis", "buyer_collateral_satoshis"]
    for field in required:
        if field not in content:
            raise ValidationError(f"Missing required content field: {field}")
    
    if content["bid_amount_satoshis"] <= 0:
        raise ValidationError("Bid amount must be positive")
        
    if content["buyer_collateral_satoshis"] < 0:
        raise ValidationError("Collateral cannot be negative")


def _validate_bid_acceptance_content(content: Dict[str, Any]) -> None:
    """Validate bid acceptance content."""
    required = ["bid_ref", "ln_invoice"]
    for field in required:
        if field not in content:
            raise ValidationError(f"Missing required content field: {field}")
    
    # Basic Lightning invoice validation
    invoice = content["ln_invoice"]
    if not invoice.startswith(("lnbc", "lntb", "lnbcrt")):
        raise ValidationError("Invalid Lightning invoice format")


def _validate_payment_confirmation_content(content: Dict[str, Any]) -> None:
    """Validate payment confirmation content."""
    required = ["bid_ref", "payment_proof", "payment_method"]
    for field in required:
        if field not in content:
            raise ValidationError(f"Missing required content field: {field}")
    
    valid_methods = ["lightning_htlc", "lightning_keysend", "onchain"]
    if content["payment_method"] not in valid_methods:
        raise ValidationError(f"Invalid payment method: {content['payment_method']}")


def _validate_receipt_confirmation_content(content: Dict[str, Any]) -> None:
    """Validate receipt confirmation content."""
    required = ["payment_ref", "status"]
    for field in required:
        if field not in content:
            raise ValidationError(f"Missing required content field: {field}")
    
    valid_statuses = ["received", "partially_received", "not_received", "damaged"]
    if content["status"] not in valid_statuses:
        raise ValidationError(f"Invalid status: {content['status']}")
    
    # If status is not "received", dispute_reason should be present
    if content["status"] != "received" and "dispute_reason" not in content:
        raise ValidationError("dispute_reason required for non-received status")


def _validate_anti_spam(event_data: Dict[str, Any]) -> None:
    """Validate anti-spam proof."""
    tags = event_data["tags"]
    
    # Find anti-spam proof tag
    anti_spam_tag = None
    for tag in tags:
        if len(tag) >= 2 and tag[0] == "anti_spam_proof":
            anti_spam_tag = tag
            break
    
    if not anti_spam_tag:
        raise ValidationError("Missing anti_spam_proof tag")
    
    proof_type = anti_spam_tag[1]
    
    if proof_type == "pow":
        _validate_pow_proof(event_data, anti_spam_tag)
    elif proof_type == "ln":
        _validate_lightning_proof(anti_spam_tag)
    elif proof_type == "ref":
        _validate_reference_proof(anti_spam_tag)
    else:
        raise ValidationError(f"Unknown anti-spam proof type: {proof_type}")


def _validate_pow_proof(event_data: Dict[str, Any], tag: List[str]) -> None:
    """Validate proof-of-work."""
    if len(tag) < 4:
        raise ValidationError("PoW tag missing nonce or difficulty")
    
    try:
        difficulty = int(tag[3])
    except ValueError:
        raise ValidationError("PoW difficulty must be integer")
    
    # Check if event ID meets difficulty requirement
    event_id = event_data["id"]
    required_zeros = difficulty // 4  # Each hex char = 4 bits
    
    if not event_id.startswith('0' * required_zeros):
        raise ValidationError(f"PoW does not meet difficulty {difficulty} (requires {required_zeros} leading zeros, got {event_id[:8]}...)")


def _validate_lightning_proof(tag: List[str]) -> None:
    """Validate Lightning payment proof."""
    if len(tag) < 3:
        raise ValidationError("Lightning proof missing payment hash")
    
    payment_hash = tag[2]
    if len(payment_hash) != 64:
        raise ValidationError("Invalid Lightning payment hash format")


def _validate_reference_proof(tag: List[str]) -> None:
    """Validate event reference proof."""
    if len(tag) < 4:
        raise ValidationError("Reference proof missing event ID or kind")
    
    event_id = tag[2]
    if len(event_id) != 64:
        raise ValidationError("Invalid referenced event ID format")


def _validate_signature(event_data: Dict[str, Any]) -> None:
    """Validate cryptographic signature."""
    if not verify_event(event_data):
        raise ValidationError("Invalid cryptographic signature")


def validate_event_chain(events: List[Dict[str, Any]]) -> bool:
    """
    Validate a chain of events forms a valid transaction.
    
    Args:
        events: List of events in chronological order
        
    Returns:
        True if valid transaction chain
        
    Raises:
        ValidationError: If chain is invalid
    """
    if not events:
        raise ValidationError("Empty event chain")
    
    # Validate individual events
    for event in events:
        validate_event(event)
    
    # Validate event sequence and references
    _validate_event_sequence(events)
    
    # Validate state transitions
    _validate_state_transitions(events)
    
    return True


def _validate_event_sequence(events: List[Dict[str, Any]]) -> None:
    """Validate event sequence and references."""
    kinds = [event["kind"] for event in events]
    expected_sequence = [300, 301, 303, 311, 313]
    
    if kinds != expected_sequence:
        raise ValidationError(f"Invalid event sequence: {kinds}")
    
    # Validate references between events
    for i in range(1, len(events)):
        current_event = events[i]
        previous_event = events[i-1]
        
        # Check if current event references previous event
        content = json.loads(current_event["content"])
        ref_field = _get_reference_field(current_event["kind"])
        
        if ref_field and ref_field in content:
            if content[ref_field] != previous_event["id"]:
                raise ValidationError(f"Event {current_event['kind']} references wrong previous event")


def _get_reference_field(kind: int) -> Optional[str]:
    """Get the content field that references previous event."""
    reference_fields = {
        301: "product_ref",
        303: "bid_ref", 
        311: "bid_ref",
        313: "payment_ref"
    }
    return reference_fields.get(kind)


def _validate_state_transitions(events: List[Dict[str, Any]]) -> None:
    """Validate transaction state transitions."""
    # Basic validation - ensure amounts are consistent
    listing_content = json.loads(events[0]["content"])  # kind-300
    bid_content = json.loads(events[1]["content"])      # kind-301
    
    listing_price = listing_content["price_satoshis"]
    bid_amount = bid_content["bid_amount_satoshis"]
    
    # For now, just check bid doesn't exceed listing price
    # In a full implementation, this would be more sophisticated
    if bid_amount > listing_price * 1.1:  # Allow 10% over asking
        raise ValidationError("Bid amount significantly exceeds listing price")


def validate_timestamp(timestamp: int, tolerance_seconds: int = 3600) -> bool:
    """
    Validate event timestamp is reasonable.
    
    Args:
        timestamp: Unix timestamp to validate
        tolerance_seconds: Acceptable deviation from current time
        
    Returns:
        True if timestamp is reasonable
    """
    current_time = int(time.time())
    return abs(current_time - timestamp) <= tolerance_seconds