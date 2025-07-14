"""
DOMP event classes and utilities.
Provides typed event creation and manipulation.
"""

import time
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from .crypto import KeyPair, compute_event_id, sign_event


@dataclass
class Event:
    """Base DOMP event."""
    
    id: str = ""
    pubkey: str = ""
    created_at: int = 0
    kind: int = 0
    tags: List[List[str]] = None
    content: str = ""
    sig: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at == 0:
            self.created_at = int(time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), separators=(',', ':'))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(**data)
    
    @classmethod 
    def from_json(cls, json_str: str) -> 'Event':
        """Create event from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def sign(self, keypair: KeyPair) -> None:
        """Sign the event with given keypair."""
        self.pubkey = keypair.public_key_hex
        
        # Check if this event has PoW (anti-spam proof) - if so, preserve existing ID
        has_pow = False
        for tag in self.tags:
            if len(tag) >= 2 and tag[0] == "anti_spam_proof" and tag[1] == "pow":
                has_pow = True
                break
        
        # Only compute new ID if no PoW exists (preserves PoW-generated IDs)
        if not has_pow:
            event_data = self.to_dict()
            event_data.pop('id', None)
            event_data.pop('sig', None)
            
            self.id = compute_event_id(event_data)
        
        # Sign the event (signatures are computed on the event ID)
        self.sig = sign_event({"id": self.id}, keypair)


class ProductListing(Event):
    """Product listing event (kind-300)."""
    
    def __init__(self, 
                 product_name: str,
                 description: str, 
                 price_satoshis: int,
                 category: str = "",
                 storage_link: str = "",
                 seller_collateral_satoshis: int = 0,
                 shipping_info: Dict[str, Any] = None,
                 listing_id: str = "",
                 anti_spam_proof: List[str] = None,
                 **kwargs):
        
        content_data = {
            "product_name": product_name,
            "description": description,
            "price_satoshis": price_satoshis
        }
        
        if category:
            content_data["category"] = category
        if storage_link:
            content_data["storage_link"] = storage_link
        if seller_collateral_satoshis > 0:
            content_data["seller_collateral_satoshis"] = seller_collateral_satoshis
        if shipping_info:
            content_data["shipping_info"] = shipping_info
            
        tags = []
        if listing_id:
            tags.append(["d", listing_id])
        if anti_spam_proof:
            tags.append(["anti_spam_proof"] + anti_spam_proof)
            
        super().__init__(
            kind=300,
            tags=tags,
            content=json.dumps(content_data, separators=(',', ':')),
            **kwargs
        )


class BidSubmission(Event):
    """Bid submission event (kind-301)."""
    
    def __init__(self,
                 product_ref: str,
                 bid_amount_satoshis: int,
                 buyer_collateral_satoshis: int,
                 message: str = "",
                 shipping_address_hash: str = "",
                 payment_timeout_hours: int = 24,
                 anti_spam_proof: List[str] = None,
                 relay_hint: str = "",
                 **kwargs):
        
        content_data = {
            "product_ref": product_ref,
            "bid_amount_satoshis": bid_amount_satoshis,
            "buyer_collateral_satoshis": buyer_collateral_satoshis
        }
        
        if message:
            content_data["message"] = message
        if shipping_address_hash:
            content_data["shipping_address_hash"] = shipping_address_hash
        if payment_timeout_hours != 24:
            content_data["payment_timeout_hours"] = payment_timeout_hours
            
        tags = []
        if anti_spam_proof:
            tags.append(["anti_spam_proof"] + anti_spam_proof)
        if product_ref:
            tags.append(["ref", product_ref, relay_hint or "", "root"])
            
        super().__init__(
            kind=301,
            tags=tags,
            content=json.dumps(content_data, separators=(',', ':')),
            **kwargs
        )


class BidAcceptance(Event):
    """Bid acceptance event (kind-303)."""
    
    def __init__(self,
                 bid_ref: str,
                 ln_invoice: str,
                 collateral_invoice: str = "",
                 estimated_shipping_time: str = "",
                 shipping_time_days: int = 0,
                 terms: str = "",
                 invoice_expiry_seconds: int = 3600,
                 htlc_timeout_blocks: int = 144,
                 anti_spam_proof: List[str] = None,
                 relay_hint: str = "",
                 **kwargs):
        
        content_data = {
            "bid_ref": bid_ref,
            "ln_invoice": ln_invoice
        }
        
        if collateral_invoice:
            content_data["collateral_invoice"] = collateral_invoice
        if estimated_shipping_time:
            content_data["estimated_shipping_time"] = estimated_shipping_time
        if shipping_time_days > 0:
            content_data["shipping_time_days"] = shipping_time_days
        if terms:
            content_data["terms"] = terms
        if invoice_expiry_seconds != 3600:
            content_data["invoice_expiry_seconds"] = invoice_expiry_seconds
        if htlc_timeout_blocks != 144:
            content_data["htlc_timeout_blocks"] = htlc_timeout_blocks
            
        tags = []
        if anti_spam_proof:
            tags.append(["anti_spam_proof"] + anti_spam_proof)
        if bid_ref:
            tags.append(["ref", bid_ref, relay_hint or "", "reply"])
            
        super().__init__(
            kind=303,
            tags=tags,
            content=json.dumps(content_data, separators=(',', ':')),
            **kwargs
        )


class PaymentConfirmation(Event):
    """Payment confirmation event (kind-311)."""
    
    def __init__(self,
                 bid_ref: str,
                 payment_proof: str,
                 payment_method: str = "lightning_htlc",
                 collateral_proof: str = "",
                 escrow_timeout_blocks: int = 144,
                 encrypted_shipping_address: str = "",
                 shipping_instructions: str = "",
                 payment_timestamp: int = 0,
                 anti_spam_proof: List[str] = None,
                 relay_hint: str = "",
                 **kwargs):
        
        content_data = {
            "bid_ref": bid_ref,
            "payment_proof": payment_proof,
            "payment_method": payment_method
        }
        
        if collateral_proof:
            content_data["collateral_proof"] = collateral_proof
        if escrow_timeout_blocks != 144:
            content_data["escrow_timeout_blocks"] = escrow_timeout_blocks
        if encrypted_shipping_address:
            content_data["encrypted_shipping_address"] = encrypted_shipping_address
        if shipping_instructions:
            content_data["shipping_instructions"] = shipping_instructions
        if payment_timestamp == 0:
            payment_timestamp = int(time.time())
        content_data["payment_timestamp"] = payment_timestamp
            
        tags = []
        if anti_spam_proof:
            tags.append(["anti_spam_proof"] + anti_spam_proof)
        if bid_ref:
            tags.append(["ref", bid_ref, relay_hint or "", "reply"])
            
        super().__init__(
            kind=311,
            tags=tags,
            content=json.dumps(content_data, separators=(',', ':')),
            **kwargs
        )


class ReceiptConfirmation(Event):
    """Receipt confirmation event (kind-313)."""
    
    def __init__(self,
                 payment_ref: str,
                 status: str = "received",
                 rating: int = 0,
                 feedback: str = "",
                 delivery_confirmation_time: int = 0,
                 item_condition: str = "",
                 shipping_rating: int = 0,
                 communication_rating: int = 0,
                 would_buy_again: bool = True,
                 dispute_reason: str = "",
                 anti_spam_proof: List[str] = None,
                 relay_hint: str = "",
                 **kwargs):
        
        content_data = {
            "payment_ref": payment_ref,
            "status": status
        }
        
        if rating > 0:
            content_data["rating"] = rating
        if feedback:
            content_data["feedback"] = feedback
        if delivery_confirmation_time == 0:
            delivery_confirmation_time = int(time.time())
        content_data["delivery_confirmation_time"] = delivery_confirmation_time
        if item_condition:
            content_data["item_condition"] = item_condition
        if shipping_rating > 0:
            content_data["shipping_rating"] = shipping_rating
        if communication_rating > 0:
            content_data["communication_rating"] = communication_rating
        content_data["would_buy_again"] = would_buy_again
        if dispute_reason and status != "received":
            content_data["dispute_reason"] = dispute_reason
            
        tags = []
        if anti_spam_proof:
            tags.append(["anti_spam_proof"] + anti_spam_proof)
        if payment_ref:
            tags.append(["ref", payment_ref, relay_hint or "", "reply"])
            
        super().__init__(
            kind=313,
            tags=tags,
            content=json.dumps(content_data, separators=(',', ':')),
            **kwargs
        )


def create_event_from_dict(data: Dict[str, Any]) -> Event:
    """Create appropriate event class from dictionary based on kind."""
    kind = data.get("kind")
    
    if kind == 300:
        return ProductListing.from_dict(data)
    elif kind == 301:
        return BidSubmission.from_dict(data)
    elif kind == 303:
        return BidAcceptance.from_dict(data)
    elif kind == 311:
        return PaymentConfirmation.from_dict(data)
    elif kind == 313:
        return ReceiptConfirmation.from_dict(data)
    else:
        return Event.from_dict(data)