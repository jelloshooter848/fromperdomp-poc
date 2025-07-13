#!/usr/bin/env python3
"""
DOMP Marketplace CLI
Complete command-line interface for the Decentralized Online Marketplace Protocol.
Integrates Lightning escrow, reputation system, and Nostr connectivity.
"""

import json
import time
import sys
import os
from typing import Dict, List, Optional, Any
from dataclasses import asdict

sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import KeyPair, generate_pow_nonce
from domp.events import ProductListing, BidSubmission, BidAcceptance, PaymentConfirmation, ReceiptConfirmation
from domp.lightning import LightningEscrowManager, MockLightningNode, EscrowState
from domp.reputation import ReputationSystem, create_reputation_from_receipt_confirmation
from domp.validation import validate_event


class DOOMPMarketplaceCLI:
    """Complete DOMP marketplace command-line interface."""
    
    def __init__(self):
        # Core components
        self.keypair: Optional[KeyPair] = None
        self.lightning_node: Optional[MockLightningNode] = None
        self.escrow_manager = LightningEscrowManager()
        self.reputation_system = ReputationSystem()
        
        # Data storage (in production, this would be a database)
        self.listings: Dict[str, Dict] = {}
        self.bids: Dict[str, Dict] = {}
        self.transactions: Dict[str, Dict] = {}
        self.my_transactions: List[str] = []
        
        # CLI state
        self.running = True
        self.current_menu = "main"
        
    def start(self):
        """Start the CLI interface."""
        self.print_header()
        
        # Load or create identity
        if not self.load_identity():
            self.create_identity()
        
        # Initialize Lightning node
        self.lightning_node = MockLightningNode(f"user_{self.keypair.public_key_hex[:8]}")
        
        # Load sample data for demo
        self.load_sample_data()
        
        # Main CLI loop
        while self.running:
            try:
                self.show_menu()
                choice = input("\n👉 Choose an option: ").strip()
                self.handle_choice(choice)
            except KeyboardInterrupt:
                print("\n\n👋 Thanks for using DOMP Marketplace!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")
    
    def print_header(self):
        """Print the CLI header."""
        print("=" * 70)
        print("🛒 DOMP MARKETPLACE CLI")
        print("Decentralized Online Marketplace Protocol")
        print("Lightning Escrow • Nostr Integration • Reputation System")
        print("=" * 70)
    
    def load_identity(self) -> bool:
        """Load existing identity or return False to create new one."""
        if os.path.exists("domp_identity.json"):
            try:
                with open("domp_identity.json", "r") as f:
                    data = json.load(f)
                    self.keypair = KeyPair(private_key=bytes.fromhex(data["private_key"]))
                    print(f"🔑 Loaded identity: {self.keypair.public_key_hex[:16]}...")
                    return True
            except Exception as e:
                print(f"❌ Error loading identity: {e}")
        return False
    
    def create_identity(self):
        """Create a new DOMP identity."""
        print("\n🔑 Creating new DOMP identity...")
        self.keypair = KeyPair()
        
        # Save identity
        try:
            with open("domp_identity.json", "w") as f:
                json.dump({
                    "private_key": self.keypair.private_key_hex,
                    "public_key": self.keypair.public_key_hex
                }, f)
            print(f"✅ Identity created: {self.keypair.public_key_hex[:16]}...")
        except Exception as e:
            print(f"❌ Error saving identity: {e}")
    
    def load_sample_data(self):
        """Load sample marketplace data for demonstration."""
        print("📦 Loading sample marketplace data...")
        
        # Create sample sellers
        alice = KeyPair()
        bob = KeyPair()
        charlie = KeyPair()
        
        # Sample listings
        sample_listings = [
            {
                "seller": alice,
                "product_name": "Digital Camera DSLR",
                "description": "Professional 24MP camera with 50mm lens, excellent condition",
                "price_sats": 75_000_000,  # 0.75 BTC
                "category": "electronics"
            },
            {
                "seller": alice,
                "product_name": "Gaming Laptop",
                "description": "High-performance gaming laptop, RTX 4070, 32GB RAM",
                "price_sats": 120_000_000,  # 1.2 BTC
                "category": "computers"
            },
            {
                "seller": bob,
                "product_name": "Smartphone iPhone",
                "description": "Latest iPhone, unlocked, 256GB storage",
                "price_sats": 50_000_000,  # 0.5 BTC
                "category": "electronics"
            },
            {
                "seller": charlie,
                "product_name": "Bitcoin Hardware Wallet",
                "description": "Secure Bitcoin storage device, brand new",
                "price_sats": 8_000_000,  # 0.08 BTC
                "category": "crypto"
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
        
        print(f"✅ Loaded {len(self.listings)} sample listings")
    
    def add_sample_reputation(self):
        """Add sample reputation data for demo sellers."""
        # This would normally come from processing historical receipt confirmations
        sample_scores = [
            {
                "seller_pubkey": list(self.listings.values())[0]["seller_keypair"].public_key_hex,
                "scores": [(5, 80_000_000), (4, 50_000_000), (5, 120_000_000), (5, 30_000_000)]
            },
            {
                "seller_pubkey": list(self.listings.values())[2]["seller_keypair"].public_key_hex,
                "scores": [(4, 40_000_000), (3, 25_000_000)]
            }
        ]
        
        for seller_data in sample_scores:
            for rating, amount in seller_data["scores"]:
                # Create a mock reputation score
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
    
    def show_menu(self):
        """Display the current menu."""
        print("\n" + "=" * 50)
        
        if self.current_menu == "main":
            self.show_main_menu()
        elif self.current_menu == "browse":
            self.show_browse_menu()
        elif self.current_menu == "sell":
            self.show_sell_menu()
        elif self.current_menu == "transactions":
            self.show_transactions_menu()
        elif self.current_menu == "reputation":
            self.show_reputation_menu()
        elif self.current_menu == "lightning":
            self.show_lightning_menu()
    
    def show_main_menu(self):
        """Show the main menu."""
        print("🏠 MAIN MENU")
        print("=" * 50)
        print("1. 🛒 Browse Marketplace")
        print("2. 💰 Sell Item")
        print("3. 📋 My Transactions")
        print("4. 🏆 Reputation System")
        print("5. ⚡ Lightning Wallet")
        print("6. ℹ️  System Info")
        print("7. 🚪 Exit")
    
    def show_browse_menu(self):
        """Show marketplace browsing interface."""
        print("🛒 MARKETPLACE BROWSER")
        print("=" * 50)
        
        if not self.listings:
            print("📭 No listings available")
            print("b. ⬅️  Back to main menu")
            return
        
        # Display listings with reputation
        for i, (listing_id, listing_data) in enumerate(self.listings.items(), 1):
            event = listing_data["event"]
            content = json.loads(event["content"])
            seller_pubkey = event["pubkey"]
            
            # Get seller reputation
            rep_summary = self.reputation_system.get_reputation_summary(seller_pubkey)
            trust_score = self.reputation_system.get_trust_score(seller_pubkey)
            
            print(f"\n{i}. 📦 {content['product_name']}")
            print(f"   💰 Price: {content['price_satoshis']:,} sats ({content['price_satoshis']/100_000_000:.3f} BTC)")
            print(f"   📝 {content['description'][:60]}...")
            print(f"   👤 Seller: {seller_pubkey[:16]}... ({rep_summary.get('reliability', 'No Data')})")
            print(f"   ⭐ Rating: {rep_summary.get('overall_score', 0.0):.1f}/5.0 ({rep_summary.get('total_transactions', 0)} transactions)")
            print(f"   🎯 Trust: {trust_score:.3f}")
        
        print(f"\n📋 Actions:")
        print("• Enter number to view/buy item")
        print("b. ⬅️  Back to main menu")
    
    def show_sell_menu(self):
        """Show selling interface."""
        print("💰 SELL ITEM")
        print("=" * 50)
        print("1. ➕ Create New Listing")
        print("2. 📋 My Active Listings")
        print("3. 📊 Selling Analytics")
        print("b. ⬅️  Back to main menu")
    
    def show_transactions_menu(self):
        """Show transactions interface."""
        print("📋 MY TRANSACTIONS")
        print("=" * 50)
        
        if not self.my_transactions:
            print("📭 No transactions yet")
        else:
            for i, tx_id in enumerate(self.my_transactions, 1):
                tx = self.transactions.get(tx_id, {})
                print(f"{i}. Transaction {tx_id[:16]}... - Status: {tx.get('status', 'Unknown')}")
        
        print("\n📋 Actions:")
        print("1. 🔍 View Transaction Details")
        print("2. ⚡ Check Lightning Escrows")
        print("b. ⬅️  Back to main menu")
    
    def show_reputation_menu(self):
        """Show reputation system interface."""
        print("🏆 REPUTATION SYSTEM")
        print("=" * 50)
        
        # Show my reputation
        my_rep = self.reputation_system.get_reputation_summary(self.keypair.public_key_hex)
        print(f"📊 Your Reputation:")
        print(f"   Overall Score: {my_rep.get('overall_score', 0.0):.1f}/5.0")
        print(f"   Reliability: {my_rep.get('reliability', 'No Data')}")
        print(f"   Transactions: {my_rep.get('total_transactions', 0)}")
        print(f"   Trust Score: {self.reputation_system.get_trust_score(self.keypair.public_key_hex):.3f}")
        
        print(f"\n📋 Actions:")
        print("1. 🔍 View Seller Reputation")
        print("2. 📊 Reputation Analytics")
        print("3. 🏆 Top Sellers")
        print("b. ⬅️  Back to main menu")
    
    def show_lightning_menu(self):
        """Show Lightning wallet interface."""
        print("⚡ LIGHTNING WALLET")
        print("=" * 50)
        
        if self.lightning_node:
            balance = self.lightning_node.get_balance()
            print(f"💰 Balance: {balance:,} sats ({balance/100_000_000:.6f} BTC)")
            
            print(f"\n📋 Actions:")
            print("1. 📄 Create Invoice")
            print("2. ⚡ Pay Invoice")
            print("3. 📋 Payment History")
            print("4. 🔒 View Active Escrows")
        else:
            print("❌ Lightning node not initialized")
        
        print("b. ⬅️  Back to main menu")
    
    def handle_choice(self, choice: str):
        """Handle user menu choice."""
        if self.current_menu == "main":
            self.handle_main_choice(choice)
        elif self.current_menu == "browse":
            self.handle_browse_choice(choice)
        elif self.current_menu == "sell":
            self.handle_sell_choice(choice)
        elif self.current_menu == "transactions":
            self.handle_transactions_choice(choice)
        elif self.current_menu == "reputation":
            self.handle_reputation_choice(choice)
        elif self.current_menu == "lightning":
            self.handle_lightning_choice(choice)
    
    def handle_main_choice(self, choice: str):
        """Handle main menu choices."""
        if choice == "1":
            self.current_menu = "browse"
        elif choice == "2":
            self.current_menu = "sell"
        elif choice == "3":
            self.current_menu = "transactions"
        elif choice == "4":
            self.current_menu = "reputation"
        elif choice == "5":
            self.current_menu = "lightning"
        elif choice == "6":
            self.show_system_info()
        elif choice == "7":
            self.running = False
        else:
            print("❌ Invalid choice")
    
    def handle_browse_choice(self, choice: str):
        """Handle browse menu choices."""
        if choice.lower() == "b":
            self.current_menu = "main"
        elif choice.isdigit():
            item_num = int(choice)
            if 1 <= item_num <= len(self.listings):
                self.view_item(item_num - 1)
        else:
            print("❌ Invalid choice")
    
    def handle_sell_choice(self, choice: str):
        """Handle sell menu choices."""
        if choice.lower() == "b":
            self.current_menu = "main"
        elif choice == "1":
            self.create_listing()
        elif choice == "2":
            self.show_my_listings()
        elif choice == "3":
            self.show_selling_analytics()
        else:
            print("❌ Invalid choice")
    
    def handle_transactions_choice(self, choice: str):
        """Handle transactions menu choices."""
        if choice.lower() == "b":
            self.current_menu = "main"
        elif choice == "1":
            self.view_transaction_details()
        elif choice == "2":
            self.check_lightning_escrows()
        else:
            print("❌ Invalid choice")
    
    def handle_reputation_choice(self, choice: str):
        """Handle reputation menu choices."""
        if choice.lower() == "b":
            self.current_menu = "main"
        elif choice == "1":
            self.view_seller_reputation()
        elif choice == "2":
            self.show_reputation_analytics()
        elif choice == "3":
            self.show_top_sellers()
        else:
            print("❌ Invalid choice")
    
    def handle_lightning_choice(self, choice: str):
        """Handle Lightning menu choices."""
        if choice.lower() == "b":
            self.current_menu = "main"
        elif choice == "1":
            self.create_invoice()
        elif choice == "2":
            self.pay_invoice()
        elif choice == "3":
            self.show_payment_history()
        elif choice == "4":
            self.view_active_escrows()
        else:
            print("❌ Invalid choice")
    
    def view_item(self, item_index: int):
        """View detailed item information and purchase options."""
        listing_items = list(self.listings.items())
        if 0 <= item_index < len(listing_items):
            listing_id, listing_data = listing_items[item_index]
            event = listing_data["event"]
            content = json.loads(event["content"])
            seller_pubkey = event["pubkey"]
            
            print("\n" + "=" * 60)
            print("📦 ITEM DETAILS")
            print("=" * 60)
            print(f"🏷️  Name: {content['product_name']}")
            print(f"📝 Description: {content['description']}")
            print(f"💰 Price: {content['price_satoshis']:,} sats ({content['price_satoshis']/100_000_000:.3f} BTC)")
            print(f"🏷️  Category: {content.get('category', 'Unknown')}")
            print(f"🛡️  Seller Collateral: {content.get('seller_collateral_satoshis', 0):,} sats")
            
            # Seller reputation
            rep_summary = self.reputation_system.get_reputation_summary(seller_pubkey)
            trust_score = self.reputation_system.get_trust_score(seller_pubkey)
            print(f"\n👤 Seller Information:")
            print(f"   Pubkey: {seller_pubkey[:16]}...")
            print(f"   Reputation: {rep_summary.get('reliability', 'No Data')}")
            print(f"   Rating: {rep_summary.get('overall_score', 0.0):.1f}/5.0")
            print(f"   Transactions: {rep_summary.get('total_transactions', 0)}")
            print(f"   Trust Score: {trust_score:.3f}")
            
            print(f"\n📋 Actions:")
            print("1. 💸 Place Bid")
            print("2. 👤 View Seller Profile")
            print("3. ⬅️  Back to browse")
            
            choice = input("\n👉 Choose action: ").strip()
            
            if choice == "1":
                self.place_bid(listing_id, listing_data)
            elif choice == "2":
                self.view_seller_profile(seller_pubkey)
            elif choice == "3":
                return
    
    def place_bid(self, listing_id: str, listing_data: dict):
        """Place a bid on an item."""
        event = listing_data["event"]
        content = json.loads(event["content"])
        
        print(f"\n💸 PLACE BID ON: {content['product_name']}")
        print(f"💰 Listed Price: {content['price_satoshis']:,} sats")
        
        try:
            bid_amount = input("💰 Enter bid amount (sats): ").strip()
            if not bid_amount.isdigit():
                print("❌ Invalid amount")
                return
            
            bid_amount = int(bid_amount)
            
            # Create bid submission
            bid = BidSubmission(
                product_ref=listing_id,
                bid_amount_satoshis=bid_amount,
                buyer_collateral_satoshis=bid_amount,  # 100% collateral
                message="Interested in purchasing this item",
                payment_timeout_hours=24
            )
            bid.sign(self.keypair)
            
            print(f"\n✅ Bid placed successfully!")
            print(f"   Bid ID: {bid.id[:16]}...")
            print(f"   Amount: {bid_amount:,} sats")
            print(f"   Collateral: {bid_amount:,} sats")
            print(f"\n⏳ Waiting for seller acceptance...")
            
            # Store bid
            self.bids[bid.id] = {
                "event": bid.to_dict(),
                "listing_id": listing_id,
                "status": "pending"
            }
            
            # Simulate seller acceptance for demo
            self.simulate_bid_acceptance(bid.id, listing_data)
            
        except Exception as e:
            print(f"❌ Error placing bid: {e}")
    
    def simulate_bid_acceptance(self, bid_id: str, listing_data: dict):
        """Simulate seller accepting the bid for demo purposes."""
        print(f"\n🎉 Seller accepted your bid!")
        
        # Create escrow and invoices
        bid_data = self.bids[bid_id]
        bid_event = bid_data["event"]
        listing_event = listing_data["event"]
        
        bid_content = json.loads(bid_event["content"])
        listing_content = json.loads(listing_event["content"])
        
        # Create Lightning escrow
        escrow = self.escrow_manager.create_escrow(
            transaction_id=f"tx_{bid_id[:8]}",
            buyer_pubkey=self.keypair.public_key_hex,
            seller_pubkey=listing_event["pubkey"],
            purchase_amount_sats=bid_content["bid_amount_satoshis"],
            buyer_collateral_sats=bid_content["buyer_collateral_satoshis"],
            seller_collateral_sats=listing_content.get("seller_collateral_satoshis", 0)
        )
        
        # Create seller Lightning node
        seller_node = MockLightningNode("seller_node")
        
        # Generate invoices
        purchase_invoice = seller_node.create_invoice(
            amount_sats=bid_content["bid_amount_satoshis"],
            description=f"Purchase: {listing_content['product_name']}",
            payment_hash=escrow.payment_hash
        )
        
        collateral_invoice = seller_node.create_invoice(
            amount_sats=bid_content["buyer_collateral_satoshis"],
            description=f"Buyer collateral: {listing_content['product_name']}"
        )
        
        print(f"⚡ Lightning invoices generated:")
        print(f"   Purchase: {purchase_invoice}")
        print(f"   Collateral: {collateral_invoice}")
        print(f"\n💸 Ready to pay? Your balance: {self.lightning_node.get_balance():,} sats")
        
        choice = input("Pay now? (y/n): ").strip().lower()
        if choice == "y":
            self.process_lightning_payment(escrow, seller_node, purchase_invoice, collateral_invoice, listing_data)
    
    def process_lightning_payment(self, escrow, seller_node, purchase_invoice, collateral_invoice, listing_data):
        """Process Lightning payment for the purchase."""
        try:
            print(f"\n💸 Processing Lightning payments...")
            
            # Pay purchase amount
            purchase_hash = self.lightning_node.pay_invoice(
                purchase_invoice,
                recipient_node=seller_node,
                preimage=escrow.payment_preimage
            )
            
            # Pay collateral
            collateral_hash = self.lightning_node.pay_invoice(
                collateral_invoice,
                recipient_node=seller_node
            )
            
            # Simulate seller paying their collateral
            listing_content = json.loads(listing_data["event"]["content"])
            seller_collateral_sats = listing_content.get("seller_collateral_satoshis", 0)
            seller_collateral_hash = None
            
            if seller_collateral_sats > 0:
                seller_collateral_invoice = seller_node.create_invoice(
                    amount_sats=seller_collateral_sats,
                    description=f"Seller collateral: {listing_content['product_name']}"
                )
                seller_collateral_hash = seller_node.pay_invoice(
                    seller_collateral_invoice,
                    recipient_node=seller_node  # Pays to themselves
                )
                print(f"   Seller collateral: {seller_collateral_hash[:16]}...")
            
            print(f"✅ Payments completed!")
            print(f"   Purchase payment: {purchase_hash[:16]}...")
            print(f"   Collateral payment: {collateral_hash[:16]}...")
            
            # Fund escrow with all required payments
            escrow_funded = self.escrow_manager.fund_escrow(
                escrow.transaction_id,
                purchase_hash,
                collateral_hash,
                seller_collateral_hash
            )
            
            if escrow_funded:
                print(f"🔒 Escrow activated! Your purchase is secured.")
                print(f"📦 Seller will now ship the item.")
                print(f"⏰ You have {escrow.timeout_blocks} blocks to confirm receipt.")
                
                # Simulate shipping and receipt
                self.simulate_shipping_and_receipt(escrow, listing_data)
            else:
                print(f"❌ Escrow funding failed")
                
        except Exception as e:
            print(f"❌ Payment failed: {e}")
    
    def simulate_shipping_and_receipt(self, escrow, listing_data):
        """Simulate item shipping and receipt confirmation."""
        print(f"\n📦 Simulating shipping process...")
        time.sleep(1)
        
        listing_event = listing_data["event"]
        listing_content = json.loads(listing_event["content"])
        
        print(f"🚚 Item shipped: {listing_content['product_name']}")
        print(f"📧 Tracking: TRK{escrow.transaction_id[:8].upper()}")
        
        choice = input("\nItem received? Confirm receipt (y/n): ").strip().lower()
        if choice == "y":
            # Create receipt confirmation
            receipt = ReceiptConfirmation(
                payment_ref=escrow.transaction_id,
                status="received",
                rating=5,
                feedback=f"Excellent transaction! {listing_content['product_name']} received as described.",
                item_condition="as_described",
                shipping_rating=5,
                communication_rating=5,
                would_buy_again=True
            )
            receipt.sign(self.keypair)
            
            # Release payment
            revealed_preimage = self.escrow_manager.release_payment(escrow.transaction_id)
            
            if revealed_preimage:
                print(f"\n🎉 TRANSACTION COMPLETED!")
                print(f"💰 Payment released to seller")
                print(f"🔑 Preimage: {revealed_preimage[:16]}...")
                print(f"💸 Your collateral will be refunded")
                
                # Add to reputation system
                rep_score = create_reputation_from_receipt_confirmation(
                    receipt.to_dict(),
                    {
                        "seller_pubkey": listing_event["pubkey"],
                        "amount_sats": json.loads(listing_event["content"])["price_satoshis"]
                    }
                )
                self.reputation_system.add_reputation_score(rep_score)
                
                print(f"🏆 Reputation updated for seller")
                
                # Store transaction
                self.transactions[escrow.transaction_id] = {
                    "status": "completed",
                    "escrow": escrow,
                    "receipt": receipt.to_dict(),
                    "listing": listing_data
                }
                self.my_transactions.append(escrow.transaction_id)
                
            else:
                print(f"❌ Failed to release payment")
    
    def create_listing(self):
        """Create a new product listing."""
        print(f"\n📦 CREATE NEW LISTING")
        print("=" * 40)
        
        try:
            name = input("🏷️  Product name: ").strip()
            if not name:
                print("❌ Product name required")
                return
            
            description = input("📝 Description: ").strip()
            if not description:
                print("❌ Description required")
                return
            
            price_input = input("💰 Price (sats): ").strip()
            if not price_input.isdigit():
                print("❌ Invalid price")
                return
            price_sats = int(price_input)
            
            category = input("🏷️  Category (optional): ").strip() or "general"
            
            # Create listing
            listing = ProductListing(
                product_name=name,
                description=description,
                price_satoshis=price_sats,
                category=category,
                seller_collateral_satoshis=price_sats // 10,  # 10% collateral
                listing_id=f"my_item_{int(time.time())}"
            )
            listing.sign(self.keypair)
            
            # Store listing
            self.listings[listing.id] = {
                "event": listing.to_dict(),
                "seller_keypair": self.keypair
            }
            
            print(f"\n✅ Listing created successfully!")
            print(f"   Listing ID: {listing.id[:16]}...")
            print(f"   Price: {price_sats:,} sats ({price_sats/100_000_000:.6f} BTC)")
            print(f"   Seller collateral: {price_sats//10:,} sats")
            
        except Exception as e:
            print(f"❌ Error creating listing: {e}")
        
        input("\nPress Enter to continue...")
    
    def show_system_info(self):
        """Show system information."""
        print(f"\n📊 DOMP SYSTEM INFORMATION")
        print("=" * 50)
        print(f"🔑 Your Identity: {self.keypair.public_key_hex[:16]}...")
        print(f"⚡ Lightning Balance: {self.lightning_node.get_balance():,} sats")
        print(f"📦 Total Listings: {len(self.listings)}")
        print(f"💸 Your Transactions: {len(self.my_transactions)}")
        print(f"🏆 Active Escrows: {len([e for e in self.escrow_manager.escrows.values() if e.state == EscrowState.ACTIVE])}")
        
        # Your reputation
        my_rep = self.reputation_system.get_reputation_summary(self.keypair.public_key_hex)
        print(f"⭐ Your Reputation: {my_rep['overall_score']:.1f}/5.0 ({my_rep['total_transactions']} transactions)")
        
        print(f"\n🔧 Protocol Features:")
        print("  ✅ Lightning HTLC Escrow")
        print("  ✅ Decentralized Reputation System")
        print("  ✅ Nostr Protocol Integration")
        print("  ✅ Proof-of-Work Anti-Spam")
        print("  ✅ Multi-signature Security")
        
        input("\nPress Enter to continue...")
    
    def show_top_sellers(self):
        """Show top sellers by reputation."""
        print(f"\n🏆 TOP SELLERS")
        print("=" * 40)
        
        # Get all seller pubkeys
        seller_pubkeys = set()
        for listing_data in self.listings.values():
            seller_pubkeys.add(listing_data["event"]["pubkey"])
        
        if not seller_pubkeys:
            print("📭 No sellers found")
            input("\nPress Enter to continue...")
            return
        
        # Compare sellers
        comparison = self.reputation_system.compare_sellers(list(seller_pubkeys))
        
        for i, seller in enumerate(comparison, 1):
            if seller["total_transactions"] > 0:
                trust_score = self.reputation_system.get_trust_score(
                    next(pubkey for pubkey in seller_pubkeys if pubkey.startswith(seller["pubkey"][:16]))
                )
                print(f"{i}. {seller['reliability']} - {seller['overall_score']:.1f}⭐")
                print(f"   Pubkey: {seller['pubkey']}")
                print(f"   Trust: {trust_score:.3f} | Transactions: {seller['total_transactions']}")
                print(f"   Volume: {seller['total_volume_btc']:.3f} BTC")
                print()
        
        input("Press Enter to continue...")
    
    def view_active_escrows(self):
        """View active Lightning escrows."""
        print(f"\n🔒 ACTIVE ESCROWS")
        print("=" * 40)
        
        active_escrows = [e for e in self.escrow_manager.escrows.values() 
                         if e.state == EscrowState.ACTIVE]
        
        if not active_escrows:
            print("📭 No active escrows")
        else:
            for escrow in active_escrows:
                print(f"🔒 Escrow: {escrow.transaction_id}")
                print(f"   Amount: {escrow.purchase_amount_sats:,} sats")
                print(f"   State: {escrow.state.value}")
                print(f"   Expires: {time.ctime(escrow.expires_at)}")
                print()
        
        input("Press Enter to continue...")
    
    def view_seller_profile(self, seller_pubkey: str):
        """View detailed seller profile and reputation."""
        print(f"\n👤 SELLER PROFILE")
        print("=" * 40)
        
        rep_summary = self.reputation_system.get_reputation_summary(seller_pubkey)
        trust_score = self.reputation_system.get_trust_score(seller_pubkey)
        
        print(f"🔑 Pubkey: {seller_pubkey}")
        print(f"⭐ Overall Rating: {rep_summary.get('overall_score', 0.0):.1f}/5.0")
        print(f"🏷️  Reliability: {rep_summary.get('reliability', 'No Data')}")
        print(f"📊 Total Transactions: {rep_summary.get('total_transactions', 0)}")
        print(f"💰 Total Volume: {rep_summary.get('total_volume_btc', 0.0):.3f} BTC")
        print(f"🎯 Trust Score: {trust_score:.3f}")
        
        if rep_summary.get('item_quality'):
            print(f"\n📊 Detailed Metrics:")
            print(f"   📦 Item Quality: {rep_summary.get('item_quality', 0.0):.1f}/5.0")
            print(f"   🚚 Shipping Speed: {rep_summary.get('shipping_speed', 0.0):.1f}/5.0")
            print(f"   💬 Communication: {rep_summary.get('communication', 0.0):.1f}/5.0")
            print(f"   💳 Payment Reliability: {rep_summary.get('payment_reliability', 0.0):.1f}/5.0")
        
        print(f"\n🔍 Trust Indicators:")
        print(f"   ✅ Verified Purchases: {rep_summary.get('verified_purchases', 0)}")
        print(f"   🔒 Completed Escrows: {rep_summary.get('completed_escrows', 0)}")
        print(f"   👥 Unique Reviewers: {rep_summary.get('unique_reviewers', 0)}")
        print(f"   📈 Recent Activity: {rep_summary.get('recent_activity', 0)} (last 30 days)")
        
        # Show their listings
        seller_listings = [(id, data) for id, data in self.listings.items() 
                          if data["event"]["pubkey"] == seller_pubkey]
        
        if seller_listings:
            print(f"\n📦 Current Listings ({len(seller_listings)}):")
            for i, (listing_id, listing_data) in enumerate(seller_listings[:3], 1):
                content = json.loads(listing_data["event"]["content"])
                print(f"   {i}. {content['product_name']} - {content['price_satoshis']:,} sats")
        
        input("\nPress Enter to continue...")
    
    def show_my_listings(self):
        """Show user's active listings."""
        print(f"\n📦 MY ACTIVE LISTINGS")
        print("=" * 40)
        
        my_listings = [(id, data) for id, data in self.listings.items() 
                      if data["event"]["pubkey"] == self.keypair.public_key_hex]
        
        if not my_listings:
            print("📭 No active listings")
        else:
            for i, (listing_id, listing_data) in enumerate(my_listings, 1):
                content = json.loads(listing_data["event"]["content"])
                print(f"{i}. 📦 {content['product_name']}")
                print(f"   💰 Price: {content['price_satoshis']:,} sats")
                print(f"   📝 {content['description'][:50]}...")
                print(f"   🆔 ID: {listing_id[:16]}...")
                print()
        
        input("Press Enter to continue...")
    
    def show_selling_analytics(self):
        """Show selling performance analytics."""
        print(f"\n📊 SELLING ANALYTICS")
        print("=" * 40)
        
        my_listings = [(id, data) for id, data in self.listings.items() 
                      if data["event"]["pubkey"] == self.keypair.public_key_hex]
        
        my_rep = self.reputation_system.get_reputation_summary(self.keypair.public_key_hex)
        
        print(f"📈 Performance Summary:")
        print(f"   📦 Active Listings: {len(my_listings)}")
        print(f"   ⭐ Seller Rating: {my_rep.get('overall_score', 0.0):.1f}/5.0")
        print(f"   💰 Total Sales Volume: {my_rep.get('total_volume_btc', 0.0):.3f} BTC")
        print(f"   📊 Total Transactions: {my_rep.get('total_transactions', 0)}")
        print(f"   🎯 Trust Score: {self.reputation_system.get_trust_score(self.keypair.public_key_hex):.3f}")
        
        if my_listings:
            total_value = sum(json.loads(data["event"]["content"])["price_satoshis"] 
                            for _, data in my_listings)
            print(f"   💵 Inventory Value: {total_value:,} sats ({total_value/100_000_000:.3f} BTC)")
        
        print(f"\n💡 Recommendations:")
        if len(my_listings) == 0:
            print("   • Create your first listing to start selling")
        elif my_rep.get('total_transactions', 0) == 0:
            print("   • Complete your first sale to build reputation")
        else:
            print("   • Keep providing excellent service to maintain high ratings")
            print("   • Consider adding more listings to increase sales volume")
        
        input("Press Enter to continue...")
    
    def view_transaction_details(self):
        """View detailed transaction information."""
        print(f"\n🔍 TRANSACTION DETAILS")
        print("=" * 40)
        
        if not self.my_transactions:
            print("📭 No transactions to display")
            input("Press Enter to continue...")
            return
        
        print(f"📊 Your Transactions:")
        for i, tx_id in enumerate(self.my_transactions, 1):
            tx_data = self.transactions.get(tx_id, {})
            print(f"{i}. Transaction: {tx_id[:16]}...")
            print(f"   Status: {tx_data.get('status', 'Unknown')}")
            
            if 'escrow' in tx_data:
                escrow = tx_data['escrow']
                print(f"   Amount: {escrow.purchase_amount_sats:,} sats")
                print(f"   Escrow State: {escrow.state.value}")
            
            if 'listing' in tx_data:
                listing_content = json.loads(tx_data['listing']['event']['content'])
                print(f"   Item: {listing_content['product_name']}")
            print()
        
        input("Press Enter to continue...")
    
    def view_seller_reputation(self):
        """View reputation for a specific seller."""
        print(f"\n🔍 VIEW SELLER REPUTATION")
        print("=" * 40)
        
        seller_pubkey = input("Enter seller pubkey (or partial): ").strip()
        if not seller_pubkey:
            print("❌ No pubkey entered")
            input("Press Enter to continue...")
            return
        
        # Find matching sellers
        matches = []
        for listing_data in self.listings.values():
            pubkey = listing_data["event"]["pubkey"]
            if seller_pubkey.lower() in pubkey.lower():
                matches.append(pubkey)
        
        matches = list(set(matches))  # Remove duplicates
        
        if not matches:
            print(f"❌ No sellers found matching '{seller_pubkey}'")
        elif len(matches) == 1:
            self.view_seller_profile(matches[0])
            return
        else:
            print(f"📋 Multiple matches found:")
            for i, pubkey in enumerate(matches, 1):
                rep = self.reputation_system.get_reputation_summary(pubkey)
                print(f"{i}. {pubkey[:16]}... - {rep.get('reliability', 'No Data')}")
            
            choice = input("Select seller (number): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(matches):
                self.view_seller_profile(matches[int(choice) - 1])
            else:
                print("❌ Invalid choice")
        
        input("Press Enter to continue...")
    
    def show_reputation_analytics(self):
        """Show reputation system analytics."""
        print(f"\n📊 REPUTATION ANALYTICS")
        print("=" * 40)
        
        # Overall marketplace stats
        all_sellers = set(data["event"]["pubkey"] for data in self.listings.values())
        
        print(f"🌐 Marketplace Overview:")
        print(f"   👥 Total Sellers: {len(all_sellers)}")
        print(f"   📦 Total Listings: {len(self.listings)}")
        
        # Reputation distribution
        reputation_data = []
        for seller_pubkey in all_sellers:
            rep = self.reputation_system.get_reputation_summary(seller_pubkey)
            reputation_data.append(rep)
        
        # Calculate averages
        with_data = [r for r in reputation_data if r.get('total_transactions', 0) > 0]
        
        if with_data:
            avg_rating = sum(r.get('overall_score', 0) for r in with_data) / len(with_data)
            avg_transactions = sum(r.get('total_transactions', 0) for r in with_data) / len(with_data)
            total_volume = sum(r.get('total_volume_btc', 0) for r in with_data)
            
            print(f"\n📈 Reputation Statistics:")
            print(f"   ⭐ Average Rating: {avg_rating:.1f}/5.0")
            print(f"   📊 Average Transactions per Seller: {avg_transactions:.1f}")
            print(f"   💰 Total Marketplace Volume: {total_volume:.3f} BTC")
            print(f"   🏆 Sellers with Data: {len(with_data)}/{len(all_sellers)}")
        
        # Rating distribution
        print(f"\n🏆 Rating Distribution:")
        excellent = sum(1 for r in with_data if r.get('overall_score', 0) >= 4.5)
        good = sum(1 for r in with_data if 3.5 <= r.get('overall_score', 0) < 4.5)
        average = sum(1 for r in with_data if 2.5 <= r.get('overall_score', 0) < 3.5)
        poor = sum(1 for r in with_data if r.get('overall_score', 0) < 2.5)
        
        print(f"   🌟 Excellent (4.5+): {excellent}")
        print(f"   👍 Good (3.5-4.4): {good}")
        print(f"   😐 Average (2.5-3.4): {average}")
        print(f"   👎 Poor (<2.5): {poor}")
        
        input("Press Enter to continue...")
    
    def create_invoice(self):
        """Create a Lightning invoice."""
        print(f"\n📄 CREATE LIGHTNING INVOICE")
        print("=" * 40)
        
        try:
            amount = input("Amount (sats): ").strip()
            if not amount.isdigit():
                print("❌ Invalid amount")
                input("Press Enter to continue...")
                return
            
            description = input("Description: ").strip() or "DOMP payment"
            
            invoice = self.lightning_node.create_invoice(
                amount_sats=int(amount),
                description=description
            )
            
            print(f"\n✅ Invoice created:")
            print(f"   Invoice: {invoice}")
            print(f"   Amount: {amount} sats")
            print(f"   Description: {description}")
            
        except Exception as e:
            print(f"❌ Error creating invoice: {e}")
        
        input("\nPress Enter to continue...")
    
    def pay_invoice(self):
        """Pay a Lightning invoice."""
        print(f"\n⚡ PAY LIGHTNING INVOICE")
        print("=" * 40)
        print(f"💰 Your balance: {self.lightning_node.get_balance():,} sats")
        
        try:
            invoice = input("Enter invoice to pay: ").strip()
            if not invoice:
                print("❌ No invoice entered")
                input("Press Enter to continue...")
                return
            
            # For demo, we'll simulate paying our own invoices
            if invoice in self.lightning_node.invoices:
                invoice_data = self.lightning_node.invoices[invoice]
                print(f"\n📄 Invoice Details:")
                print(f"   Amount: {invoice_data['amount_sats']:,} sats")
                print(f"   Description: {invoice_data['description']}")
                
                confirm = input("Pay this invoice? (y/n): ").strip().lower()
                if confirm == 'y':
                    payment_hash = self.lightning_node.pay_invoice(invoice)
                    print(f"\n✅ Payment completed!")
                    print(f"   Payment hash: {payment_hash[:16]}...")
                    print(f"   New balance: {self.lightning_node.get_balance():,} sats")
            else:
                print("❌ Invoice not found (demo only supports paying own invoices)")
                
        except Exception as e:
            print(f"❌ Payment failed: {e}")
        
        input("\nPress Enter to continue...")
    
    def show_payment_history(self):
        """Show Lightning payment history."""
        print(f"\n📋 LIGHTNING PAYMENT HISTORY")
        print("=" * 40)
        
        if not self.lightning_node.payments:
            print("📭 No payments yet")
        else:
            print(f"💸 Recent Payments:")
            for payment_hash, payment_data in list(self.lightning_node.payments.items())[-10:]:
                print(f"   {payment_hash[:16]}... - {payment_data['amount_sats']:,} sats")
                print(f"      Invoice: {payment_data['invoice'][:30]}...")
                if payment_data.get('paid_at'):
                    print(f"      Paid: {time.ctime(payment_data['paid_at'])}")
                print()
        
        print(f"📊 Summary:")
        print(f"   Total Payments: {len(self.lightning_node.payments)}")
        print(f"   Current Balance: {self.lightning_node.get_balance():,} sats")
        
        input("Press Enter to continue...")
    
    def check_lightning_escrows(self):
        """Check Lightning escrows status."""
        print(f"\n🔒 LIGHTNING ESCROWS STATUS")
        print("=" * 40)
        
        if not self.escrow_manager.escrows:
            print("📭 No escrows found")
        else:
            print(f"⚡ All Escrows:")
            for escrow_id, escrow in self.escrow_manager.escrows.items():
                print(f"   {escrow_id}: {escrow.state.value}")
                print(f"      Amount: {escrow.purchase_amount_sats:,} sats")
                if escrow.state.value == "active":
                    remaining = max(0, escrow.expires_at - int(time.time()))
                    print(f"      Time remaining: {remaining} seconds")
                print()
        
        # Show active escrows
        active_escrows = [e for e in self.escrow_manager.escrows.values() 
                         if e.state.value == "active"]
        
        print(f"📊 Summary:")
        print(f"   Total Escrows: {len(self.escrow_manager.escrows)}")
        print(f"   Active Escrows: {len(active_escrows)}")
        
        input("Press Enter to continue...")


def main():
    """Main CLI entry point."""
    try:
        cli = DOOMPMarketplaceCLI()
        cli.start()
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using DOMP Marketplace!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()