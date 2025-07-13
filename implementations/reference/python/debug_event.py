#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to Python path so we can import domp
sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.validation import validate_event
from domp.crypto import verify_event, compute_event_id

def debug_event(filename):
    with open(filename) as f:
        event = json.load(f)

    print(f'=== Debugging {filename} ===')
    print('Event ID:', event['id'])
    
    # Check if ID recomputes correctly
    event_copy = event.copy()
    event_copy.pop('id', None)
    event_copy.pop('sig', None)
    
    print('\nEvent structure for ID computation:')
    print('pubkey:', event_copy['pubkey'])
    print('created_at:', event_copy['created_at'])
    print('kind:', event_copy['kind'])
    print('tags:', event_copy['tags'])
    print('content:', event_copy['content'])
    
    # Create serialization data like compute_event_id does
    serialization_data = [
        0,
        event_copy["pubkey"],
        event_copy["created_at"], 
        event_copy["kind"],
        event_copy["tags"],
        event_copy["content"]
    ]
    
    import json as json_module
    serialized = json_module.dumps(serialization_data, separators=(',', ':'), sort_keys=True)
    print('\nSerialized for hashing:', serialized)
    
    computed_id = compute_event_id(event_copy)
    print('\nComputed ID:', computed_id)
    print('IDs match:', event['id'] == computed_id)
    
    # Check PoW
    starts_with_00 = event['id'].startswith('00')
    print('Starts with 00:', starts_with_00)
    
    # Try verification
    try:
        is_valid = verify_event(event)
        print('Event verification:', is_valid)
    except Exception as e:
        print('Event verification error:', e)

if __name__ == '__main__':
    debug_event('test-listing4.json')