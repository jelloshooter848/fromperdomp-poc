#!/usr/bin/env python3

import json
import sys
sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import compute_event_id, generate_pow_nonce

# Test data matching test-listing3.json structure
test_event = {
    "pubkey": "c49a5019d72292cea13b599c16f70a9b1f96c8650058d19549e3c65c0896850c",
    "created_at": 1752418668,
    "kind": 300,
    "tags": [["d", "listing-1752418668"]],
    "content": '{"product_name":"Test Item 3","description":"Fixed version test","price_satoshis":3000000}'
}

print("=== Testing PoW Generation ===")
print("Original event:")
print(json.dumps(test_event, indent=2))

print("\nGenerating PoW...")
event_id, nonce = generate_pow_nonce(test_event, 8)

print(f"Found nonce: {nonce}")
print(f"Generated event ID: {event_id}")

# Manually add the PoW tag and recompute
test_event_with_pow = test_event.copy()
test_event_with_pow["tags"] = test_event["tags"] + [["anti_spam_proof", "pow", nonce, "8"]]

print("\nEvent with PoW tag:")
print(json.dumps(test_event_with_pow, indent=2))

manual_id = compute_event_id(test_event_with_pow)
print(f"Manual computation: {manual_id}")
print(f"IDs match: {event_id == manual_id}")