"""
Lightning Network integration for DOMP escrow.
Handles HTLC creation, monitoring, and trustless payment flows.
"""

import asyncio
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum


class EscrowState(Enum):
    """Escrow transaction states."""
    PENDING = "pending"
    ACTIVE = "active"  
    COMPLETED = "completed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


@dataclass
class HTLCEscrow:
    """HTLC-based escrow for DOMP transactions."""
    
    # Transaction identifiers
    transaction_id: str
    buyer_pubkey: str
    seller_pubkey: str
    
    # Payment details
    purchase_amount_sats: int
    buyer_collateral_sats: int
    seller_collateral_sats: int
    
    # HTLC details
    payment_hash: str
    payment_preimage: Optional[str] = None
    timeout_blocks: int = 144
    
    # State tracking
    state: EscrowState = EscrowState.PENDING
    created_at: int = None
    expires_at: int = None
    
    # Lightning payment details
    buyer_payment_hash: Optional[str] = None
    buyer_collateral_hash: Optional[str] = None
    seller_collateral_hash: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = int(time.time())
        if self.expires_at is None:
            self.expires_at = self.created_at + (self.timeout_blocks * 600)  # ~10 min per block


class LightningEscrowManager:
    """Manages Lightning HTLC escrows for DOMP transactions."""
    
    def __init__(self):
        self.escrows: Dict[str, HTLCEscrow] = {}
        self.preimages: Dict[str, str] = {}  # payment_hash -> preimage
    
    def generate_payment_secret(self) -> Tuple[str, str]:
        """
        Generate a payment secret and hash for HTLC.
        
        Returns:
            Tuple of (preimage_hex, payment_hash_hex)
        """
        preimage = secrets.token_bytes(32)
        payment_hash = hashlib.sha256(preimage).digest()
        
        preimage_hex = preimage.hex()
        payment_hash_hex = payment_hash.hex()
        
        # Store the preimage for later use
        self.preimages[payment_hash_hex] = preimage_hex
        
        return preimage_hex, payment_hash_hex
    
    def create_escrow(self,
                     transaction_id: str,
                     buyer_pubkey: str, 
                     seller_pubkey: str,
                     purchase_amount_sats: int,
                     buyer_collateral_sats: int = 0,
                     seller_collateral_sats: int = 0,
                     timeout_blocks: int = 144) -> HTLCEscrow:
        """
        Create a new HTLC escrow for a DOMP transaction.
        
        Args:
            transaction_id: Unique identifier for the transaction
            buyer_pubkey: Buyer's public key
            seller_pubkey: Seller's public key  
            purchase_amount_sats: Amount buyer pays for item
            buyer_collateral_sats: Buyer's collateral deposit
            seller_collateral_sats: Seller's collateral deposit
            timeout_blocks: HTLC timeout in blocks
            
        Returns:
            HTLCEscrow object
        """
        # Generate payment secret for this escrow
        preimage, payment_hash = self.generate_payment_secret()
        
        escrow = HTLCEscrow(
            transaction_id=transaction_id,
            buyer_pubkey=buyer_pubkey,
            seller_pubkey=seller_pubkey,
            purchase_amount_sats=purchase_amount_sats,
            buyer_collateral_sats=buyer_collateral_sats,
            seller_collateral_sats=seller_collateral_sats,
            payment_hash=payment_hash,
            payment_preimage=preimage,
            timeout_blocks=timeout_blocks
        )
        
        self.escrows[transaction_id] = escrow
        return escrow
    
    def get_escrow(self, transaction_id: str) -> Optional[HTLCEscrow]:
        """Get escrow by transaction ID."""
        return self.escrows.get(transaction_id)
    
    def fund_escrow(self, 
                   transaction_id: str,
                   buyer_payment_hash: str,
                   buyer_collateral_hash: Optional[str] = None,
                   seller_collateral_hash: Optional[str] = None) -> bool:
        """
        Mark escrow as funded when all required payments are made.
        
        Args:
            transaction_id: Transaction identifier
            buyer_payment_hash: Hash of buyer's purchase payment
            buyer_collateral_hash: Hash of buyer's collateral payment
            seller_collateral_hash: Hash of seller's collateral payment
            
        Returns:
            True if escrow is now fully funded
        """
        escrow = self.escrows.get(transaction_id)
        if not escrow:
            return False
        
        # Update payment hashes
        escrow.buyer_payment_hash = buyer_payment_hash
        if buyer_collateral_hash:
            escrow.buyer_collateral_hash = buyer_collateral_hash
        if seller_collateral_hash:
            escrow.seller_collateral_hash = seller_collateral_hash
        
        # Check if all required payments are present
        required_payments = [buyer_payment_hash]
        if escrow.buyer_collateral_sats > 0:
            required_payments.append(buyer_collateral_hash)
        if escrow.seller_collateral_sats > 0:
            required_payments.append(seller_collateral_hash)
        
        if all(payment for payment in required_payments):
            escrow.state = EscrowState.ACTIVE
            return True
        
        return False
    
    def release_payment(self, transaction_id: str) -> Optional[str]:
        """
        Release payment to seller by revealing preimage.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            Payment preimage if released, None if error
        """
        escrow = self.escrows.get(transaction_id)
        if not escrow or escrow.state != EscrowState.ACTIVE:
            return None
        
        # Mark as completed and return preimage
        escrow.state = EscrowState.COMPLETED
        return escrow.payment_preimage
    
    def refund_payment(self, transaction_id: str) -> bool:
        """
        Mark payment as refunded (timeout occurred).
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            True if refund processed
        """
        escrow = self.escrows.get(transaction_id)
        if not escrow:
            return False
        
        escrow.state = EscrowState.REFUNDED
        return True
    
    def check_timeouts(self) -> List[str]:
        """
        Check for expired escrows and mark them for refund.
        
        Returns:
            List of transaction IDs that have expired
        """
        current_time = int(time.time())
        expired_transactions = []
        
        for transaction_id, escrow in self.escrows.items():
            if (escrow.state == EscrowState.ACTIVE and 
                current_time > escrow.expires_at):
                escrow.state = EscrowState.EXPIRED
                expired_transactions.append(transaction_id)
        
        return expired_transactions
    
    def get_escrow_summary(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get human-readable escrow summary.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            Dictionary with escrow details
        """
        escrow = self.escrows.get(transaction_id)
        if not escrow:
            return None
        
        return {
            "transaction_id": escrow.transaction_id,
            "state": escrow.state.value,
            "buyer": escrow.buyer_pubkey[:16] + "...",
            "seller": escrow.seller_pubkey[:16] + "...", 
            "purchase_amount_sats": escrow.purchase_amount_sats,
            "buyer_collateral_sats": escrow.buyer_collateral_sats,
            "seller_collateral_sats": escrow.seller_collateral_sats,
            "payment_hash": escrow.payment_hash,
            "created_at": escrow.created_at,
            "expires_at": escrow.expires_at,
            "time_remaining": max(0, escrow.expires_at - int(time.time()))
        }


class MockLightningNode:
    """
    Mock Lightning node for testing DOMP escrow functionality.
    In production, this would integrate with actual Lightning implementations.
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.balance_sats = 1000000000  # 10 BTC for testing
        self.invoices: Dict[str, Dict[str, Any]] = {}
        self.payments: Dict[str, Dict[str, Any]] = {}
    
    def create_invoice(self, 
                      amount_sats: int,
                      description: str,
                      payment_hash: Optional[str] = None) -> str:
        """
        Create a Lightning invoice.
        
        Args:
            amount_sats: Invoice amount in satoshis
            description: Invoice description
            payment_hash: Optional payment hash for HTLC
            
        Returns:
            Invoice string (bolt11 format)
        """
        if payment_hash is None:
            # Generate random payment hash for regular invoices
            payment_hash = secrets.token_bytes(32).hex()
        
        invoice_id = f"lnbc{amount_sats}1p{secrets.token_hex(20)}"
        
        self.invoices[invoice_id] = {
            "amount_sats": amount_sats,
            "description": description,
            "payment_hash": payment_hash,
            "created_at": int(time.time()),
            "paid": False
        }
        
        return invoice_id
    
    def pay_invoice(self, invoice: str, recipient_node: 'MockLightningNode' = None, preimage: Optional[str] = None) -> str:
        """
        Pay a Lightning invoice (cross-node payment simulation).
        
        Args:
            invoice: Invoice string to pay
            recipient_node: Node that created the invoice
            preimage: Payment preimage for HTLC payments
            
        Returns:
            Payment hash of completed payment
        """
        # For mock purposes, allow paying any invoice if recipient_node is provided
        if recipient_node and invoice in recipient_node.invoices:
            invoice_data = recipient_node.invoices[invoice]
        elif invoice in self.invoices:
            invoice_data = self.invoices[invoice]
        else:
            raise ValueError(f"Unknown invoice: {invoice}")
        
        if invoice_data["paid"]:
            raise ValueError(f"Invoice already paid: {invoice}")
        
        if self.balance_sats < invoice_data["amount_sats"]:
            raise ValueError("Insufficient balance")
        
        # Deduct from payer balance
        self.balance_sats -= invoice_data["amount_sats"]
        
        # Add to recipient balance (if different node)
        if recipient_node and recipient_node != self:
            recipient_node.balance_sats += invoice_data["amount_sats"]
        
        # Mark invoice as paid
        invoice_data["paid"] = True
        invoice_data["paid_at"] = int(time.time())
        
        # Record payment on both nodes
        payment_hash = invoice_data["payment_hash"]
        payment_record = {
            "invoice": invoice,
            "amount_sats": invoice_data["amount_sats"],
            "preimage": preimage,
            "paid_at": int(time.time())
        }
        
        self.payments[payment_hash] = payment_record
        if recipient_node and recipient_node != self:
            recipient_node.payments[payment_hash] = payment_record
        
        return payment_hash
    
    def get_payment_status(self, payment_hash: str) -> Optional[Dict[str, Any]]:
        """Get status of a payment by hash."""
        return self.payments.get(payment_hash)
    
    def get_balance(self) -> int:
        """Get current node balance in satoshis."""
        return self.balance_sats


# Integration helpers for DOMP events
def create_escrow_from_events(escrow_manager: LightningEscrowManager,
                             listing_event: Dict[str, Any],
                             bid_event: Dict[str, Any],
                             acceptance_event: Dict[str, Any]) -> HTLCEscrow:
    """
    Create Lightning escrow from DOMP protocol events.
    
    Args:
        escrow_manager: Lightning escrow manager
        listing_event: kind-300 product listing event
        bid_event: kind-301 bid submission event  
        acceptance_event: kind-303 bid acceptance event
        
    Returns:
        Created HTLCEscrow object
    """
    import json
    
    # Parse event contents
    listing_content = json.loads(listing_event["content"])
    bid_content = json.loads(bid_event["content"])
    
    # Extract transaction details
    transaction_id = listing_event["id"]
    buyer_pubkey = bid_event["pubkey"]
    seller_pubkey = listing_event["pubkey"]
    purchase_amount = bid_content["bid_amount_satoshis"]
    buyer_collateral = bid_content.get("buyer_collateral_satoshis", 0)
    seller_collateral = listing_content.get("seller_collateral_satoshis", 0)
    
    # Create escrow
    escrow = escrow_manager.create_escrow(
        transaction_id=transaction_id,
        buyer_pubkey=buyer_pubkey,
        seller_pubkey=seller_pubkey,
        purchase_amount_sats=purchase_amount,
        buyer_collateral_sats=buyer_collateral,
        seller_collateral_sats=seller_collateral
    )
    
    return escrow


def generate_lightning_invoices(escrow: HTLCEscrow, 
                               seller_node: MockLightningNode) -> Dict[str, str]:
    """
    Generate Lightning invoices for a DOMP escrow.
    
    Args:
        escrow: HTLC escrow object
        seller_node: Seller's Lightning node
        
    Returns:
        Dictionary of invoice type -> invoice string
    """
    invoices = {}
    
    # Purchase amount invoice (with HTLC payment hash)
    purchase_invoice = seller_node.create_invoice(
        amount_sats=escrow.purchase_amount_sats,
        description=f"DOMP purchase - {escrow.transaction_id}",
        payment_hash=escrow.payment_hash
    )
    invoices["purchase"] = purchase_invoice
    
    # Buyer collateral invoice (if required)
    if escrow.buyer_collateral_sats > 0:
        collateral_invoice = seller_node.create_invoice(
            amount_sats=escrow.buyer_collateral_sats,
            description=f"DOMP buyer collateral - {escrow.transaction_id}"
        )
        invoices["buyer_collateral"] = collateral_invoice
    
    return invoices