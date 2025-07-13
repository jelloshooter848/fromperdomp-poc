# DOMP - Decentralized Online Marketplace Protocol

A complete protocol for trustless peer-to-peer commerce built on Bitcoin Lightning Network and Nostr.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Protocol Status](https://img.shields.io/badge/Status-Reference%20Implementation-green.svg)]()

## Overview

DOMP enables secure, decentralized marketplaces without intermediaries by combining:
- ⚡ **Bitcoin Lightning Network** for instant payments and trustless escrow via HTLC
- 🌐 **Nostr protocol** for censorship-resistant communication and event broadcasting  
- 🔐 **Cryptographic proofs** for identity, reputation, and transaction verification
- 🛡️ **Decentralized reputation system** with time-decay and verification bonuses

## Key Features

### 🔒 Trustless Escrow
- Lightning HTLC-based escrow without third parties
- Automatic collateral enforcement for buyers and sellers
- Atomic swap guarantees: payment released only on confirmed receipt

### 📊 Reputation System
- Cryptographically verifiable seller ratings
- Time-weighted scoring with decay for sustained performance
- Volume-weighted metrics for transaction significance
- Cross-relay reputation aggregation

### 🌍 Decentralized Architecture  
- No central authority or single point of failure
- Nostr relay network for global event distribution
- Client-side validation and cryptographic verification
- Open protocol enabling multiple marketplace implementations

### ⚡ Lightning Integration
- Instant Bitcoin payments with minimal fees
- Real Lightning Network compatibility (reference uses mock for demo)
- HTLC-based conditional payments tied to delivery confirmation

## Demo Applications

### 🖥️ Web Interface
Modern, responsive marketplace with real-time updates:
```bash
cd implementations/reference/python
python3 web_api.py
# Visit http://localhost:8080
```

### 💻 CLI Client
Full-featured command-line marketplace client:
```bash
cd implementations/reference/python  
python3 domp_marketplace_cli.py
```

## Project Structure

```
fromperdomp-poc/
├── docs/                     # Protocol specifications and guides
│   └── protocol/            # DOMP Improvement Proposals (DIPs)
├── specs/                   # Machine-readable schemas and test vectors  
│   └── event-schemas/       # JSON schemas for DOMP events
├── implementations/         # Reference implementations
│   └── reference/python/    # Complete Python implementation
│       ├── domp/           # Core protocol library
│       ├── static/         # Web interface assets
│       ├── web_api.py      # FastAPI backend
│       └── domp_marketplace_cli.py  # CLI client
└── white-paper.md          # Original protocol specification
```

## Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd fromperdomp-poc/implementations/reference/python

# Setup environment
python3 -m venv domp-env
source domp-env/bin/activate

# Install dependencies
pip install fastapi uvicorn websockets secp256k1 pydantic
```

### Run Demo
```bash
# Start web interface
python3 web_api.py

# Or use CLI client  
python3 domp_marketplace_cli.py
```

## Protocol Specifications

DOMP follows a NIP-style specification format with DOMP Improvement Proposals (DIPs):

- **[DIP-01: Core Events](docs/protocol/dip-01-core-events.md)** - Product listings, bids, and transactions
- **[DIP-02: Transaction Flow](docs/protocol/dip-02-transaction-flow.md)** - Complete purchase workflow  
- **[DIP-03: Lightning Integration](docs/protocol/dip-03-lightning-integration.md)** - HTLC escrow mechanics
- **[DIP-04: Anti-Spam](docs/protocol/dip-04-anti-spam.md)** - Proof-of-work spam prevention

## Event Types

| Kind | Event Type | Description |
|------|------------|-------------|
| 300 | Product Listing | Items for sale with pricing and metadata |
| 301 | Bid Submission | Purchase offers from buyers |
| 303 | Bid Acceptance | Seller acceptance creating escrow |
| 311 | Payment Confirmation | Lightning payment completion |  
| 313 | Receipt Confirmation | Delivery confirmation with rating |

## API Documentation

### REST Endpoints
- `GET /api/listings` - Retrieve marketplace listings
- `POST /api/listings` - Create new product listing
- `POST /api/bids` - Submit purchase bid
- `GET /api/transactions` - Get user transactions
- `GET /api/reputation/analytics` - Marketplace reputation data

### WebSocket Updates
Real-time marketplace events via WebSocket at `/ws`

## Development

### Architecture
- **Protocol Layer**: Event definitions, cryptography, validation
- **Lightning Layer**: HTLC escrow management and payment handling
- **Reputation Layer**: Scoring algorithms and verification
- **Network Layer**: Nostr relay integration and event broadcasting
- **Application Layer**: CLI and web interfaces

### Testing
```bash
# Run protocol tests
python3 -m pytest tests/

# Test with real Nostr relays
python3 test_nostr_integration.py
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup and guidelines
- DIP (DOMP Improvement Proposal) process
- Code style and testing requirements
- Community governance model

## Roadmap

### ✅ Completed
- Core protocol specification and implementation
- Lightning HTLC escrow system  
- Decentralized reputation scoring
- CLI and web marketplace interfaces
- Real Nostr relay integration
- Complete transaction workflow

### 🚧 In Progress
- Comprehensive documentation
- Developer integration guides
- Protocol compliance testing

### 🔮 Future
- Real Lightning Network integration
- Mobile applications
- Multi-language implementations
- Advanced reputation features
- Performance optimizations

## Security Considerations

- All events are cryptographically signed
- Reputation scores are independently verifiable
- Lightning HTLCs provide atomic payment guarantees
- No trusted third parties required for transactions
- Open source for transparency and auditability

## License

MIT License - See [LICENSE](LICENSE) for details.

## Community

- **Protocol Discussion**: [GitHub Issues](https://github.com/your-org/domp/issues)
- **Development**: [Contributing Guide](CONTRIBUTING.md)
- **Specifications**: [DOMP Improvement Proposals](docs/protocol/)

---

*DOMP: Enabling trustless commerce through cryptographic proofs and decentralized infrastructure.*
