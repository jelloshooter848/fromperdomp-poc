#!/usr/bin/env python3

import json
import sys
sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import compute_event_id

# Load the actual event
with open('test-listing4.json') as f:
    actual_event = json.load(f)

print("=== Actual Event Structure ===")
print("Stored ID:", actual_event['id'])

# Remove id and sig for computation
event_copy = actual_event.copy()
event_copy.pop('id', None)
event_copy.pop('sig', None)

print("\nEvent data for ID computation:")
for key, value in event_copy.items():
    print(f"{key}: {repr(value)}")

# Compute ID
computed_id = compute_event_id(event_copy)
print(f"\nComputed ID: {computed_id}")
print(f"IDs match: {actual_event['id'] == computed_id}")

# Test if manually recreating the exact structure that should generate stored ID
print("\n=== Manual Recreation Test ===")
# Try with same data but ensuring exact structure
test_event = {
    "pubkey": "c49a5019d72292cea13b599c16f70a9b1f96c8650058d19549e3c65c0896850c",
    "created_at": 1752418894,
    "kind": 300,
    "tags": [["d", "listing-1752418894"], ["anti_spam_proof", "pow", "185", "8"]],
    "content": "{\"product_name\":\"Test Item 4\",\"description\":\"Final fix test\",\"price_satoshis\":4000000}"
}

manual_id = compute_event_id(test_event)
print(f"Manual recreation ID: {manual_id}")
print(f"Matches stored ID: {actual_event['id'] == manual_id}")

# Check if the content strings are exactly the same
print(f"\nContent comparison:")
print(f"Actual: {repr(actual_event['content'])}")
print(f"Manual: {repr(test_event['content'])}")
print(f"Content matches: {actual_event['content'] == test_event['content']}")