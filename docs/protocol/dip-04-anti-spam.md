# DIP-04: Anti-Spam Mechanisms

## Summary

Defines anti-spam measures for DOMP events including Proof-of-Work (PoW) and Lightning Network payments to prevent network abuse while maintaining decentralization and accessibility.

## Motivation

Decentralized networks are vulnerable to spam attacks that can:
- Degrade relay performance and user experience  
- Flood marketplaces with fake listings or bids
- Enable Sybil attacks on reputation systems
- Waste network resources and storage

DOMP needs flexible anti-spam mechanisms that:
- Allow relay operators to set their own policies
- Provide multiple options for different user capabilities
- Scale cost with network demand
- Maintain protocol simplicity

## Specification

### Anti-Spam Requirements

All DOMP events MUST include one of the following anti-spam proofs:

1. **Proof-of-Work (PoW)**: Computational proof via NIP-13
2. **Lightning Payment**: Small payment to relay or protocol
3. **Event Reference**: Hash of valid previous event (reputation events only)

### Proof-of-Work (PoW)

#### PoW Tag Format
```json
["anti_spam_proof", "pow", "<nonce>", "<difficulty>"]
```

#### Requirements
- Uses SHA256 hashing as per Nostr NIP-13
- Event ID must have leading zeros equal to difficulty
- Nonce is arbitrary string to achieve target
- Difficulty is number of leading zero bits required

#### Example PoW Event
```json
{
  "id": "000012345678901234567890123456789012345678901234567890123456789",
  "tags": [
    ["anti_spam_proof", "pow", "987654321", "20"]
  ],
  "content": "{\"product_name\":\"Camera\"}"
}
```

#### Validation
```python
def validate_pow(event_id, difficulty):
    required_zeros = difficulty
    actual_zeros = len(event_id) - len(event_id.lstrip('0'))
    return actual_zeros >= required_zeros
```

### Lightning Payments

#### Payment Tag Format
```json
["anti_spam_proof", "ln", "<payment_hash>", "<amount_msat>"]
```

#### Requirements
- Payment hash proves payment was made
- Amount is in millisatoshis
- Payment recipient determined by relay policy
- Payment should be recent (within reasonable timeframe)

#### Example Lightning Payment Event
```json
{
  "tags": [
    ["anti_spam_proof", "ln", "abcdef123456...", "1000"]
  ],
  "content": "{\"bid_amount_satoshis\":80000000}"
}
```

#### Payment Recipients
- **Relay Operators**: Direct payment for event processing
- **Protocol Fund**: Community-managed development fund
- **Burn Address**: Proof of economic commitment

### Event Reference Proofs

For reputation and feedback events only:

```json
["anti_spam_proof", "ref", "<previous_event_id>", "<event_kind>"]
```

#### Requirements
- Referenced event must be valid and signed by prover
- Only works for events that reference transactions
- Prevents reputation manipulation by non-participants
- Each event can only be referenced once per user

### Relay Anti-Spam Policies

#### Policy Flexibility
Relays MAY:
- Set different requirements for different event kinds
- Adjust difficulty/payment amounts based on demand
- Accept multiple anti-spam methods
- Implement time-based rate limiting
- Whitelist trusted users

#### Policy Announcement
Relays SHOULD announce their policies via NIP-11:

```json
{
  "name": "DOMP Relay",
  "supported_nips": [1, 11, 13],
  "domp_policy": {
    "anti_spam_required": true,
    "pow_difficulty": {
      "kind_300": 20,
      "kind_301": 18, 
      "default": 16
    },
    "lightning_payment": {
      "amount_msat": 1000,
      "recipient": "lnurl1234..."
    },
    "rate_limits": {
      "events_per_hour": 100,
      "events_per_day": 1000
    }
  }
}
```

#### Dynamic Adjustment
Relays MAY adjust requirements based on:
- Network congestion levels
- Available storage capacity
- Quality of service targets
- Economic incentives

### Client Implementation

#### Multiple Method Support
Clients SHOULD support all anti-spam methods:
- PoW generation for users without Lightning
- Lightning payments for users with wallets
- Automatic method selection based on user preference

#### Cost Optimization
Clients SHOULD:
- Cache PoW results when possible
- Batch Lightning payments efficiently
- Monitor relay policies and adjust accordingly
- Provide cost estimates to users

#### User Experience
Clients MUST:
- Display anti-spam costs clearly
- Allow users to choose preferred method
- Handle failures gracefully
- Provide progress feedback for PoW generation

### Security Considerations

#### PoW Security
- Higher difficulty increases spam cost but also user burden
- GPU/ASIC mining may create unfair advantages
- Difficulty should scale with network capacity

#### Lightning Payment Security
- Payments prove economic commitment but require Lightning access
- Payment proofs can be replayed (use timestamps)
- Relay operators must be trusted to process payments fairly

#### Gaming Prevention
- Event reference proofs prevent Sybil reputation attacks
- Rate limiting prevents burst spam attacks
- Multiple methods prevent single point of failure

### Economics

#### Cost Structure
```
PoW Cost = electricity_cost * hash_rate * time_to_solve
Lightning Cost = payment_amount + routing_fees
```

#### Market Dynamics
- Higher demand → higher anti-spam requirements
- Quality relays can charge premium rates
- Competition keeps costs reasonable
- Users can switch to cheaper relays

#### Accessibility
- PoW ensures access for users without Lightning
- Small payment amounts keep barriers low
- Free tier possible for established users
- Multiple relays provide competition

### Implementation Examples

#### PoW Generation (Python)
```python
import hashlib
import json
import time

def generate_pow(event_data, difficulty):
    nonce = 0
    target_zeros = difficulty
    
    while True:
        event_data['tags'].append(['anti_spam_proof', 'pow', str(nonce), str(difficulty)])
        event_json = json.dumps(event_data, separators=(',', ':'), sort_keys=True)
        event_id = hashlib.sha256(event_json.encode()).hexdigest()
        
        if event_id.startswith('0' * target_zeros):
            return event_id, nonce
            
        nonce += 1
        event_data['tags'].pop()  # Remove failed nonce
```

#### Lightning Payment Integration
```python
async def pay_for_anti_spam(relay_policy, event_kind):
    amount_msat = relay_policy['lightning_payment']['amount_msat']
    recipient = relay_policy['lightning_payment']['recipient']
    
    payment_hash = await lightning_client.pay_invoice(
        amount_msat=amount_msat,
        recipient=recipient,
        memo=f"DOMP anti-spam for kind-{event_kind}"
    )
    
    return payment_hash
```

### Migration and Compatibility

#### Legacy Support
- Existing Nostr events without anti-spam proofs
- Gradual rollout of requirements
- Backwards compatibility during transition

#### Future Extensions
- Additional anti-spam methods (stake-based, reputation-based)
- Cross-relay coordination
- Adaptive difficulty algorithms

## Test Vectors

### Valid PoW Event
```json
{
  "id": "000012345678901234567890123456789012345678901234567890123456789",
  "tags": [["anti_spam_proof", "pow", "42", "20"]]
}
```

### Valid Lightning Payment Event  
```json
{
  "tags": [["anti_spam_proof", "ln", "fedcba987654321", "1000"]]
}
```

### Invalid Anti-Spam (Insufficient PoW)
```json
{
  "id": "123456789012345678901234567890123456789012345678901234567890123",
  "tags": [["anti_spam_proof", "pow", "99", "20"]]
}
```

## Implementation Requirements

### Relay Implementation
- Validate anti-spam proofs before accepting events
- Implement configurable policies
- Provide clear rejection messages
- Monitor and adjust requirements dynamically

### Client Implementation  
- Support multiple anti-spam methods
- Automatic relay policy detection
- User-friendly cost display
- Graceful fallback handling

## References

- [Nostr NIP-13: Proof of Work](https://github.com/nostr-protocol/nips/blob/master/13.md)
- [Nostr NIP-11: Relay Information Document](https://github.com/nostr-protocol/nips/blob/master/11.md)
- [Lightning Network Specifications](https://github.com/lightningnetwork/lightning-rfc)
- [Hashcash Paper](http://www.hashcash.org/papers/hashcash.pdf)