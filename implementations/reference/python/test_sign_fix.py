#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')
from domp.events import ProductListing
from domp.crypto import KeyPair

kp = KeyPair()
listing = ProductListing(
    product_name='test',
    description='test', 
    price_satoshis=100,
    category='test',
    seller_collateral_satoshis=10,
    listing_id='test_id'
)
listing.tags.append(['anti_spam_proof', 'pow', '134', '8'])
listing.id = '00test123'
print('Before sign:', listing.id)
listing.sign(kp)
print('After sign:', listing.id)
print('Tags:', listing.tags)