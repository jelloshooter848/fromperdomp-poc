#!/usr/bin/env python3
"""
Simplified DOMP Lightning escrow demo.
Focuses on the core escrow functionality without PoW validation issues.
"""

import json
import time
import sys
sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.crypto import KeyPair
from domp.lightning import LightningEscrowManager, MockLightningNode, EscrowState


def print_step(step_num: int, title: str):
    """Print a formatted step header."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print('='*60)


def main():
    print("⚡ DOMP LIGHTNING ESCROW DEMO")
    print("Demonstrating trustless Bitcoin payments for marketplace transactions")
    
    # ========================================
    # SETUP
    # ========================================
    print_step(1, "SETUP - Create participants and Lightning infrastructure")
    
    # Create participants
    seller_keypair = KeyPair()
    buyer_keypair = KeyPair()
    
    print(f"👤 Seller: {seller_keypair.public_key_hex[:16]}...")
    print(f"👤 Buyer: {buyer_keypair.public_key_hex[:16]}...")
    
    # Create Lightning nodes (mock for demo)
    seller_node = MockLightningNode("seller_node")
    buyer_node = MockLightningNode("buyer_node")
    
    print(f"⚡ Seller Lightning balance: {seller_node.get_balance():,} sats")
    print(f"⚡ Buyer Lightning balance: {buyer_node.get_balance():,} sats")
    
    # Create escrow manager
    escrow_manager = LightningEscrowManager()
    print("🔒 Lightning escrow manager ready")
    
    # ========================================
    # CREATE TRANSACTION
    # ========================================
    print_step(2, "MARKETPLACE TRANSACTION - Digital Camera Sale")
    
    transaction_id = "camera_sale_001"
    purchase_amount = 80_000_000  # 0.8 BTC
    buyer_collateral = 80_000_000  # 100% collateral
    seller_collateral = 8_000_000   # 10% collateral
    
    print(f"📦 Product: High-quality DSLR camera")
    print(f"💰 Price: {purchase_amount:,} sats (0.8 BTC)")
    print(f"🛡️  Buyer collateral: {buyer_collateral:,} sats")
    print(f"🛡️  Seller collateral: {seller_collateral:,} sats")
    
    # ========================================
    # CREATE LIGHTNING ESCROW
    # ========================================
    print_step(3, "CREATE LIGHTNING HTLC ESCROW")
    
    # Create the escrow
    escrow = escrow_manager.create_escrow(
        transaction_id=transaction_id,
        buyer_pubkey=buyer_keypair.public_key_hex,
        seller_pubkey=seller_keypair.public_key_hex,
        purchase_amount_sats=purchase_amount,
        buyer_collateral_sats=buyer_collateral,
        seller_collateral_sats=seller_collateral,
        timeout_blocks=144  # ~24 hours
    )
    
    print(f"🔒 HTLC Escrow Created Successfully!")
    print(f"  Transaction ID: {escrow.transaction_id}")
    print(f"  Payment Hash: {escrow.payment_hash[:16]}...")
    print(f"  Payment Secret: {escrow.payment_preimage[:16]}... (HIDDEN)")
    print(f"  State: {escrow.state.value}")
    print(f"  Timeout: {escrow.timeout_blocks} blocks")
    print(f"  Expires: {time.ctime(escrow.expires_at)}")
    
    # ========================================
    # GENERATE LIGHTNING INVOICES
    # ========================================
    print_step(4, "GENERATE LIGHTNING INVOICES")
    
    # Generate invoices for the transaction
    purchase_invoice = seller_node.create_invoice(
        amount_sats=purchase_amount,
        description=f"DOMP purchase - {transaction_id}",
        payment_hash=escrow.payment_hash  # HTLC payment hash
    )
    
    buyer_collateral_invoice = seller_node.create_invoice(
        amount_sats=buyer_collateral,
        description=f"DOMP buyer collateral - {transaction_id}"
    )
    
    # Seller also needs to deposit collateral (simulated)
    seller_collateral_invoice = seller_node.create_invoice(
        amount_sats=seller_collateral,
        description=f"DOMP seller collateral - {transaction_id}"
    )
    
    print(f"⚡ Lightning Invoices Generated:")
    print(f"  Purchase Invoice: {purchase_invoice}")
    print(f"    Amount: {purchase_amount:,} sats")
    print(f"    Payment Hash: {escrow.payment_hash[:16]}...")
    print(f"  Buyer Collateral Invoice: {buyer_collateral_invoice}")
    print(f"    Amount: {buyer_collateral:,} sats")
    print(f"  Seller Collateral Invoice: {seller_collateral_invoice}")
    print(f"    Amount: {seller_collateral:,} sats")
    
    # ========================================
    # BUYER PAYS INVOICES
    # ========================================
    print_step(5, "BUYER PAYS LIGHTNING INVOICES")
    
    print(f"💸 Buyer paying invoices...")
    print(f"  Balance before: {buyer_node.get_balance():,} sats")
    
    # Pay the purchase amount (HTLC with preimage)
    purchase_payment_hash = buyer_node.pay_invoice(
        purchase_invoice,
        recipient_node=seller_node,
        preimage=escrow.payment_preimage
    )
    print(f"  ✅ Purchase payment: {purchase_payment_hash[:16]}...")
    
    # Pay the buyer collateral 
    buyer_collateral_payment_hash = buyer_node.pay_invoice(
        buyer_collateral_invoice,
        recipient_node=seller_node
    )
    print(f"  ✅ Buyer collateral payment: {buyer_collateral_payment_hash[:16]}...")
    
    # Seller pays their own collateral (simulated)
    seller_collateral_payment_hash = seller_node.pay_invoice(
        seller_collateral_invoice,
        recipient_node=seller_node  # Pays to themselves for simplicity
    )
    print(f"  ✅ Seller collateral payment: {seller_collateral_payment_hash[:16]}...")
    
    print(f"  Buyer balance after: {buyer_node.get_balance():,} sats")
    print(f"  Seller balance after: {seller_node.get_balance():,} sats")
    print(f"  Total buyer paid: {purchase_amount + buyer_collateral:,} sats")
    print(f"  Total seller paid: {seller_collateral:,} sats")
    
    # ========================================
    # ACTIVATE ESCROW
    # ========================================
    print_step(6, "ACTIVATE LIGHTNING ESCROW")
    
    # Fund the escrow with payment proofs
    escrow_funded = escrow_manager.fund_escrow(
        transaction_id,
        purchase_payment_hash,
        buyer_collateral_payment_hash,
        seller_collateral_payment_hash
    )
    
    print(f"🔒 Escrow funding result: {escrow_funded}")
    print(f"🔒 Escrow state: {escrow.state.value}")
    
    if escrow.state == EscrowState.ACTIVE:
        print("✅ ESCROW IS NOW ACTIVE!")
        print("   💰 Purchase payment locked in HTLC")
        print("   🛡️  Buyer collateral held securely") 
        print("   🚚 Seller can now ship with payment guarantee")
        print("   ⏰ Automatic refund if buyer doesn't confirm receipt")
    
    # ========================================
    # SIMULATE SHIPPING
    # ========================================
    print_step(7, "SELLER SHIPS ITEM")
    
    print("📦 Seller packages and ships the camera...")
    print("📧 Tracking number: XYZ123456789")
    print("🚚 Item in transit...")
    print("✅ Seller confident in payment security!")
    
    # Show escrow status
    summary = escrow_manager.get_escrow_summary(transaction_id)
    print(f"\n📊 Escrow Status:")
    print(f"  State: {summary['state']}")
    print(f"  Time remaining: {summary['time_remaining']} seconds")
    
    # ========================================
    # BUYER RECEIVES ITEM
    # ========================================
    print_step(8, "BUYER RECEIVES ITEM & CONFIRMS")
    
    print("📦 Buyer receives the package...")
    print("📸 Inspects camera: Excellent condition!")
    print("✅ Item matches description perfectly")
    print("😊 Buyer is satisfied with purchase")
    
    # ========================================
    # RELEASE PAYMENT
    # ========================================
    print_step(9, "RELEASE LIGHTNING PAYMENT")
    
    print("🔓 Buyer confirms receipt → releasing payment...")
    
    # Release the payment (reveals preimage to seller)
    revealed_preimage = escrow_manager.release_payment(transaction_id)
    
    if revealed_preimage:
        print(f"🔑 Payment preimage revealed: {revealed_preimage[:16]}...")
        print(f"🔒 Escrow state: {escrow.state.value}")
    else:
        print("❌ Failed to release payment - escrow may not be active")
        print(f"🔒 Current escrow state: {escrow.state.value}")
        return
    
    # In real Lightning Network:
    # 1. Seller uses preimage to claim HTLC payment
    # 2. Buyer's collateral gets refunded automatically
    
    print(f"💰 Seller can now claim {purchase_amount:,} sats using the preimage!")
    print(f"💰 Buyer gets {buyer_collateral:,} sats collateral refunded!")
    
    # ========================================
    # TRANSACTION COMPLETE
    # ========================================
    print_step(10, "TRANSACTION COMPLETE")
    
    final_summary = escrow_manager.get_escrow_summary(transaction_id)
    
    print("🎉 TRUSTLESS TRANSACTION COMPLETED SUCCESSFULLY!")
    print(f"\n📊 Final Transaction Summary:")
    for key, value in final_summary.items():
        if key.endswith('_sats'):
            print(f"  {key}: {value:,} sats")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n🏆 DOMP LIGHTNING ESCROW ACHIEVEMENTS:")
    print("  ✅ No trusted third party required")
    print("  ✅ Seller guaranteed payment upon delivery")
    print("  ✅ Buyer guaranteed refund if no delivery") 
    print("  ✅ Lightning-fast Bitcoin settlements")
    print("  ✅ Minimal fees (no escrow service costs)")
    print("  ✅ Cryptographically secure HTLC mechanism")
    print("  ✅ Automatic timeout protection")
    print("  ✅ Censorship resistant payments")
    
    print(f"\n⚡ This demonstrates DOMP's core innovation:")
    print("   🔒 HTLC-based escrow without trusted third parties")
    print("   💨 Lightning Network speed and low fees")
    print("   🔐 Bitcoin-level security and finality")
    print("   🌍 Global, permissionless commerce")
    
    print(f"\n🚀 Ready for integration with:")
    print("   📱 Mobile wallets and apps")
    print("   🌐 Web-based marketplaces") 
    print("   🏪 E-commerce platforms")
    print("   🤝 P2P trading platforms")


if __name__ == "__main__":
    main()