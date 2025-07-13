# DOMP API Documentation

Complete API reference for the DOMP (Decentralized Online Marketplace Protocol) implementation.

## Table of Contents

- [Authentication](#authentication)
- [REST API Endpoints](#rest-api-endpoints)
- [WebSocket API](#websocket-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Authentication

DOMP uses cryptographic keypairs for identity and authentication. All API operations that modify state require valid signatures.

### Identity Management

The client automatically generates or loads a keypair on first use:
- **Storage**: `domp_web_identity.json` (web) or `domp_identity.json` (CLI)
- **Key Format**: secp256k1 private/public key pairs
- **Encoding**: Hexadecimal strings

### Request Signing

All write operations require cryptographic signatures:
```python
# Event signing example
event.sign(keypair)
```

## REST API Endpoints

### Base URL
```
http://localhost:8080/api
```

### Identity & Wallet

#### Get User Identity
```http
GET /api/identity
```

**Response:**
```json
{
  "pubkey": "02a1b2c3...",
  "pubkey_short": "02a1b2c3...",
  "lightning_balance": 1000000
}
```

#### Get Wallet Balance
```http
GET /api/wallet/balance
```

**Response:**
```json
{
  "balance_sats": 1000000,
  "balance_btc": 0.01
}
```

### Marketplace Listings

#### Get All Listings
```http
GET /api/listings
```

**Query Parameters:**
- `category` (optional): Filter by category

**Response:**
```json
{
  "listings": [
    {
      "id": "item_1234567890_1",
      "product_name": "Digital Camera DSLR",
      "description": "Professional 24MP camera...",
      "price_sats": 75000000,
      "price_btc": 0.75,
      "category": "electronics",
      "seller_collateral_sats": 7500000,
      "seller": {
        "pubkey": "02a1b2c3...",
        "pubkey_short": "02a1b2c3...",
        "rating": 4.5,
        "total_transactions": 15,
        "reliability": "Excellent",
        "trust_score": 0.892
      },
      "created_at": 1703894400
    }
  ]
}
```

#### Get Listing Details
```http
GET /api/listings/{listing_id}
```

**Response:**
```json
{
  "id": "item_1234567890_1",
  "product_name": "Digital Camera DSLR",
  "description": "Professional 24MP camera with 50mm lens...",
  "price_sats": 75000000,
  "price_btc": 0.75,
  "category": "electronics",
  "seller_collateral_sats": 7500000,
  "seller": {
    "pubkey": "02a1b2c3...",
    "pubkey_short": "02a1b2c3...",
    "rating": 4.5,
    "total_transactions": 15,
    "reliability": "Excellent",
    "trust_score": 0.892,
    "item_quality": 4.6,
    "shipping_speed": 4.4,
    "communication": 4.5,
    "verified_purchases": 12,
    "completed_escrows": 15,
    "unique_reviewers": 14
  },
  "created_at": 1703894400,
  "event": {
    "id": "event_hash...",
    "pubkey": "02a1b2c3...",
    "created_at": 1703894400,
    "kind": 300,
    "content": "{...}",
    "sig": "signature..."
  }
}
```

#### Create New Listing
```http
POST /api/listings
```

**Request Body:**
```json
{
  "product_name": "iPhone 15 Pro",
  "description": "Latest iPhone 15 Pro, unlocked, 256GB storage",
  "price_sats": 50000000,
  "category": "electronics"
}
```

**Response:**
```json
{
  "success": true,
  "listing_id": "user_item_1703894400",
  "message": "Listing created successfully"
}
```

### Bidding & Transactions

#### Place Bid
```http
POST /api/bids
```

**Request Body:**
```json
{
  "listing_id": "item_1234567890_1",
  "bid_amount_sats": 75000000,
  "message": "Interested in purchasing this camera"
}
```

**Response:**
```json
{
  "success": true,
  "bid_id": "bid_hash...",
  "message": "Bid placed and accepted!"
}
```

#### Get User Transactions
```http
GET /api/transactions
```

**Response:**
```json
{
  "transactions": [
    {
      "id": "tx_bid_12345",
      "status": "escrow_created",
      "product_name": "Digital Camera DSLR",
      "amount_sats": 75000000,
      "amount_btc": 0.75,
      "created_at": 1703894400,
      "escrow_state": "funded"
    }
  ]
}
```

### Reputation System

#### Get Reputation Analytics
```http
GET /api/reputation/analytics
```

**Response:**
```json
{
  "total_sellers": 3,
  "total_listings": 6,
  "sellers_with_data": 2,
  "average_rating": 4.2,
  "average_transactions": 9.0,
  "total_volume_btc": 2.45,
  "rating_distribution": {
    "excellent": 2,
    "good": 0,
    "average": 0,
    "poor": 0
  }
}
```

#### Get Top Sellers
```http
GET /api/reputation/sellers
```

**Response:**
```json
{
  "sellers": [
    {
      "pubkey": "02a1b2c3...",
      "pubkey_short": "02a1b2c3...",
      "reliability": "Excellent",
      "overall_score": 4.5,
      "total_transactions": 15,
      "total_volume_btc": 1.25,
      "trust_score": 0.892
    }
  ]
}
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');
```

### Message Types

#### Connection Acknowledgment
```json
{
  "type": "connected",
  "message": "Connected to DOMP marketplace updates"
}
```

#### New Listing Notification
```json
{
  "type": "new_listing",
  "listing_id": "user_item_1703894400",
  "product_name": "iPhone 15 Pro"
}
```

#### Bid Acceptance Notification
```json
{
  "type": "bid_accepted",
  "transaction_id": "tx_bid_12345",
  "product_name": "Digital Camera DSLR"
}
```

#### Keep-Alive
```json
{
  "type": "pong"
}
```

## Data Models

### Listing Object
```typescript
interface Listing {
  id: string;
  product_name: string;
  description: string;
  price_sats: number;
  price_btc: number;
  category: string;
  seller_collateral_sats: number;
  seller: SellerInfo;
  created_at: number;
}
```

### Seller Info Object
```typescript
interface SellerInfo {
  pubkey: string;
  pubkey_short: string;
  rating: number;           // 0-5 scale
  total_transactions: number;
  reliability: string;      // "Excellent" | "Good" | "New Seller" | "Limited Data"
  trust_score: number;      // 0-1 scale
  item_quality?: number;    // Optional detailed metrics
  shipping_speed?: number;
  communication?: number;
  verified_purchases?: number;
  completed_escrows?: number;
  unique_reviewers?: number;
}
```

### Transaction Object
```typescript
interface Transaction {
  id: string;
  status: string;           // "escrow_created" | "payment_sent" | "completed"
  product_name: string;
  amount_sats: number;
  amount_btc: number;
  created_at: number;
  escrow_state: string;     // "pending" | "funded" | "released" | "refunded"
}
```

### Event Object (DOMP Protocol)
```typescript
interface DOMPEvent {
  id: string;               // Event hash
  pubkey: string;          // Author public key
  created_at: number;      // Unix timestamp
  kind: number;            // Event type (300, 301, 303, 311, 313)
  content: string;         // JSON-encoded event data
  tags: string[][];        // Event tags
  sig: string;             // Schnorr signature
}
```

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

### Error Types

#### Validation Errors
```json
{
  "detail": "Invalid bid amount",
  "status_code": 422,
  "error_type": "validation_error"
}
```

#### Authentication Errors
```json
{
  "detail": "User identity not initialized",
  "status_code": 400,
  "error_type": "authentication_error"
}
```

#### Resource Errors
```json
{
  "detail": "Listing not found",
  "status_code": 404,
  "error_type": "resource_error"
}
```

## Rate Limiting

Currently no rate limiting is implemented in the reference implementation. For production deployments, consider:

- **Listing Creation**: 10 per hour per user
- **Bid Submission**: 100 per hour per user  
- **API Queries**: 1000 per hour per IP
- **WebSocket Connections**: 5 per IP

## Examples

### JavaScript Client Example

```javascript
class DOMPClient {
    constructor(baseUrl = 'http://localhost:8080/api') {
        this.baseUrl = baseUrl;
    }
    
    async getListings() {
        const response = await fetch(`${this.baseUrl}/listings`);
        return response.json();
    }
    
    async createListing(listing) {
        const response = await fetch(`${this.baseUrl}/listings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(listing)
        });
        return response.json();
    }
    
    async placeBid(bid) {
        const response = await fetch(`${this.baseUrl}/bids`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bid)
        });
        return response.json();
    }
}

// Usage
const client = new DOMPClient();
const listings = await client.getListings();
```

### Python Client Example

```python
import requests
import json

class DOMPClient:
    def __init__(self, base_url="http://localhost:8080/api"):
        self.base_url = base_url
    
    def get_listings(self):
        response = requests.get(f"{self.base_url}/listings")
        return response.json()
    
    def create_listing(self, listing_data):
        response = requests.post(
            f"{self.base_url}/listings",
            json=listing_data
        )
        return response.json()
    
    def place_bid(self, bid_data):
        response = requests.post(
            f"{self.base_url}/bids",
            json=bid_data
        )
        return response.json()

# Usage
client = DOMPClient()
listings = client.get_listings()
```

### cURL Examples

#### Get Listings
```bash
curl -X GET http://localhost:8080/api/listings
```

#### Create Listing
```bash
curl -X POST http://localhost:8080/api/listings \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Test Item",
    "description": "A test item for sale",
    "price_sats": 100000,
    "category": "general"
  }'
```

#### Place Bid
```bash
curl -X POST http://localhost:8080/api/bids \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": "item_1234567890_1",
    "bid_amount_sats": 100000,
    "message": "Interested in buying"
  }'
```

## Integration Notes

### Web Frontend Integration
The API is designed to work seamlessly with modern web frameworks:
- CORS enabled for local development
- JSON responses for easy parsing
- WebSocket support for real-time updates
- RESTful design patterns

### Mobile App Integration
- Lightweight JSON responses
- Efficient WebSocket messaging
- Stateless authentication via cryptographic signatures
- Optimized for bandwidth-conscious environments

### Third-Party Integration
- Open API specification available
- Well-defined data models
- Comprehensive error handling
- Extensible event system

---

*This API documentation is maintained alongside the DOMP reference implementation. For protocol-level details, see the [DOMP Improvement Proposals](../protocol/).*