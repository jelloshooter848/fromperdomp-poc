#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')
from domp.events import ProductListing
from domp.crypto import KeyPair, generate_pow_event, verify_event

# Create test objects
kp = KeyPair()
listing = ProductListing(
    product_name='test',
    description='test', 
    price_satoshis=100,
    category='test',
    seller_collateral_satoshis=10,
    listing_id='test_id'
)

print("=== Debugging Signature Issue ===")

# Get initial event data
event_data = listing.to_dict()
event_data.pop('id', None)
event_data.pop('sig', None)

print("1. Generating PoW...")
event_id, nonce, complete_event_data = generate_pow_event(event_data, 8)
print(f"   PoW ID: {event_id[:8]}... (starts with 00: {event_id.startswith('00')})")

print("2. Applying PoW data to listing...")
listing.tags = complete_event_data["tags"]
listing.id = event_id
print(f"   Listing ID: {listing.id[:8]}...")
print(f"   Listing tags: {listing.tags}")

print("3. Signing listing...")
listing.sign(kp)
print(f"   Signature: {listing.sig[:16]}...")
print(f"   Pubkey: {listing.pubkey[:16]}...")

print("4. Testing verification...")
final_event = listing.to_dict()
print(f"   Final event ID: {final_event['id'][:8]}...")
print(f"   ID matches PoW: {final_event['id'] == event_id}")

result = verify_event(final_event)
print(f"   Verification result: {result}")

if not result:
    print("\n5. Manual verification check...")
    from domp.crypto import compute_event_id
    
    # Check what ID would be computed normally
    test_event = final_event.copy()
    test_event.pop('id', None)
    test_event.pop('sig', None)
    normal_id = compute_event_id(test_event)
    print(f"   Normal computed ID: {normal_id[:8]}...")
    print(f"   PoW ID:            {event_id[:8]}...")
    print(f"   IDs different: {normal_id != event_id}")