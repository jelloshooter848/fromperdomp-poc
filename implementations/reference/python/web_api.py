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
import secrets
from typing import List, Dict, Optional, Any
from dataclasses import asdict

sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import KeyPair, generate_pow_nonce
from domp.events import ProductListing, BidSubmission, BidAcceptance, PaymentConfirmation, ReceiptConfirmation
from domp.lightning import LightningEscrowManager, MockLightningNode, LightningClientFactory, EscrowState
from domp.reputation import ReputationSystem, create_reputation_from_receipt_confirmation
from domp.validation import validate_event
from domp.client import DOMPClient


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
        self.nostr_client: Optional[DOMPClient] = None
        
        # Core DOMP components
        self.escrow_manager = LightningEscrowManager()
        self.reputation_system = ReputationSystem()
        
        # Data storage (will be replaced with Nostr-sourced data)
        self.listings: Dict[str, Dict] = {}
        self.bids: Dict[str, Dict] = {}
        self.transactions: Dict[str, Dict] = {}
        self.my_transactions: List[str] = []
        
        # Nostr event tracking
        self.processed_events: set = set()  # Track processed event IDs
        self.event_processing_task: Optional[asyncio.Task] = None
        
        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []
        
        # Initialize identity first (needed for Nostr client)
        self.load_identity()
        
        # Initialize sample data (temporary - will be replaced by Nostr events)
        self.load_sample_data()
        
        # Initialize clients
        self.initialize_lightning_client()
        self.initialize_nostr_client()
    
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
    
    def initialize_nostr_client(self):
        """Initialize Nostr client for real-time event processing."""
        if not self.keypair:
            print("⚠️  No keypair available for Nostr client")
            return
        
        try:
            # Use popular public relays for multi-computer communication
            relays = [
                "wss://relay.damus.io",
                "wss://nos.lol", 
                "wss://relay.nostr.band",
                "wss://nostr.wine"
            ]
            
            self.nostr_client = DOMPClient(self.keypair, relays)
            print(f"✅ Nostr client initialized with {len(relays)} relays")
            
            # Add event handler for incoming events
            self.nostr_client.add_event_handler(self.handle_nostr_event)
            
        except Exception as e:
            print(f"❌ Failed to initialize Nostr client: {e}")
            self.nostr_client = None
    
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
                "product_name": "Lightning Test Item",
                "description": "Small test item for Lightning Network payment testing. Perfect for testing real Lightning transactions!",
                "price_sats": 100,
                "category": "test"
            },
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
    
    def handle_nostr_event(self, event):
        """Handle incoming Nostr events for cross-computer synchronization."""
        try:
            event_id = event.id if hasattr(event, 'id') else event.get('id')
            
            # Skip if already processed
            if event_id in self.processed_events:
                return
            
            self.processed_events.add(event_id)
            
            # Convert to dict if needed
            event_dict = event.to_dict() if hasattr(event, 'to_dict') else event
            kind = event_dict.get('kind')
            
            print(f"📡 Received Nostr event: kind-{kind}, id: {event_id[:16]}...")
            
            # Process different event types
            if kind == 300:  # Product Listing
                self.process_listing_event(event_dict)
            elif kind == 301:  # Bid Submission
                self.process_bid_event(event_dict)
            elif kind == 303:  # Bid Acceptance
                self.process_bid_acceptance_event(event_dict)
            elif kind == 311:  # Payment Confirmation
                self.process_payment_confirmation_event(event_dict)
            elif kind == 313:  # Receipt Confirmation
                self.process_receipt_event(event_dict)
            elif kind == 321:  # Reputation Feedback
                self.process_reputation_event(event_dict)
            
            # Broadcast update to connected WebSocket clients
            asyncio.create_task(self.broadcast_update({
                "type": "nostr_event",
                "kind": kind,
                "event_id": event_id,
                "source": "external"
            }))
            
        except Exception as e:
            print(f"❌ Error processing Nostr event: {e}")
    
    def process_listing_event(self, event_dict):
        """Process incoming product listing events."""
        try:
            listing_id = event_dict['id']
            
            # Skip our own events
            if event_dict['pubkey'] == self.keypair.public_key_hex:
                return
            
            # Store the listing
            self.listings[listing_id] = {
                "event": event_dict,
                "seller_keypair": None,  # External listing
                "source": "nostr"
            }
            
            content = json.loads(event_dict['content'])
            print(f"📦 New external listing: {content.get('product_name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error processing listing event: {e}")
    
    def process_bid_event(self, event_dict):
        """Process incoming bid submission events."""
        try:
            bid_id = event_dict['id']
            content = json.loads(event_dict['content'])
            
            # Store the bid
            self.bids[bid_id] = {
                "event": event_dict,
                "listing_id": content.get('product_ref'),
                "status": "pending",
                "source": "nostr"
            }
            
            print(f"💰 New external bid: {content.get('bid_amount_satoshis', 0)} sats")
            
        except Exception as e:
            print(f"❌ Error processing bid event: {e}")
    
    def process_bid_acceptance_event(self, event_dict):
        """Process incoming bid acceptance events."""
        try:
            content = json.loads(event_dict['content'])
            bid_ref = content.get('bid_ref')
            ln_invoice = content.get('ln_invoice', '')
            collateral_invoice = content.get('collateral_invoice', '')
            
            print(f"✅ Processing bid acceptance for bid {bid_ref[:16]}...")
            
            # If this is our bid that was accepted, we need to pay the invoices
            if bid_ref in self.bids:
                self.bids[bid_ref]['status'] = 'accepted'
                
                # Create payment information for the buyer
                payment_info = {
                    "bid_id": bid_ref,
                    "ln_invoice": ln_invoice,
                    "collateral_invoice": collateral_invoice,
                    "status": "payment_required"
                }
                
                # Broadcast to UI so buyer can pay invoices
                asyncio.create_task(self.broadcast_update({
                    "type": "bid_accepted_payment_required",
                    "bid_id": bid_ref,
                    "lightning_invoice": ln_invoice,
                    "collateral_invoice": collateral_invoice,
                    "message": "Your bid was accepted! Payment required to complete transaction."
                }))
                
                print(f"💰 Bid {bid_ref[:16]}... accepted - payment invoices available")
            
        except Exception as e:
            print(f"❌ Error processing bid acceptance event: {e}")
    
    def process_payment_confirmation_event(self, event_dict):
        """Process incoming payment confirmation events for cross-computer escrow coordination."""
        try:
            content = json.loads(event_dict['content'])
            bid_ref = content.get('bid_ref')
            payment_proof = content.get('payment_proof', '')
            payment_method = content.get('payment_method', 'lightning_htlc')
            
            print(f"💰 Processing payment confirmation for bid {bid_ref[:16]}...")
            
            # Find the transaction this payment belongs to
            transaction_id = None
            for tx_id, tx_data in self.transactions.items():
                bid_data = tx_data.get("bid", {})
                if bid_data and bid_data.get("event", {}).get("id") == bid_ref:
                    transaction_id = tx_id
                    break
            
            if transaction_id:
                tx_data = self.transactions[transaction_id]
                escrow = tx_data.get("escrow")
                
                if escrow:
                    # Update escrow state with payment confirmation
                    escrow.fund_escrow(
                        transaction_id=transaction_id,
                        buyer_payment_hash=payment_proof[:64],  # Use first 64 chars as hash
                        buyer_collateral_hash="",
                        seller_collateral_hash=""
                    )
                    
                    # Update transaction status
                    tx_data["status"] = "payment_confirmed"
                    
                    print(f"🔒 Updated escrow state for transaction {transaction_id} from remote payment")
                    
                    # Broadcast real-time update
                    asyncio.create_task(self.broadcast_update({
                        "type": "payment_confirmed_remote",
                        "transaction_id": transaction_id,
                        "bid_ref": bid_ref,
                        "payment_method": payment_method,
                        "message": "Payment confirmed from other computer"
                    }))
                else:
                    print(f"⚠️  No escrow found for transaction {transaction_id}")
            else:
                print(f"⚠️  No transaction found for bid {bid_ref[:16]}...")
            
        except Exception as e:
            print(f"❌ Error processing payment confirmation event: {e}")
    
    def process_receipt_event(self, event_dict):
        """Process incoming receipt confirmation events."""
        try:
            content = json.loads(event_dict['content'])
            payment_ref = content.get('payment_ref')
            
            # Update transaction status if we're tracking it
            for tx_id, tx_data in self.transactions.items():
                if tx_data.get('escrow') and hasattr(tx_data['escrow'], 'transaction_id'):
                    if tx_data['escrow'].transaction_id == payment_ref:
                        tx_data['status'] = 'completed'
                        break
            
            print(f"✅ Receipt confirmed: {payment_ref[:16]}...")
            
        except Exception as e:
            print(f"❌ Error processing receipt event: {e}")
    
    def process_reputation_event(self, event_dict):
        """Process incoming reputation feedback events."""
        try:
            content = json.loads(event_dict['content'])
            print(f"⭐ New reputation feedback: {content.get('rating', 0)} stars")
            
            # Add to reputation system
            # TODO: Implement proper reputation event processing
            
        except Exception as e:
            print(f"❌ Error processing reputation event: {e}")
    
    async def start_nostr_processing(self):
        """Start background Nostr event processing."""
        if not self.nostr_client:
            print("⚠️  No Nostr client available for event processing")
            return
        
        try:
            print("🚀 Starting Nostr client and event processing...")
            
            # Connect to relays
            await self.nostr_client.connect()
            
            # Subscribe to DOMP event types
            filters = [
                {"kinds": [300, 301, 303, 311, 313, 321]},  # Core DOMP events including payment confirmations
                {"since": int(time.time()) - 3600}           # Last hour
            ]
            
            await self.nostr_client.subscribe("domp_events", filters)
            print("✅ Subscribed to DOMP events on Nostr relays")
            
            # Keep processing events
            while True:
                await asyncio.sleep(1)
                # Event processing happens via callbacks
                
        except Exception as e:
            print(f"❌ Error in Nostr processing: {e}")
    
    async def stop_nostr_processing(self):
        """Stop Nostr event processing."""
        if self.event_processing_task:
            self.event_processing_task.cancel()
            try:
                await self.event_processing_task
            except asyncio.CancelledError:
                pass
        
        if self.nostr_client:
            await self.nostr_client.disconnect()
            print("✅ Nostr client disconnected")
    
    async def get_listings_from_nostr(self, limit: int = 100) -> List[Dict]:
        """Get product listings from Nostr relays instead of memory."""
        if not self.nostr_client:
            print("⚠️  No Nostr client available - using sample data")
            return list(self.listings.values())
        
        try:
            # Get recent product listings from Nostr
            events = await self.nostr_client.get_product_listings(limit=limit)
            listings = []
            
            for event in events:
                try:
                    content = json.loads(event.content)
                    listings.append({
                        "event": event.to_dict(),
                        "seller_keypair": None  # Remote seller
                    })
                except json.JSONDecodeError:
                    print(f"Invalid JSON in listing event {event.id}")
                    continue
            
            # Include local sample data for demo purposes
            listings.extend(list(self.listings.values()))
            return listings
            
        except Exception as e:
            print(f"Error fetching listings from Nostr: {e}")
            # Fallback to sample data
            return list(self.listings.values())
    
    async def get_bids_from_nostr(self, listing_id: str = None) -> List[Dict]:
        """Get bid submissions from Nostr relays instead of memory.""" 
        if not self.nostr_client:
            return list(self.bids.values())
        
        try:
            # Build filters for bid events
            filters = [{"kinds": [301]}]
            if listing_id:
                filters[0]["#ref"] = [listing_id]
            
            events = await self.nostr_client.get_events(filters, timeout=5)
            bids = []
            
            for event in events:
                try:
                    content = json.loads(event.content)
                    bids.append({
                        "event": event.to_dict(),
                        "listing_id": content.get("product_ref"),
                        "status": "pending"  # Default status
                    })
                except json.JSONDecodeError:
                    continue
            
            return bids
            
        except Exception as e:
            print(f"Error fetching bids from Nostr: {e}")
            return list(self.bids.values())
    
    async def get_transactions_from_nostr(self, pubkey: str = None) -> List[Dict]:
        """Get transaction events from Nostr relays instead of memory."""
        if not self.nostr_client:
            return []
        
        try:
            # Get transaction-related events (bids, acceptances, payments, receipts)
            filters = [
                {"kinds": [301, 303, 311, 313]},  # Bid, acceptance, payment, receipt
            ]
            
            if pubkey:
                filters[0]["authors"] = [pubkey]
            
            events = await self.nostr_client.get_events(filters, timeout=5)
            
            # Group events by transaction/product
            transactions = {}
            
            for event in events:
                try:
                    content = json.loads(event.content)
                    
                    if event.kind == 301:  # Bid
                        product_ref = content.get("product_ref")
                        if product_ref:
                            if product_ref not in transactions:
                                transactions[product_ref] = {"bids": [], "acceptances": [], "payments": [], "receipts": []}
                            transactions[product_ref]["bids"].append(event.to_dict())
                    
                    elif event.kind == 303:  # Bid acceptance
                        bid_ref = content.get("bid_ref")
                        # Find the product this bid belongs to
                        for tx_id, tx_data in transactions.items():
                            for bid in tx_data["bids"]:
                                if bid["id"] == bid_ref:
                                    transactions[tx_id]["acceptances"].append(event.to_dict())
                                    break
                    
                    # Similar logic for payments and receipts...
                    
                except json.JSONDecodeError:
                    continue
            
            return list(transactions.values())
            
        except Exception as e:
            print(f"Error fetching transactions from Nostr: {e}")
            return []


# Initialize global state
app_state = DOMPWebState()

# FastAPI app
app = FastAPI(title="DOMP Marketplace API", version="1.0.0")

# Serve static files
static_dir = "/home/lando/projects/fromperdomp-poc/implementations/reference/python/static"
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize Nostr client on application startup."""
    if app_state.nostr_client:
        # Start background Nostr processing
        app_state.event_processing_task = asyncio.create_task(
            app_state.start_nostr_processing()
        )
        print("🚀 Background Nostr processing started")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up Nostr client on application shutdown."""
    await app_state.stop_nostr_processing()
    print("🛑 Application shutdown complete")


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


@app.post("/api/payments")
async def pay_lightning_invoice(request: PayInvoiceRequest):
    """Pay a Lightning invoice."""
    if not app_state.lightning_client:
        raise HTTPException(status_code=400, detail="Lightning client not initialized")
    
    try:
        # Handle both real and mock clients
        if hasattr(app_state.lightning_client, 'node_id'):
            # Mock client (synchronous) - need to parse invoice for amount
            # For mock, we'll simulate payment
            payment_hash = secrets.token_hex(32)
            
            result = {
                "payment_preimage": secrets.token_hex(32),
                "payment_hash": payment_hash,
                "payment_route": [],
                "fee_sat": 1,
                "fee_msat": 1000,
                "value_sat": 1000,  # Would parse from invoice in real implementation
                "value_msat": 1000000,
                "status": "SUCCEEDED",
                "client_type": "mock"
            }
            
            # Publish payment confirmation event to Nostr for cross-computer escrow coordination
            await publish_payment_confirmation(request.invoice, result)
            
            return result
        else:
            # Real client (asynchronous)
            if not hasattr(app_state.lightning_client, '_channel') or not app_state.lightning_client._channel:
                await app_state.lightning_client.connect()
            
            payment_result = await app_state.lightning_client.pay_invoice(
                payment_request=request.invoice,
                timeout_seconds=60
            )
            
            result = {
                "payment_preimage": payment_result["payment_preimage"],
                "payment_hash": payment_result["payment_hash"],
                "payment_route": payment_result["payment_route"],
                "fee_sat": payment_result["fee_sat"],
                "fee_msat": payment_result["fee_msat"],
                "value_sat": payment_result["value_sat"],
                "value_msat": payment_result["value_msat"],
                "status": payment_result["status"],
                "payment_error": payment_result.get("payment_error", ""),
                "client_type": "real_lnd"
            }
            
            # Publish payment confirmation event to Nostr for cross-computer escrow coordination
            if payment_result["status"] == "SUCCEEDED":
                await publish_payment_confirmation(request.invoice, payment_result)
            
            return result
    except Exception as e:
        print(f"Failed to pay Lightning invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pay invoice: {str(e)}")


async def publish_payment_confirmation(invoice: str, payment_result: Dict[str, Any]):
    """Publish payment confirmation event to Nostr for cross-computer escrow coordination."""
    try:
        if not app_state.nostr_client or not app_state.keypair:
            print("⚠️  Cannot publish payment confirmation - missing Nostr client or keypair")
            return
        
        # Find which transaction this payment belongs to by matching invoice
        transaction_id = None
        bid_ref = None
        
        for tx_id, tx_data in app_state.transactions.items():
            lightning_invoices = tx_data.get("lightning_invoices", {})
            purchase_invoice = lightning_invoices.get("purchase", {}).get("payment_request", "")
            
            if purchase_invoice == invoice:
                transaction_id = tx_id
                # Get bid reference from transaction
                bid_data = tx_data.get("bid", {})
                if bid_data:
                    bid_ref = bid_data.get("event", {}).get("id")
                break
        
        if not transaction_id or not bid_ref:
            print(f"⚠️  Could not find transaction for invoice {invoice[:20]}...")
            return
        
        # Create payment confirmation event
        from domp.events import PaymentConfirmation
        payment_confirmation = PaymentConfirmation(
            bid_ref=bid_ref,
            payment_proof=payment_result.get("payment_preimage", ""),
            payment_method="lightning_htlc",
            collateral_proof="",  # Would include collateral payment proof if applicable
            escrow_timeout_blocks=144
        )
        payment_confirmation.sign(app_state.keypair)
        
        # Publish to Nostr relays
        from domp.events import create_event_from_dict
        nostr_event = create_event_from_dict(payment_confirmation.to_dict())
        published = await app_state.nostr_client.publish_event(nostr_event)
        
        if published:
            print(f"✅ Published payment confirmation {payment_confirmation.id[:16]}... to Nostr relays")
            
            # Update local escrow state
            if transaction_id in app_state.transactions:
                tx_data = app_state.transactions[transaction_id]
                escrow = tx_data.get("escrow")
                if escrow:
                    # Fund the escrow with payment confirmation
                    escrow.fund_escrow(
                        transaction_id=transaction_id,
                        buyer_payment_hash=payment_result.get("payment_hash", ""),
                        buyer_collateral_hash="",  # Would include if collateral was paid
                        seller_collateral_hash=""  # Would include if seller collateral exists
                    )
                    print(f"🔒 Updated escrow state for transaction {transaction_id}")
            
            # Broadcast real-time update
            await app_state.broadcast_update({
                "type": "payment_confirmed",
                "transaction_id": transaction_id,
                "payment_hash": payment_result.get("payment_hash", ""),
                "status": "payment_confirmed"
            })
        else:
            print(f"⚠️  Failed to publish payment confirmation to Nostr")
            
    except Exception as e:
        print(f"❌ Error publishing payment confirmation: {e}")


@app.post("/api/transactions/{tx_id}/complete-payment")
async def complete_payment_for_testing(tx_id: str):
    """Complete a Lightning payment for testing purposes (testnet only)."""
    if tx_id not in app_state.transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx_data = app_state.transactions[tx_id]
    
    # Update transaction status
    tx_data["status"] = "paid"
    if hasattr(tx_data["escrow"], 'state'):
        from domp.lightning import EscrowState
        tx_data["escrow"].state = EscrowState.ACTIVE
    
    # Broadcast update
    await app_state.broadcast_update({
        "type": "payment_completed",
        "transaction_id": tx_id,
        "status": "paid",
        "message": "Payment completed (test simulation)"
    })
    
    return {
        "success": True,
        "transaction_id": tx_id,
        "status": "paid",
        "message": "Payment completed for testing"
    }


# Marketplace endpoints
@app.get("/api/listings")
async def get_listings():
    """Get all marketplace listings with reputation data from Nostr."""
    listings_with_reputation = []
    
    # Get listings from Nostr instead of memory
    nostr_listings = await app_state.get_listings_from_nostr(limit=100)
    
    for listing_data in nostr_listings:
        event = listing_data["event"]
        content = json.loads(event["content"])
        seller_pubkey = event["pubkey"]
        listing_id = event["id"]
        
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
    """Get detailed information about a specific listing from Nostr."""
    # First check if listing exists in Nostr or local memory
    nostr_listings = await app_state.get_listings_from_nostr(limit=100)
    listing_data = None
    
    for listing in nostr_listings:
        if listing["event"]["id"] == listing_id:
            listing_data = listing
            break
    
    if not listing_data:
        raise HTTPException(status_code=404, detail="Listing not found")
    
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
    """Create a new product listing and publish to Nostr."""
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
    
    # Store listing locally (temporary for demo)
    app_state.listings[listing.id] = {
        "event": listing.to_dict(),
        "seller_keypair": app_state.keypair
    }
    
    # Publish to Nostr for cross-computer visibility
    if app_state.nostr_client:
        try:
            from domp.events import create_event_from_dict
            nostr_event = create_event_from_dict(listing.to_dict())
            published = await app_state.nostr_client.publish_event(nostr_event)
            if published:
                print(f"✅ Published listing {listing.id} to Nostr relays")
            else:
                print(f"⚠️  Failed to publish listing {listing.id} to Nostr")
        except Exception as e:
            print(f"❌ Error publishing listing to Nostr: {e}")
    
    # Broadcast update
    await app_state.broadcast_update({
        "type": "new_listing",
        "listing_id": listing.id,
        "product_name": request.product_name
    })
    
    return {
        "success": True,
        "listing_id": listing.id,
        "message": "Listing created and published to Nostr"
    }


@app.post("/api/bids")
async def place_bid(request: PlaceBidRequest):
    """Place a bid on a listing and publish to Nostr."""
    if not app_state.keypair:
        raise HTTPException(status_code=400, detail="User identity not initialized")
    
    # Check if listing exists in Nostr or local memory
    nostr_listings = await app_state.get_listings_from_nostr(limit=100)
    listing_exists = any(listing["event"]["id"] == request.listing_id for listing in nostr_listings)
    
    if not listing_exists:
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
    
    # Store bid locally (temporary)
    app_state.bids[bid.id] = {
        "event": bid.to_dict(),
        "listing_id": request.listing_id,
        "status": "pending"
    }
    
    # Publish bid to Nostr for cross-computer visibility
    if app_state.nostr_client:
        try:
            from domp.events import create_event_from_dict
            nostr_event = create_event_from_dict(bid.to_dict())
            published = await app_state.nostr_client.publish_event(nostr_event)
            if published:
                print(f"✅ Published bid {bid.id} to Nostr relays")
            else:
                print(f"⚠️  Failed to publish bid {bid.id} to Nostr")
        except Exception as e:
            print(f"❌ Error publishing bid to Nostr: {e}")
    
    # Bid placed successfully - no automatic acceptance
    # Sellers must now manually accept bids via /api/bids/{bid_id}/accept
    
    return {
        "success": True,
        "bid_id": bid.id,
        "message": "Bid placed and published to Nostr! Waiting for seller acceptance.",
        "status": "pending"
    }


@app.get("/api/bids")
async def get_bids(listing_id: str = None):
    """Get bids from Nostr, optionally filtered by listing."""
    if not app_state.keypair:
        raise HTTPException(status_code=400, detail="User identity not initialized")
    
    # Get bids from Nostr
    nostr_bids = await app_state.get_bids_from_nostr(listing_id)
    
    # Format bids for response
    formatted_bids = []
    for bid_data in nostr_bids:
        event = bid_data["event"]
        content = json.loads(event["content"])
        
        formatted_bids.append({
            "id": event["id"],
            "listing_id": content.get("product_ref"),
            "bidder_pubkey": event["pubkey"],
            "bidder_short": event["pubkey"][:16] + "...",
            "bid_amount_sats": content.get("bid_amount_satoshis"),
            "bid_amount_btc": content.get("bid_amount_satoshis", 0) / 100_000_000,
            "message": content.get("message", ""),
            "collateral_sats": content.get("buyer_collateral_satoshis", 0),
            "created_at": event["created_at"],
            "status": bid_data.get("status", "pending")
        })
    
    # Filter for listings owned by current user if no specific listing_id
    if not listing_id:
        user_listings = await app_state.get_listings_from_nostr()
        user_listing_ids = {listing["event"]["id"] for listing in user_listings 
                           if listing["event"]["pubkey"] == app_state.keypair.public_key_hex}
        formatted_bids = [bid for bid in formatted_bids if bid["listing_id"] in user_listing_ids]
    
    return {"bids": formatted_bids}


@app.post("/api/bids/{bid_id}/accept")
async def accept_bid(bid_id: str):
    """Accept a bid and create Lightning escrow."""
    if not app_state.keypair:
        raise HTTPException(status_code=400, detail="User identity not initialized")
    
    # Find the bid in Nostr data
    nostr_bids = await app_state.get_bids_from_nostr()
    bid_data = None
    
    for bid in nostr_bids:
        if bid["event"]["id"] == bid_id:
            bid_data = bid
            break
    
    if not bid_data:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bid_event = bid_data["event"]
    bid_content = json.loads(bid_event["content"])
    listing_id = bid_content.get("product_ref")
    
    if not listing_id:
        raise HTTPException(status_code=400, detail="Invalid bid: missing product reference")
    
    # Find the listing to ensure we own it
    nostr_listings = await app_state.get_listings_from_nostr()
    listing_data = None
    
    for listing in nostr_listings:
        if listing["event"]["id"] == listing_id:
            listing_data = listing
            break
    
    if not listing_data:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing_event = listing_data["event"]
    
    # Verify we own this listing
    if listing_event["pubkey"] != app_state.keypair.public_key_hex:
        raise HTTPException(status_code=403, detail="You can only accept bids on your own listings")
    
    listing_content = json.loads(listing_event["content"])
    
    try:
        # Create Lightning escrow
        escrow = app_state.escrow_manager.create_escrow(
            transaction_id=f"tx_{bid_id[:8]}",
            buyer_pubkey=bid_event["pubkey"],
            seller_pubkey=app_state.keypair.public_key_hex,
            purchase_amount_sats=bid_content["bid_amount_satoshis"],
            buyer_collateral_sats=bid_content.get("buyer_collateral_satoshis", 0),
            seller_collateral_sats=listing_content.get("seller_collateral_satoshis", 0)
        )
        
        # Create Lightning invoices
        lightning_invoices = await create_transaction_invoices(escrow, listing_content)
        
        if "error" in lightning_invoices:
            raise HTTPException(status_code=500, detail=f"Failed to create Lightning invoices: {lightning_invoices['error']}")
        
        # Create bid acceptance event
        purchase_invoice = lightning_invoices.get("purchase", {}).get("payment_request", "")
        collateral_invoice = lightning_invoices.get("buyer_collateral", {}).get("payment_request", "")
        
        from domp.events import BidAcceptance
        acceptance = BidAcceptance(
            bid_ref=bid_id,
            ln_invoice=purchase_invoice,
            collateral_invoice=collateral_invoice,
            estimated_shipping_time="2-3 business days",
            shipping_time_days=3,
            terms="Payment required within 24 hours"
        )
        acceptance.sign(app_state.keypair)
        
        # Store transaction locally
        app_state.transactions[escrow.transaction_id] = {
            "status": "awaiting_payment",
            "escrow": escrow,
            "bid": bid_data,
            "listing": listing_data,
            "lightning_invoices": lightning_invoices,
            "acceptance_event": acceptance.to_dict(),
            "created_at": int(time.time())
        }
        
        app_state.my_transactions.append(escrow.transaction_id)
        
        # Publish acceptance event to Nostr
        if app_state.nostr_client:
            try:
                from domp.events import create_event_from_dict
                nostr_event = create_event_from_dict(acceptance.to_dict())
                published = await app_state.nostr_client.publish_event(nostr_event)
                if published:
                    print(f"✅ Published bid acceptance {acceptance.id} to Nostr relays")
                else:
                    print(f"⚠️  Failed to publish bid acceptance to Nostr")
            except Exception as e:
                print(f"❌ Error publishing bid acceptance to Nostr: {e}")
        
        # Broadcast update
        await app_state.broadcast_update({
            "type": "bid_accepted",
            "transaction_id": escrow.transaction_id,
            "bid_id": bid_id,
            "product_name": listing_content["product_name"],
            "lightning_invoices": lightning_invoices,
            "status": "awaiting_payment"
        })
        
        return {
            "success": True,
            "transaction_id": escrow.transaction_id,
            "lightning_invoices": lightning_invoices,
            "message": "Bid accepted! Lightning invoices created and published to Nostr."
        }
        
    except Exception as e:
        print(f"Error accepting bid: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to accept bid: {str(e)}")


@app.post("/api/bids/{bid_id}/reject")  
async def reject_bid(bid_id: str):
    """Reject a bid."""
    if not app_state.keypair:
        raise HTTPException(status_code=400, detail="User identity not initialized")
    
    # For now, just return success - could implement bid rejection events later
    await app_state.broadcast_update({
        "type": "bid_rejected",
        "bid_id": bid_id,
        "message": "Bid rejected by seller"
    })
    
    return {
        "success": True,
        "message": "Bid rejected"
    }


@app.get("/api/transactions/{tx_id}/status")
async def get_transaction_status(tx_id: str):
    """Get real-time transaction status including Lightning payment and escrow state."""
    if tx_id not in app_state.transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx_data = app_state.transactions[tx_id]
    escrow = tx_data.get("escrow")
    listing_data = tx_data.get("listing", {})
    bid_data = tx_data.get("bid", {})
    
    # Get basic transaction info
    listing_content = json.loads(listing_data.get("event", {}).get("content", "{}"))
    bid_content = json.loads(bid_data.get("event", {}).get("content", "{}"))
    
    status_info = {
        "transaction_id": tx_id,
        "status": tx_data.get("status", "unknown"),
        "product_name": listing_content.get("product_name", "Unknown"),
        "bid_amount_sats": bid_content.get("bid_amount_satoshis", 0),
        "created_at": tx_data.get("created_at", 0)
    }
    
    # Add escrow information
    if escrow:
        status_info["escrow"] = {
            "state": escrow.state.value,
            "purchase_amount_sats": escrow.purchase_amount_sats,
            "buyer_collateral_sats": escrow.buyer_collateral_sats,
            "seller_collateral_sats": escrow.seller_collateral_sats,
            "payment_hash": escrow.payment_hash,
            "created_at": escrow.created_at,
            "expires_at": escrow.expires_at,
            "time_remaining": max(0, escrow.expires_at - int(time.time()))
        }
    
    # Add Lightning invoice information
    lightning_invoices = tx_data.get("lightning_invoices", {})
    if lightning_invoices:
        status_info["lightning_invoices"] = lightning_invoices
    
    # Add cross-computer sync status
    status_info["sync_status"] = {
        "local_state": tx_data.get("status", "unknown"),
        "last_updated": int(time.time()),
        "source": "local" if tx_id in app_state.my_transactions else "remote"
    }
    
    return status_info


async def create_transaction_invoices(escrow, listing_content):
    """Create Lightning invoices for a DOMP transaction."""
    invoices = {}
    
    try:
        if not app_state.lightning_client:
            return {"error": "Lightning client not available"}
        
        # Create invoice for purchase amount (main payment)
        purchase_description = f"DOMP: {listing_content['product_name']} - Purchase"
        
        if hasattr(app_state.lightning_client, 'node_id'):
            # Mock client
            invoice_id = app_state.lightning_client.create_invoice(
                amount_sats=escrow.purchase_amount_sats,
                description=purchase_description
            )
            invoices["purchase"] = {
                "payment_request": invoice_id,
                "amount_sats": escrow.purchase_amount_sats,
                "description": purchase_description,
                "client_type": "mock"
            }
        else:
            # Real Lightning client
            if not hasattr(app_state.lightning_client, '_channel') or not app_state.lightning_client._channel:
                await asyncio.wait_for(app_state.lightning_client.connect(), timeout=5.0)
            
            invoice_data = await asyncio.wait_for(
                app_state.lightning_client.create_invoice(
                    amount_sats=escrow.purchase_amount_sats,
                    description=purchase_description,
                    expiry_seconds=3600  # 1 hour to pay
                ), timeout=5.0
            )
            invoices["purchase"] = {
                "payment_request": invoice_data["payment_request"],
                "payment_hash": invoice_data["payment_hash"],
                "amount_sats": invoice_data["amount_sats"],
                "description": invoice_data["description"],
                "client_type": "real_lnd"
            }
        
        # Create collateral invoices if needed
        if escrow.buyer_collateral_sats > 0:
            collateral_description = f"DOMP: {listing_content['product_name']} - Buyer Collateral"
            
            if hasattr(app_state.lightning_client, 'node_id'):
                # Mock client
                collateral_invoice = app_state.lightning_client.create_invoice(
                    amount_sats=escrow.buyer_collateral_sats,
                    description=collateral_description
                )
                invoices["buyer_collateral"] = {
                    "payment_request": collateral_invoice,
                    "amount_sats": escrow.buyer_collateral_sats,
                    "description": collateral_description,
                    "client_type": "mock"
                }
            else:
                # Real Lightning client  
                collateral_data = await asyncio.wait_for(
                    app_state.lightning_client.create_invoice(
                        amount_sats=escrow.buyer_collateral_sats,
                        description=collateral_description,
                        expiry_seconds=3600
                    ), timeout=5.0
                )
                invoices["buyer_collateral"] = {
                    "payment_request": collateral_data["payment_request"],
                    "payment_hash": collateral_data["payment_hash"],
                    "amount_sats": collateral_data["amount_sats"],
                    "description": collateral_data["description"],
                    "client_type": "real_lnd"
                }
        
        return invoices
        
    except Exception as e:
        print(f"Failed to create transaction invoices: {e}")
        return {"error": str(e)}


# simulate_bid_acceptance function removed - replaced with real cross-computer bid acceptance flow
# Sellers now manually accept bids via POST /api/bids/{bid_id}/accept


@app.get("/api/transactions")
async def get_transactions():
    """Get user's transactions from both local memory and Nostr."""
    transactions = []
    
    # Get transactions from local memory (for current demo functionality)
    for tx_id in app_state.my_transactions:
        if tx_id in app_state.transactions:
            tx_data = app_state.transactions[tx_id]
            listing_content = json.loads(tx_data["listing"]["event"]["content"])
            
            transaction_info = {
                "id": tx_id,
                "status": tx_data["status"],
                "product_name": listing_content["product_name"],
                "amount_sats": tx_data["escrow"].purchase_amount_sats,
                "amount_btc": tx_data["escrow"].purchase_amount_sats / 100_000_000,
                "created_at": tx_data["created_at"],
                "escrow_state": tx_data["escrow"].state.value
            }
            
            # Add Lightning invoice information if available
            if "lightning_invoices" in tx_data:
                transaction_info["lightning_invoices"] = tx_data["lightning_invoices"]
                
                # Add payment instructions for easier frontend consumption
                if "purchase" in tx_data["lightning_invoices"]:
                    purchase_invoice = tx_data["lightning_invoices"]["purchase"]
                    transaction_info["payment_required"] = {
                        "amount_sats": purchase_invoice["amount_sats"],
                        "payment_request": purchase_invoice["payment_request"],
                        "description": purchase_invoice["description"],
                        "client_type": purchase_invoice.get("client_type", "unknown")
                    }
            
            transactions.append(transaction_info)
    
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