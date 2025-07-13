# DIP-03: Lightning Network Integration

## Summary

Defines how DOMP integrates with the Lightning Network for payments, collateral deposits, and trustless escrow using Hash Time-Locked Contracts (HTLCs).

## Motivation

Lightning Network provides:
- **Instant payments** with low fees
- **Trustless escrow** through HTLC mechanism  
- **Atomic transactions** ensuring payment reliability
- **Scalability** for high-frequency marketplace transactions

DOMP needs a standardized way to leverage Lightning for secure, fast payments without requiring trusted third parties.

## Specification

### Payment Types

DOMP uses Lightning Network for three types of payments:

1. **Purchase Payment**: Buyer pays seller for item
2. **Buyer Collateral**: Buyer's security deposit 
3. **Seller Collateral**: Seller's security deposit
4. **Anti-Spam Payments**: Small payments to relays/protocol

### HTLC Escrow Mechanism

#### Basic HTLC Flow

```
1. Buyer generates random preimage R
2. Buyer calculates hash H = SHA256(R)  
3. Buyer creates HTLC to seller with hash H
4. Seller can claim payment only by revealing R
5. Buyer reveals R only after confirming item receipt
6. If timeout occurs, buyer gets refund
```

#### DOMP HTLC Structure

```json
{
  "amount_msat": 80000000000,
  "payment_hash": "abc123...",
  "timeout_blocks": 144,
  "recipient": "<seller_pubkey>",
  "purpose": "domp_purchase",
  "domp_transaction_id": "<event_chain_root>"
}
```

### Lightning Invoice Requirements

#### Invoice Generation (kind-303)

Sellers MUST include valid Lightning invoices in bid acceptance:

```json
{
  "kind": 303,
  "content": "{
    \"bid_ref\": \"<bid_event_id>\",
    \"ln_invoice\": \"lnbc800m1pwjqwqpp5...\",
    \"collateral_invoice\": \"lnbc800m1pwjqwqpp6...\",
    \"invoice_expiry_seconds\": 3600
  }"
}
```

**Invoice Requirements**:
- Amount must match bid exactly
- Expiry should be reasonable (1-24 hours)
- Description should reference DOMP transaction
- Must be generated for seller's node

#### Payment Proof (kind-311)

Buyers MUST provide payment proofs after paying:

```json
{
  "kind": 311,
  "content": "{
    \"bid_ref\": \"<acceptance_event_id>\",
    \"payment_proof\": \"<payment_preimage_or_hash>\",
    \"collateral_proof\": \"<collateral_preimage_or_hash>\",
    \"payment_method\": \"lightning_htlc\"
  }"
}
```

### Escrow State Management

#### Three-Phase Escrow

**Phase 1: Setup**
- Seller generates invoices for purchase + buyer collateral
- Buyer pays both invoices, creating HTLCs
- Payments locked until seller provides preimages

**Phase 2: Shipping** 
- Seller ships item (trusting HTLC security)
- Buyer monitors for item delivery
- HTLCs remain locked during shipping

**Phase 3: Resolution**
- Buyer confirms receipt, reveals preimages
- Seller claims purchase payment
- Buyer reclaims collateral
- OR timeout occurs and buyer gets refunds

#### Collateral Management

**Seller Collateral**:
- Deposited before listing (optional but recommended)
- Separate Lightning payment to escrow service or buyer
- Released when transaction completes successfully

**Buyer Collateral**:
- Paid together with purchase amount
- Incentivizes honest receipt confirmation
- Returned upon successful completion

### Lightning Node Requirements

#### For Sellers
- Must run Lightning node or use custodial service
- Must be able to generate invoices
- Should have adequate inbound liquidity
- Must monitor for incoming payments

#### For Buyers  
- Must be able to pay Lightning invoices
- Should understand HTLC mechanics
- Must have adequate outbound liquidity
- Must store payment proofs securely

#### For DOMP Clients
- Should integrate with Lightning node/wallet
- Must validate Lightning invoices
- Should handle payment timeouts gracefully
- Must track HTLC states

### Payment Flows

#### Successful Transaction
```
1. Seller: Generate invoices → kind-303 event
2. Buyer: Pay invoices → kind-311 event  
3. Seller: Ship item
4. Buyer: Confirm receipt → kind-313 event
5. Seller: Claim payments using preimages
6. Buyer: Reclaim collateral
```

#### Failed Transaction (Non-delivery)
```
1-3. Same as successful flow
4. Buyer: Does NOT confirm receipt
5. HTLC timeout occurs
6. Buyer: Reclaim all payments
7. Seller: Loses collateral (if any)
```

#### Failed Transaction (Non-payment)
```
1. Seller: Generate invoices → kind-303 event
2. Buyer: Does NOT pay invoices
3. Lightning invoices expire
4. Transaction abandoned
```

### Security Considerations

#### HTLC Timeout Selection
- **Too short**: Seller may not have time to ship
- **Too long**: Buyer funds locked unnecessarily  
- **Recommended**: 144 blocks (24 hours) minimum
- Should scale with shipping time estimates

#### Preimage Management
- Buyers must securely store preimages
- Revealing preimage commits to receipt
- Lost preimages = lost collateral
- Should backup preimages securely

#### Invoice Validation
- Clients must validate invoice amounts
- Check invoice expiry times
- Verify recipient node identity
- Detect duplicate invoices

#### Payment Routing
- Large payments may fail due to liquidity
- Consider payment splitting for large amounts
- Monitor routing fee costs
- Have backup payment methods

### Anti-Spam Integration

#### Lightning Anti-Spam Payments
```json
{
  "tags": [
    ["anti_spam_proof", "ln", "<payment_hash>", "<amount_msat>"]
  ]
}
```

- Small payments (1-1000 sats) to relay operators
- Proves economic commitment to event
- Payment hash serves as proof
- Alternative to Proof-of-Work

#### Relay Payment Policies
- Relays set their own payment requirements
- Market-driven pricing for event storage
- Quality relays can charge premium rates
- Free tier possible for established users

### Error Handling

#### Common Failure Modes
1. **Invoice Generation Failure**: Seller node offline
2. **Payment Routing Failure**: Insufficient liquidity
3. **HTLC Timeout**: Buyer doesn't confirm receipt
4. **Node Offline**: Either party's node unreachable

#### Client Behavior
- Display clear error messages
- Provide retry mechanisms
- Handle partial payment states
- Implement graceful degradation

#### Recovery Procedures
- Monitor HTLC expiry times
- Automatic refund claiming
- Dispute resolution escalation
- Manual intervention options

### Implementation Requirements

#### Lightning Library Integration
- Use established Lightning libraries (LND, CLN, Eclair)
- Implement proper key management
- Handle channel management
- Monitor payment states

#### Protocol Compliance
- Validate all Lightning invoices before payment
- Store payment proofs securely
- Implement timeout monitoring
- Provide HTLC state APIs

## Test Vectors

### Valid Lightning Invoice
```
lnbc800m1pwjqwqpp5abc123...
```

### Payment Proof Event
```json
{
  "kind": 311,
  "content": "{\"payment_proof\":\"def456...\",\"payment_method\":\"lightning_htlc\"}"
}
```

### HTLC Timeout Scenario
```json
{
  "htlc_timeout_blocks": 144,
  "current_block_height": 800000,
  "payment_block_height": 799900,
  "blocks_remaining": 44
}
```

## Implementation Notes

### Client Integration
- Lightning wallet integration required
- HTLC state monitoring essential
- Backup/recovery mechanisms critical
- User education about timeouts important

### Testing Strategies
- Use Lightning testnet for development
- Test various failure scenarios
- Validate timeout behavior
- Ensure proper fee handling

## References

- [Lightning Network BOLT Specifications](https://github.com/lightningnetwork/lightning-rfc)
- [BOLT #2: Peer Protocol for Channel Management](https://github.com/lightningnetwork/lightning-rfc/blob/master/02-peer-protocol.md)
- [BOLT #3: Bitcoin Transaction and Script Formats](https://github.com/lightningnetwork/lightning-rfc/blob/master/03-transactions.md)
- [Lightning Network Paper](https://lightning.network/lightning-network-paper.pdf)