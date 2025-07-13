#!/usr/bin/env python3

import json
import sys
sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import compute_event_id

# Load the actual event
with open('test-listing4.json') as f:
    event = json.load(f)

print("=== PoW Verification Test ===")
print("Event ID:", event['id'])

# Extract the PoW proof
pow_tag = None
for tag in event['tags']:
    if len(tag) >= 2 and tag[0] == 'anti_spam_proof' and tag[1] == 'pow':
        pow_tag = tag
        break

if not pow_tag:
    print("No PoW tag found!")
    exit(1)

nonce = pow_tag[2]
difficulty = int(pow_tag[3])

print(f"PoW nonce: {nonce}")
print(f"PoW difficulty: {difficulty}")

# Now simulate what the PoW generation should have done
# Start with event WITHOUT PoW tag
event_without_pow = event.copy()
event_without_pow.pop('id', None)
event_without_pow.pop('sig', None)

# Remove PoW tag
tags_without_pow = [tag for tag in event_without_pow['tags'] 
                   if not (len(tag) >= 2 and tag[0] == 'anti_spam_proof')]
event_without_pow['tags'] = tags_without_pow

print("\nEvent WITHOUT PoW tag:")
print(json.dumps(event_without_pow, indent=2))

# Add the PoW tag back (simulating what generate_pow_nonce does)
event_with_pow = event_without_pow.copy()
event_with_pow['tags'] = event_without_pow['tags'] + [['anti_spam_proof', 'pow', nonce, str(difficulty)]]

print("\nEvent WITH PoW tag (reconstructed):")
print(json.dumps(event_with_pow, indent=2))

# Compute ID of the reconstructed event
reconstructed_id = compute_event_id(event_with_pow)
print(f"\nReconstructed ID: {reconstructed_id}")
print(f"Matches stored ID: {event['id'] == reconstructed_id}")

# Check PoW validity
required_zeros = difficulty // 4
target_prefix = '0' * required_zeros
print(f"\nPoW validation:")
print(f"Required prefix: '{target_prefix}' ({required_zeros} zeros)")
print(f"Event ID starts with: '{event['id'][:required_zeros]}'")
print(f"PoW valid: {event['id'].startswith(target_prefix)}")