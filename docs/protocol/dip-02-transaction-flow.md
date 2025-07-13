# DIP-02: Basic Transaction Flow

## Summary

Defines the complete transaction workflow for DOMP marketplace interactions, from product listing through payment confirmation, using the minimal 5-event structure for the POC.

## Motivation

A clear, deterministic transaction flow is essential for:
- Predictable client behavior across implementations
- Proper escrow state management
- Dispute resolution and arbitration
- User experience consistency

## Specification

### Transaction States

Each transaction progresses through these states:

1. **LISTED** - Product available for bidding
2. **BID_RECEIVED** - Buyer has submitted bid
3. **BID_ACCEPTED** - Seller accepted, awaiting payment
4. **PAYMENT_CONFIRMED** - Funds in escrow, item should ship
5. **COMPLETED** - Buyer confirmed receipt, funds released

### Event Flow Diagram

```
[Seller] kind-300 Product Listing
    ↓
[Buyer] kind-301 Bid Submission  
    ↓
[Seller] kind-303 Bid Acceptance (with LN invoice)
    ↓
[Buyer] kind-311 Payment Confirmation (payment + collateral)
    ↓ (seller ships item)
[Buyer] kind-313 Receipt Confirmation
    ↓
[Funds Released via Protocol Rules]
```

### Detailed Event Specifications

#### 1. Product Listing (kind-300)

**Purpose**: Seller advertises product for sale
**State Change**: None → LISTED

```json
{
  "kind": 300,
  "pubkey": "<seller_pubkey>",
  "tags": [
    ["d", "<unique_listing_id>"],
    ["anti_spam_proof", "pow", "<nonce>", "<difficulty>"]
  ],
  "content": "{
    \"product_name\": \"Digital Camera\",
    \"description\": \"High-quality DSLR camera with lens\", 
    \"price_satoshis\": 80000000,
    \"category\": \"electronics\",
    \"storage_link\": \"ipfs://QmHash...\",
    \"shipping_info\": {
      \"domestic_cost_satoshis\": 5000000,
      \"estimated_days\": 7
    },
    \"seller_collateral_satoshis\": 8000000
  }"
}
```

**Required Fields**:
- `product_name`: String, 1-100 chars
- `description`: String, max 2000 chars  
- `price_satoshis`: Integer > 0

#### 2. Bid Submission (kind-301)

**Purpose**: Buyer offers to purchase at specific terms
**State Change**: LISTED → BID_RECEIVED

```json
{
  "kind": 301,
  "pubkey": "<buyer_pubkey>",
  "tags": [
    ["anti_spam_proof", "ln", "<payment_hash>"],
    ["ref", "<product_listing_event_id>", "<relay_hint>", "root"]
  ],
  "content": "{
    \"product_ref\": \"<product_listing_event_id>\",
    \"bid_amount_satoshis\": 80000000,
    \"buyer_collateral_satoshis\": 80000000,
    \"message\": \"I'll take it at asking price\",
    \"shipping_address_hash\": \"<sha256_of_encrypted_address>\"
  }"
}
```

**Required Fields**:
- `product_ref`: Event ID of kind-300 listing
- `bid_amount_satoshis`: Integer > 0
- `buyer_collateral_satoshis`: Integer >= bid_amount

#### 3. Bid Acceptance (kind-303)

**Purpose**: Seller accepts bid and provides Lightning invoice
**State Change**: BID_RECEIVED → BID_ACCEPTED

```json
{
  "kind": 303,
  "pubkey": "<seller_pubkey>", 
  "tags": [
    ["anti_spam_proof", "ln", "<payment_hash>"],
    ["ref", "<bid_event_id>", "<relay_hint>", "reply"]
  ],
  "content": "{
    \"bid_ref\": \"<bid_event_id>\",
    \"ln_invoice\": \"lnbc800m1p...\",
    \"collateral_invoice\": \"lnbc800m1p...\",
    \"estimated_shipping_time\": \"3-5 business days\",
    \"terms\": \"Item ships within 24h of payment confirmation\"
  }"
}
```

**Required Fields**:
- `bid_ref`: Event ID of accepted kind-301 bid
- `ln_invoice`: Lightning invoice for purchase amount
- `collateral_invoice`: Lightning invoice for buyer's collateral

#### 4. Payment Confirmation (kind-311)

**Purpose**: Buyer confirms payment and collateral deposited
**State Change**: BID_ACCEPTED → PAYMENT_CONFIRMED

```json
{
  "kind": 311,
  "pubkey": "<buyer_pubkey>",
  "tags": [
    ["anti_spam_proof", "ln", "<payment_hash>"], 
    ["ref", "<bid_acceptance_event_id>", "<relay_hint>", "reply"]
  ],
  "content": "{
    \"bid_ref\": \"<bid_acceptance_event_id>\",
    \"payment_proof\": \"<lightning_payment_hash>\",
    \"collateral_proof\": \"<collateral_payment_hash>\",
    \"payment_method\": \"lightning_htlc\",
    \"escrow_timeout_blocks\": 144,
    \"encrypted_shipping_address\": \"<encrypted_with_seller_pubkey>\"
  }"
}
```

**Required Fields**:
- `bid_ref`: Event ID of kind-303 acceptance
- `payment_proof`: Hash proving payment made
- `collateral_proof`: Hash proving collateral deposited

#### 5. Receipt Confirmation (kind-313)

**Purpose**: Buyer confirms item received, releases funds
**State Change**: PAYMENT_CONFIRMED → COMPLETED

```json
{
  "kind": 313,
  "pubkey": "<buyer_pubkey>",
  "tags": [
    ["anti_spam_proof", "ln", "<payment_hash>"],
    ["ref", "<payment_confirmation_event_id>", "<relay_hint>", "reply"]
  ],
  "content": "{
    \"payment_ref\": \"<payment_confirmation_event_id>\",
    \"status\": \"received\",
    \"rating\": 5,
    \"feedback\": \"Item as described, fast shipping\",
    \"delivery_confirmation_time\": 1672531200
  }"
}
```

**Required Fields**:
- `payment_ref`: Event ID of kind-311 payment confirmation
- `status`: Must be "received"

### Event Validation Rules

#### Temporal Ordering
- Events must reference previous events in the chain
- `created_at` timestamps should be chronologically ordered
- Payment confirmations must occur after bid acceptance

#### State Transitions
- Each event kind can only appear once per transaction chain
- Invalid state transitions should be rejected by clients
- Events referencing non-existent events are invalid

#### Economic Validation
- Bid amounts must not exceed listing price (unless counter-bid)
- Collateral amounts must meet minimum requirements
- Lightning invoices must match bid amounts exactly

## Rationale

### Why This Event Sequence?
- **Minimal viable flow**: Covers essential marketplace operations
- **Clear state machine**: Each event has specific purpose and outcome
- **Bilateral commitment**: Both parties commit resources before shipping
- **Buyer protection**: Funds only released upon confirmation

### Why Lightning Invoices in Acceptance?
- **Atomic commitment**: Invoice creation commits seller to terms
- **Payment reliability**: Standard Lightning payment flow
- **Escrow integration**: HTLC provides trustless escrow mechanism

### Why Separate Collateral?
- **Incentive alignment**: Both parties have skin in the game
- **Spam prevention**: Economic cost to participate
- **Flexible requirements**: Can be negotiated per transaction

## Error Conditions

### Invalid Event Chains
- Events referencing wrong previous events
- Missing required fields in content
- Invalid Lightning invoices or payment proofs
- Collateral amounts below minimums

### Timeout Scenarios
- Bid not accepted within reasonable time
- Payment not confirmed after acceptance
- Receipt not confirmed after reasonable shipping time

### Client Behavior
- Clients should validate entire event chain
- Reject transactions with invalid state transitions
- Display clear error messages for invalid events
- Implement timeout warnings for pending states

## Security Considerations

### Event Chain Integrity
- All events must be cryptographically signed
- Event references create immutable transaction history
- Tampering with any event invalidates the chain

### Payment Security
- Lightning payments are atomic and final
- HTLC preimages provide proof of payment
- Collateral ensures both parties committed

### Privacy Considerations
- Shipping addresses should be encrypted
- Product details may reveal buyer/seller info
- Event IDs are publicly linkable

## Test Vectors

### Complete Successful Transaction
```json
[
  {"kind": 300, "content": "{\"product_name\":\"Camera\",\"price_satoshis\":80000000}"},
  {"kind": 301, "content": "{\"product_ref\":\"abc123\",\"bid_amount_satoshis\":80000000}"},
  {"kind": 303, "content": "{\"bid_ref\":\"def456\",\"ln_invoice\":\"lnbc800m...\"}"},
  {"kind": 311, "content": "{\"bid_ref\":\"ghi789\",\"payment_proof\":\"jkl012\"}"},
  {"kind": 313, "content": "{\"payment_ref\":\"mno345\",\"status\":\"received\"}"} 
]
```

### Invalid Transaction (Wrong Reference)
```json
[
  {"kind": 300, "content": "{\"product_name\":\"Camera\",\"price_satoshis\":80000000}"},
  {"kind": 301, "content": "{\"product_ref\":\"wrong_id\",\"bid_amount_satoshis\":80000000}"}
]
```

## Implementation Notes

### Client Requirements
- Validate event chains before displaying transactions
- Implement state machine for transaction tracking
- Handle Lightning payment integration
- Provide clear UI for each transaction state

### Relay Considerations
- Relays may filter events by anti-spam proofs
- Event storage requirements for transaction history
- Query patterns for finding related events

## References

- [DIP-01: Core Event Structure](dip-01-core-events.md)
- [Lightning Network BOLT specifications](https://github.com/lightningnetwork/lightning-rfc)
- [Nostr NIP-01: Basic Event Format](https://github.com/nostr-protocol/nips/blob/master/01.md)