# DOMP Python Reference Implementation

A reference implementation of the Decentralized Online Marketplace Protocol (DOMP) in Python with full Lightning Network integration.

## Features

- **🚀 DOMP Service Launcher** - Unified management for all services
- **⚡ Lightning Network Integration** - Real LND client with escrow management
- **🌐 Web API** - FastAPI backend with WebSocket real-time updates
- Complete DOMP event creation and validation
- Nostr relay integration for event publishing
- Cryptographic event signing and verification  
- Proof-of-Work anti-spam generation
- Transaction state management
- Comprehensive test suite (11 tests, 100% passing)

## Installation

### From Source

```bash
git clone https://github.com/domp-protocol/domp
cd domp/implementations/reference/python
pip install -e .
```

### Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

> **💡 Recommended**: Use the DOMP Service Launcher for the easiest setup experience.

### Option 1: Using the Service Launcher (Recommended)

```bash
# Start the interactive launcher
python domp_launcher.py

# Or use command-line mode
python domp_launcher.py start    # Start all services
python domp_launcher.py unlock   # Unlock Lightning wallet
python domp_launcher.py test     # Run comprehensive tests
```

**Interactive Menu:**
1. Start LND Lightning Node
2. Start Web API  
3. Start All Services ✅
4. Stop services
5. Unlock Wallet ✅
6. Run Tests ✅
7. View Logs
8. Help

**Web Interface:** http://localhost:8001

### Option 2: Manual Setup

### 1. Generate Keys

```bash
# Generate a new keypair
domp keys generate --output my-key.txt

# Show public key from private key file
domp keys show my-key.txt
```

### 2. Create a Product Listing

```bash
# Create a product listing with proof-of-work
domp event create-listing \
  --key-file my-key.txt \
  --product-name \"Digital Camera\" \
  --description \"High-quality DSLR camera\" \
  --price 80000000 \
  --category electronics \
  --output listing.json
```

### 3. Validate Events

```bash
# Validate a single event
domp event validate listing.json

# Validate a transaction chain
domp event validate-chain transaction.json
```

### 4. Publish to Relays

```bash
# Publish event to default relays
domp client publish --key-file my-key.txt listing.json

# Publish to specific relays
domp client publish \
  --key-file my-key.txt \
  --relays wss://relay.damus.io \
  --relays wss://nos.lol \
  listing.json
```

### 5. Browse Marketplace

```bash
# List recent product listings
domp client list-products --key-file my-key.txt --limit 20

# Track a specific transaction
domp client track-transaction --key-file my-key.txt <product-id>
```

## Python API

### Basic Event Creation

```python
from domp import KeyPair, ProductListing, validate_event

# Generate keypair
keypair = KeyPair()

# Create product listing
listing = ProductListing(
    product_name=\"Digital Camera\",
    description=\"High-quality DSLR camera\",
    price_satoshis=80000000,
    category=\"electronics\"
)

# Add proof-of-work anti-spam
from domp.crypto import generate_pow_nonce
event_data = listing.to_dict()
event_id, nonce = generate_pow_nonce(event_data, difficulty=20)
listing.tags.append([\"anti_spam_proof\", \"pow\", nonce, \"20\"])

# Sign the event
listing.sign(keypair)

# Validate
validate_event(listing.to_dict())
```

### Client Usage

```python
import asyncio
from domp import DOMPClient, KeyPair

async def main():
    # Create client
    keypair = KeyPair()
    client = DOMPClient(keypair)
    
    # Connect to relays
    await client.connect()
    
    # Get recent listings
    listings = await client.get_product_listings(limit=10)
    for listing in listings:
        print(f\"Product: {listing.content}\")
    
    # Publish event
    await client.publish_event(listing)
    
    # Disconnect
    await client.disconnect()

asyncio.run(main())
```

### Transaction Management

```python
from domp import TransactionManager

# Create transaction manager
manager = TransactionManager(client)

# Track transaction state
state = manager.get_transaction_state(product_id)
print(f\"Transaction state: {state}\")

# Get user transactions
transactions = manager.get_user_transactions(user_pubkey, role=\"seller\")
```

## Event Types

The implementation supports all DOMP core event types:

- **kind-300**: Product Listing - Seller lists item for sale
- **kind-301**: Bid Submission - Buyer places bid on item  
- **kind-303**: Bid Acceptance - Seller accepts bid terms
- **kind-311**: Payment Confirmation - Buyer confirms payment made
- **kind-313**: Receipt Confirmation - Buyer confirms item received

## Anti-Spam Support

### Proof-of-Work

```bash
# Generate PoW for existing event
domp pow generate event.json --difficulty 20 --output event-with-pow.json
```

```python
from domp.crypto import generate_pow_nonce

event_id, nonce = generate_pow_nonce(event_data, difficulty=20)
```

### Lightning Payments

```python
# Add Lightning payment proof
event.tags.append([\"anti_spam_proof\", \"ln\", payment_hash, \"1000\"])
```

## Validation

The implementation includes comprehensive validation:

- JSON schema validation for all event types
- Cryptographic signature verification
- Anti-spam proof validation
- Transaction chain validation
- Timestamp validation

## Configuration

### Relay Configuration

Default relays can be overridden:

```python
client = DOMPClient(keypair, relays=[
    \"wss://relay.damus.io\",
    \"wss://nos.lol\",
    \"wss://relay.snort.social\"
])
```

### Key Storage

Private keys should be stored securely:

```python
# Load from file
keypair = KeyPair.from_hex(open('private-key.txt').read().strip())

# Generate new key
keypair = KeyPair()
with open('new-key.txt', 'w') as f:
    f.write(keypair.private_key_hex)
```

## Testing

### Using the Launcher (Recommended)

```bash
# Run all tests through the launcher
python domp_launcher.py test

# Or through interactive menu (option 9)
python domp_launcher.py
```

The launcher automatically:
- Starts required services (LND + Web API)
- Checks wallet status
- Runs all 11 comprehensive tests
- Provides detailed results

### Manual Testing

```bash
# Run individual tests
python test_pow.py
python test_lightning_escrow.py  
python test_complete_domp_flow.py

# Run master test suite
python run_all_tests.py
```

### Test Categories

✅ **Core & Crypto** (1/1): PoW, signatures, validation
✅ **Lightning Network** (5/5): LND client, escrow, payments  
✅ **Network Integration** (1/1): Nostr relay compatibility
✅ **Web API** (2/2): FastAPI endpoints, WebSocket updates
✅ **Complete Flows** (2/2): End-to-end marketplace transactions

## Development

### Code Style

```bash
# Format code
black domp/

# Type checking  
mypy domp/

# Linting
flake8 domp/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Security Considerations

- Private keys are never transmitted over the network
- All events are cryptographically signed
- Event validation prevents malformed data
- Anti-spam mechanisms prevent network abuse

## Lightning Network Integration

### Prerequisites

Ensure LND is installed and configured for testnet:

```bash
# Install LND (if not already installed)
# See: https://docs.lightning.engineering/lightning-network-tools/lnd/installation

# Start LND on testnet (automatically handled by launcher)
lnd --bitcoin.testnet --bitcoin.node=neutrino
```

### Lightning Features

✅ **Real LND Integration**: Direct gRPC connection to Lightning Network Daemon
✅ **Invoice Generation**: Create real Bitcoin testnet invoices  
✅ **Escrow Management**: HTLC-based trustless escrow contracts
✅ **Payment Verification**: Real Lightning payment confirmation
✅ **Wallet Management**: Automatic wallet unlock and balance checking

### Usage with Launcher

The launcher handles all Lightning operations:

```bash
python domp_launcher.py start    # Starts LND + Web API
python domp_launcher.py unlock   # Unlocks LND wallet  
python domp_launcher.py test     # Tests Lightning integration
```

### Manual Lightning Operations

```bash
# Check LND status
lncli --network=testnet getinfo

# Unlock wallet
lncli --network=testnet unlock

# Create invoice  
lncli --network=testnet addinvoice --amt 1000

# Pay invoice
lncli --network=testnet payinvoice <payment_request>
```

## Documentation

- **[SETUP.md](SETUP.md)** - Quick setup guide (5 minute setup)
- **[LAUNCHER.md](LAUNCHER.md)** - Complete launcher documentation
- **[API Documentation](web_api.py)** - FastAPI endpoint reference
- **[Test Documentation](run_all_tests.py)** - Test suite overview

## Examples

See the test files for complete usage examples:

- `test_complete_domp_flow.py` - End-to-end marketplace transaction
- `test_lightning_escrow.py` - Lightning escrow management  
- `test_web_lightning.py` - Web API Lightning integration
- `test_nostr_relays.py` - Nostr relay compatibility

## License

MIT License - see LICENSE file for details.