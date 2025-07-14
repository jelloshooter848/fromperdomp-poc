#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import generate_pow_event, compute_event_id

# Simple test event
test_event = {
    "pubkey": "test_pubkey",
    "created_at": 1234567890,
    "kind": 300,
    "tags": [["d", "test-listing"]],
    "content": '{"product_name":"Test Item","price_satoshis":1000}'
}

print("=== Debugging PoW Generation ===")
print("Test event:", test_event)

print("\nGenerating PoW with difficulty 8...")
try:
    event_id, nonce, complete_event_data = generate_pow_event(test_event, 8)
    
    print(f"Generated event ID: {event_id}")
    print(f"Generated nonce: {nonce}")
    print(f"Leading characters: {event_id[:4]}")
    print(f"Meets difficulty 8 (2 leading zeros): {event_id.startswith('00')}")
    
    # Verify by recomputing
    verification_data = complete_event_data.copy()
    verification_data.pop('id', None)
    verification_data.pop('sig', None)
    
    recomputed_id = compute_event_id(verification_data)
    print(f"Recomputed ID: {recomputed_id}")
    print(f"IDs match: {event_id == recomputed_id}")
    
    print(f"Complete event tags: {complete_event_data['tags']}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()