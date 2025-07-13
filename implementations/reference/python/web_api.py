#!/usr/bin/env python3
"""
DOMP Web API
FastAPI backend for the DOMP marketplace web interface.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import json
import asyncio
import time
import sys
import os
from typing import List, Dict, Optional, Any
from dataclasses import asdict

sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import KeyPair, generate_pow_nonce
from domp.events import ProductListing, BidSubmission, BidAcceptance, PaymentConfirmation, ReceiptConfirmation
from domp.lightning import LightningEscrowManager, MockLightningNode, LightningClientFactory, EscrowState
from domp.reputation import ReputationSystem, create_reputation_from_receipt_confirmation
from domp.validation import validate_event


# Pydantic models for API requests/responses
class CreateListingRequest(BaseModel):
    product_name: str
    description: str
    price_sats: int
    category: str = "general"

class PlaceBidRequest(BaseModel):
    listing_id: str
    bid_amount_sats: int
    message: str = ""

class ConfirmReceiptRequest(BaseModel):
    transaction_id: str
    rating: int
    feedback: str = ""
    item_condition: str = "as_described"

class CreateInvoiceRequest(BaseModel):
    amount_sats: int
    description: str = ""

class PayInvoiceRequest(BaseModel):
    invoice: str


# Global application state (in production, use proper database)
class DOMPWebState:
    def __init__(self):
        # User identity
        self.keypair: Optional[KeyPair] = None
        self.lightning_client = None
        
        # Core DOMP components
        self.escrow_manager = LightningEscrowManager()
        self.reputation_system = ReputationSystem()
        
        # Data storage
        self.listings: Dict[str, Dict] = {}
        self.bids: Dict[str, Dict] = {}
        self.transactions: Dict[str, Dict] = {}
        self.my_transactions: List[str] = []
        
        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []
        
        # Initialize sample data
        self.load_sample_data()
        
        # Initialize Lightning client
        self.initialize_lightning_client()
    
    def load_identity(self):
        """Load or create user identity."""
        if os.path.exists("domp_web_identity.json"):
            try:
                with open("domp_web_identity.json", "r") as f:
                    data = json.load(f)
                    self.keypair = KeyPair(private_key=bytes.fromhex(data["private_key"]))
                    return True
            except Exception:
                pass
        
        # Create new identity
        self.keypair = KeyPair()
        try:
            with open("domp_web_identity.json", "w") as f:
                json.dump({
                    "private_key": self.keypair.private_key_hex,
                    "public_key": self.keypair.public_key_hex
                }, f)
        except Exception:
            pass
        
        return False
    
    def initialize_lightning_client(self):
        """Initialize Lightning client (separate from identity loading)."""
        try:
            self.lightning_client = LightningClientFactory.create_client(use_real=True)
            print("✅ Using real Lightning client (LND)")
        except Exception as e:
            print(f"⚠️  Real Lightning client failed, using mock: {e}")
            self.lightning_client = LightningClientFactory.create_client(use_real=False)
    
    def load_sample_data(self):
        """Load sample marketplace data."""
        # Create sample sellers
        alice = KeyPair()
        bob = KeyPair()
        charlie = KeyPair()
        
        # Sample listings
        sample_listings = [
            {
                "seller": alice,
                "product_name": "Digital Camera DSLR",
                "description": "Professional 24MP camera with 50mm lens, excellent condition. Includes battery, charger, and camera bag.",
                "price_sats": 75_000_000,
                "category": "electronics"
            },
            {
                "seller": alice,
                "product_name": "Gaming Laptop",
                "description": "High-performance gaming laptop with RTX 4070, 32GB RAM, 1TB SSD. Perfect for gaming and development.",
                "price_sats": 120_000_000,
                "category": "computers"
            },
            {
                "seller": bob,
                "product_name": "iPhone 15 Pro",
                "description": "Latest iPhone 15 Pro, unlocked, 256GB storage. Excellent condition with original box.",
                "price_sats": 50_000_000,
                "category": "electronics"
            },
            {
                "seller": bob,
                "product_name": "MacBook Air M3",
                "description": "Brand new MacBook Air with M3 chip, 16GB RAM, 512GB SSD. Still in original packaging.",
                "price_sats": 85_000_000,
                "category": "computers"
            },
            {
                "seller": charlie,
                "product_name": "Bitcoin Hardware Wallet",
                "description": "Secure Bitcoin hardware wallet device, brand new and unopened. Supports multiple cryptocurrencies.",
                "price_sats": 8_000_000,
                "category": "crypto"
            },
            {
                "seller": charlie,
                "product_name": "Vintage Vinyl Collection",
                "description": "Rare collection of vintage vinyl records from the 70s-80s. Over 50 classic albums in excellent condition.",
                "price_sats": 25_000_000,
                "category": "collectibles"
            }
        ]
        
        # Create listings
        for item in sample_listings:
            listing = ProductListing(
                product_name=item["product_name"],
                description=item["description"],
                price_satoshis=item["price_sats"],
                category=item["category"],
                seller_collateral_satoshis=item["price_sats"] // 10,
                listing_id=f"item_{int(time.time())}_{len(self.listings)}"
            )
            listing.sign(item["seller"])
            
            self.listings[listing.id] = {
                "event": listing.to_dict(),
                "seller_keypair": item["seller"]
            }
        
        # Add sample reputation data
        self.add_sample_reputation()
    
    def add_sample_reputation(self):
        """Add sample reputation data."""
        sample_scores = [
            {
                "seller_pubkey": list(self.listings.values())[0]["seller_keypair"].public_key_hex,
                "scores": [(5, 80_000_000), (4, 50_000_000), (5, 120_000_000), (5, 30_000_000), (4, 45_000_000)]
            },
            {
                "seller_pubkey": list(self.listings.values())[2]["seller_keypair"].public_key_hex,
                "scores": [(4, 40_000_000), (3, 25_000_000), (4, 35_000_000)]
            }
        ]
        
        for seller_data in sample_scores:
            for rating, amount in seller_data["scores"]:
                from domp.reputation import ReputationScore
                score = ReputationScore(
                    transaction_id=f"sample_{int(time.time())}",
                    reviewer_pubkey=KeyPair().public_key_hex,
                    reviewed_pubkey=seller_data["seller_pubkey"],
                    overall_rating=rating,
                    item_quality=rating,
                    shipping_speed=rating,
                    communication=rating,
                    payment_reliability=5,
                    transaction_amount_sats=amount,
                    verified_purchase=True,
                    escrow_completed=True
                )
                self.reputation_system.add_reputation_score(score)
    
    async def broadcast_update(self, message: dict):
        """Broadcast update to all connected WebSocket clients."""
        if self.websocket_connections:
            disconnected = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append(websocket)
            
            # Remove disconnected clients
            for ws in disconnected:
                self.websocket_connections.remove(ws)


# Initialize global state
app_state = DOMPWebState()

# FastAPI app
app = FastAPI(title="DOMP Marketplace API", version="1.0.0")

# Serve static files
static_dir = "/home/lando/projects/fromperdomp-poc/implementations/reference/python/static"
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Startup handled in main function to avoid deprecation warning


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main web interface."""
    return FileResponse("/home/lando/projects/fromperdomp-poc/implementations/reference/python/static/index.html")


# Identity and wallet endpoints
@app.get("/api/identity")
async def get_identity():
    """Get user identity information."""
    if not app_state.keypair:
        app_state.load_identity()
    
    try:
        lightning_balance = await get_lightning_balance_safe()
        print(f"Lightning balance result: {lightning_balance} (type: {type(lightning_balance)})")
        
        result = {
            "pubkey": app_state.keypair.public_key_hex,
            "pubkey_short": app_state.keypair.public_key_hex[:16] + "...",
            "lightning_balance": lightning_balance
        }
        print(f"Identity result: {result}")
        return result
    except Exception as e:
        print(f"Error in get_identity: {e}")
        return {
            "pubkey": app_state.keypair.public_key_hex if app_state.keypair else "unknown",
            "pubkey_short": "unknown",
            "lightning_balance": 0
        }


async def get_lightning_balance_safe():
    """Get Lightning balance with proper error handling."""
    if not app_state.lightning_client:
        return 0
    
    try:
        # Check if it's a mock client (MockLightningNode)
        if hasattr(app_state.lightning_client, 'node_id'):
            # Mock client (synchronous)
            balance = app_state.lightning_client.get_balance()
            return int(balance) if balance is not None else 0
        else:
            # Real client (asynchronous) - try to connect first
            try:
                if not hasattr(app_state.lightning_client, '_channel') or not app_state.lightning_client._channel:
                    await app_state.lightning_client.connect()
                balance = await app_state.lightning_client.get_balance()
                return int(balance) if balance is not None else 0
            except Exception as real_error:
                print(f"Real Lightning client failed: {real_error}")
                return 0
    except Exception as e:
        print(f"Failed to get Lightning balance: {e}")
        return 0


@app.get("/api/wallet/balance")
async def get_wallet_balance():
    """Get Lightning wallet balance."""
    if not app_state.lightning_client:
        raise HTTPException(status_code=400, detail="Lightning client not initialized")
    
    balance_sats = await get_lightning_balance_safe()
    return {
        "balance_sats": balance_sats,
        "balance_btc": balance_sats / 100_000_000
    }


@app.post("/api/invoices")
async def create_lightning_invoice(request: CreateInvoiceRequest):
    """Create a Lightning invoice for DOMP transactions."""
    if not app_state.lightning_client:
        raise HTTPException(status_code=400, detail="Lightning client not initialized")
    
    try:
        # Handle both real and mock clients
        if hasattr(app_state.lightning_client, 'node_id'):
            # Mock client (synchronous)
            invoice_id = app_state.lightning_client.create_invoice(
                amount_sats=request.amount_sats,
                description=request.description or "DOMP transaction"
            )
            result = {
                "payment_request": invoice_id,
                "amount_sats": request.amount_sats,
                "description": request.description or "DOMP transaction",
                "client_type": "mock"
            }
            return result
        else:
            # Real client (asynchronous)
            if not hasattr(app_state.lightning_client, '_channel') or not app_state.lightning_client._channel:
                await app_state.lightning_client.connect()
            
            invoice_data = await app_state.lightning_client.create_invoice(
                amount_sats=request.amount_sats,
                description=request.description or "DOMP transaction",
                expiry_seconds=3600  # 1 hour expiry
            )
            
            result = {
                "payment_request": invoice_data["payment_request"],
                "payment_hash": invoice_data["payment_hash"],
                "amount_sats": invoice_data["amount_sats"],
                "description": invoice_data["description"],
                "client_type": "real_lnd"
            }
            return result
    except Exception as e:
        print(f"Failed to create Lightning invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")


# Marketplace endpoints
@app.get("/api/listings")
async def get_listings():
    """Get all marketplace listings with reputation data."""
    listings_with_reputation = []
    
    for listing_id, listing_data in app_state.listings.items():
        event = listing_data["event"]
        content = json.loads(event["content"])
        seller_pubkey = event["pubkey"]
        
        # Get seller reputation
        rep_summary = app_state.reputation_system.get_reputation_summary(seller_pubkey)
        trust_score = app_state.reputation_system.get_trust_score(seller_pubkey)
        
        listings_with_reputation.append({
            "id": listing_id,
            "product_name": content["product_name"],
            "description": content["description"],
            "price_sats": content["price_satoshis"],
            "price_btc": content["price_satoshis"] / 100_000_000,
            "category": content.get("category", "general"),
            "seller_collateral_sats": content.get("seller_collateral_satoshis", 0),
            "seller": {
                "pubkey": seller_pubkey,
                "pubkey_short": seller_pubkey[:16] + "...",
                "rating": rep_summary.get("overall_score", 0.0),
                "total_transactions": rep_summary.get("total_transactions", 0),
                "reliability": rep_summary.get("reliability", "No Data"),
                "trust_score": trust_score
            },
            "created_at": event["created_at"]
        })
    
    # Sort by creation time (newest first)
    listings_with_reputation.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"listings": listings_with_reputation}


@app.get("/api/listings/{listing_id}")
async def get_listing_details(listing_id: str):
    """Get detailed information about a specific listing."""
    if listing_id not in app_state.listings:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing_data = app_state.listings[listing_id]
    event = listing_data["event"]
    content = json.loads(event["content"])
    seller_pubkey = event["pubkey"]
    
    # Get detailed seller reputation
    rep_summary = app_state.reputation_system.get_reputation_summary(seller_pubkey)
    trust_score = app_state.reputation_system.get_trust_score(seller_pubkey)
    
    return {
        "id": listing_id,
        "product_name": content["product_name"],
        "description": content["description"],
        "price_sats": content["price_satoshis"],
        "price_btc": content["price_satoshis"] / 100_000_000,
        "category": content.get("category", "general"),
        "seller_collateral_sats": content.get("seller_collateral_satoshis", 0),
        "seller": {
            "pubkey": seller_pubkey,
            "pubkey_short": seller_pubkey[:16] + "...",
            "rating": rep_summary.get("overall_score", 0.0),
            "total_transactions": rep_summary.get("total_transactions", 0),
            "reliability": rep_summary.get("reliability", "No Data"),
            "trust_score": trust_score,
            "item_quality": rep_summary.get("item_quality"),
            "shipping_speed": rep_summary.get("shipping_speed"),
            "communication": rep_summary.get("communication"),
            "verified_purchases": rep_summary.get("verified_purchases", 0),
            "completed_escrows": rep_summary.get("completed_escrows", 0),
            "unique_reviewers": rep_summary.get("unique_reviewers", 0)
        },
        "created_at": event["created_at"],
        "event": event
    }


@app.post("/api/listings")
async def create_listing(request: CreateListingRequest):
    """Create a new product listing."""
    if not app_state.keypair:
        raise HTTPException(status_code=400, detail="User identity not initialized")
    
    # Create listing
    listing = ProductListing(
        product_name=request.product_name,
        description=request.description,
        price_satoshis=request.price_sats,
        category=request.category,
        seller_collateral_satoshis=request.price_sats // 10,
        listing_id=f"user_item_{int(time.time())}"
    )
    listing.sign(app_state.keypair)
    
    # Store listing
    app_state.listings[listing.id] = {
        "event": listing.to_dict(),
        "seller_keypair": app_state.keypair
    }
    
    # Broadcast update
    await app_state.broadcast_update({
        "type": "new_listing",
        "listing_id": listing.id,
        "product_name": request.product_name
    })
    
    return {
        "success": True,
        "listing_id": listing.id,
        "message": "Listing created successfully"
    }


@app.post("/api/bids")
async def place_bid(request: PlaceBidRequest):
    """Place a bid on a listing."""
    if not app_state.keypair:
        raise HTTPException(status_code=400, detail="User identity not initialized")
    
    if request.listing_id not in app_state.listings:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Create bid
    bid = BidSubmission(
        product_ref=request.listing_id,
        bid_amount_satoshis=request.bid_amount_sats,
        buyer_collateral_satoshis=request.bid_amount_sats,
        message=request.message or "Interested in purchasing",
        payment_timeout_hours=24
    )
    bid.sign(app_state.keypair)
    
    # Store bid
    app_state.bids[bid.id] = {
        "event": bid.to_dict(),
        "listing_id": request.listing_id,
        "status": "pending"
    }
    
    # Simulate automatic bid acceptance for demo
    success = await simulate_bid_acceptance(bid.id, request.listing_id)
    
    return {
        "success": success,
        "bid_id": bid.id,
        "message": "Bid placed and accepted!" if success else "Bid placed, waiting for acceptance"
    }


async def simulate_bid_acceptance(bid_id: str, listing_id: str):
    """Simulate seller accepting the bid."""
    try:
        bid_data = app_state.bids[bid_id]
        listing_data = app_state.listings[listing_id]
        
        bid_event = bid_data["event"]
        listing_event = listing_data["event"]
        
        bid_content = json.loads(bid_event["content"])
        listing_content = json.loads(listing_event["content"])
        
        # Create Lightning escrow
        escrow = app_state.escrow_manager.create_escrow(
            transaction_id=f"tx_{bid_id[:8]}",
            buyer_pubkey=app_state.keypair.public_key_hex,
            seller_pubkey=listing_event["pubkey"],
            purchase_amount_sats=bid_content["bid_amount_satoshis"],
            buyer_collateral_sats=bid_content["buyer_collateral_satoshis"],
            seller_collateral_sats=listing_content.get("seller_collateral_satoshis", 0)
        )
        
        # Store transaction
        app_state.transactions[escrow.transaction_id] = {
            "status": "escrow_created",
            "escrow": escrow,
            "bid": bid_data,
            "listing": listing_data,
            "created_at": int(time.time())
        }
        
        app_state.my_transactions.append(escrow.transaction_id)
        
        # Broadcast update
        await app_state.broadcast_update({
            "type": "bid_accepted",
            "transaction_id": escrow.transaction_id,
            "product_name": listing_content["product_name"]
        })
        
        return True
        
    except Exception as e:
        print(f"Error in bid acceptance simulation: {e}")
        return False


@app.get("/api/transactions")
async def get_transactions():
    """Get user's transactions."""
    transactions = []
    
    for tx_id in app_state.my_transactions:
        if tx_id in app_state.transactions:
            tx_data = app_state.transactions[tx_id]
            listing_content = json.loads(tx_data["listing"]["event"]["content"])
            
            transactions.append({
                "id": tx_id,
                "status": tx_data["status"],
                "product_name": listing_content["product_name"],
                "amount_sats": tx_data["escrow"].purchase_amount_sats,
                "amount_btc": tx_data["escrow"].purchase_amount_sats / 100_000_000,
                "created_at": tx_data["created_at"],
                "escrow_state": tx_data["escrow"].state.value
            })
    
    return {"transactions": transactions}


@app.get("/api/reputation/sellers")
async def get_top_sellers():
    """Get top sellers by reputation."""
    seller_pubkeys = set(data["event"]["pubkey"] for data in app_state.listings.values())
    comparison = app_state.reputation_system.compare_sellers(list(seller_pubkeys))
    
    sellers = []
    for seller in comparison[:10]:  # Top 10
        if seller.get("total_transactions", 0) > 0:
            # Find the actual pubkey
            actual_pubkey = next(
                (pubkey for pubkey in seller_pubkeys if pubkey.startswith(seller["pubkey"][:16])),
                None
            )
            if actual_pubkey:
                trust_score = app_state.reputation_system.get_trust_score(actual_pubkey)
                sellers.append({
                    "pubkey": actual_pubkey,
                    "pubkey_short": seller["pubkey"],
                    "reliability": seller["reliability"],
                    "overall_score": seller["overall_score"],
                    "total_transactions": seller["total_transactions"],
                    "total_volume_btc": seller["total_volume_btc"],
                    "trust_score": trust_score
                })
    
    return {"sellers": sellers}


@app.get("/api/reputation/analytics")
async def get_reputation_analytics():
    """Get marketplace reputation analytics."""
    all_sellers = set(data["event"]["pubkey"] for data in app_state.listings.values())
    
    reputation_data = []
    for seller_pubkey in all_sellers:
        rep = app_state.reputation_system.get_reputation_summary(seller_pubkey)
        reputation_data.append(rep)
    
    with_data = [r for r in reputation_data if r.get('total_transactions', 0) > 0]
    
    analytics = {
        "total_sellers": len(all_sellers),
        "total_listings": len(app_state.listings),
        "sellers_with_data": len(with_data)
    }
    
    if with_data:
        analytics.update({
            "average_rating": sum(r.get('overall_score', 0) for r in with_data) / len(with_data),
            "average_transactions": sum(r.get('total_transactions', 0) for r in with_data) / len(with_data),
            "total_volume_btc": sum(r.get('total_volume_btc', 0) for r in with_data),
            "rating_distribution": {
                "excellent": sum(1 for r in with_data if r.get('overall_score', 0) >= 4.5),
                "good": sum(1 for r in with_data if 3.5 <= r.get('overall_score', 0) < 4.5),
                "average": sum(1 for r in with_data if 2.5 <= r.get('overall_score', 0) < 3.5),
                "poor": sum(1 for r in with_data if r.get('overall_score', 0) < 2.5)
            }
        })
    
    return analytics


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time marketplace updates."""
    await websocket.accept()
    app_state.websocket_connections.append(websocket)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to DOMP marketplace updates"
        })
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            await websocket.receive_text()
            await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        if websocket in app_state.websocket_connections:
            app_state.websocket_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    # Initialize app state on startup
    app_state.load_identity()
    print("🚀 Starting DOMP Marketplace Web Server...")
    print("📱 Open your browser to: http://localhost:8080")
    uvicorn.run("web_api:app", host="0.0.0.0", port=8080, reload=True)