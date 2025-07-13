# DIP-01: Core Event Structure

## Summary

Defines the fundamental event structure and signature requirements for DOMP protocol events, building on Nostr's event format while adding marketplace-specific fields.

## Motivation

DOMP needs a standardized way to represent marketplace actions (listings, bids, payments) that is:
- Compatible with existing Nostr infrastructure
- Cryptographically verifiable
- Extensible for future marketplace features
- Simple enough for widespread adoption

## Specification

### Base Event Structure

All DOMP events extend the Nostr event format:

```json
{
  "id": "<32-byte hex event id>",
  "pubkey": "<32-byte hex pubkey of the event creator>", 
  "created_at": <unix timestamp in seconds>,
  "kind": <event kind number>,
  "tags": [
    ["d", "<unique identifier for replaceable events>"],
    ["anti_spam_proof", "<proof of work or payment hash>"],
    ["ref", "<referenced event id>", "<relay hint>"]
  ],
  "content": "<JSON string with event-specific data>",
  "sig": "<64-byte hex signature>"
}
```

### DOMP-Specific Requirements

#### Event ID Generation
- Calculated as SHA256 of serialized event data
- Must match Nostr NIP-01 specification
- Ensures tamper detection

#### Anti-Spam Proof
All events MUST include one of:
- **Proof of Work**: `["anti_spam_proof", "pow", "<nonce>", "<difficulty>"]`
- **Lightning Payment**: `["anti_spam_proof", "ln", "<payment_hash>"]`

#### Event References
Events referencing other events MUST use:
```json
["ref", "<event_id>", "<relay_url>", "<marker>"]
```
Where `marker` indicates relationship type: "reply", "root", "mention"

#### Content Validation
- Content field MUST be valid JSON string
- Required fields depend on event kind (see DIP-02)
- All amounts MUST be in satoshis (integers)

### Signature Verification

Events MUST be signed using Schnorr signatures:
1. Serialize event data (id, pubkey, created_at, kind, tags, content)
2. SHA256 hash the serialized data
3. Sign hash with creator's private key
4. Verify signature matches pubkey

### Event Kinds

DOMP reserves event kinds 300-399 for marketplace operations:

| Kind | Name | Description |
|------|------|-------------|
| 300 | Product Listing | Seller lists item for sale |
| 301 | Bid Submission | Buyer places bid on item |
| 303 | Bid Acceptance | Seller accepts bid terms |
| 311 | Payment Confirmation | Buyer confirms payment made |
| 313 | Receipt Confirmation | Buyer confirms item received |

## Rationale

### Why Extend Nostr?
- Leverages existing relay infrastructure
- Proven cryptographic model
- Active developer community
- Natural fit for decentralized marketplace

### Why Specific Event Kinds?
- Clear protocol semantics
- Easier client development
- Better relay filtering
- Future extensibility

### Why Anti-Spam Requirements?
- Prevents marketplace flooding
- Economic incentive alignment
- Flexible implementation options
- Relay autonomy preserved

## Test Vectors

### Valid Product Listing Event
```json
{
  "id": "abc123...",
  "pubkey": "def456...", 
  "created_at": 1672531200,
  "kind": 300,
  "tags": [
    ["anti_spam_proof", "pow", "12345", "20"],
    ["d", "camera-listing-001"]
  ],
  "content": "{\"product_name\":\"Digital Camera\",\"price_satoshis\":80000000}",
  "sig": "789abc..."
}
```

### Invalid Event (Missing Anti-Spam)
```json
{
  "id": "abc123...",
  "pubkey": "def456...",
  "created_at": 1672531200, 
  "kind": 300,
  "tags": [],
  "content": "{\"product_name\":\"Digital Camera\"}",
  "sig": "789abc..."
}
```

## Implementation

Reference implementations MUST:
- Validate event structure before processing
- Verify signatures and event IDs
- Check anti-spam proofs
- Reject malformed or invalid events
- Support both PoW and Lightning anti-spam

## Security Considerations

- Private keys must be securely generated and stored
- Events are public and permanent once broadcast
- Anti-spam proofs should be verified by relays
- Event timestamps should be recent (within reasonable bounds)

## References

- [Nostr NIP-01: Basic Event Format](https://github.com/nostr-protocol/nips/blob/master/01.md)
- [Nostr NIP-13: Proof of Work](https://github.com/nostr-protocol/nips/blob/master/13.md)