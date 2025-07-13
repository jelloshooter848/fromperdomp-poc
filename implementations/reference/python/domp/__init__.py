"""
DOMP - Decentralized Online Marketplace Protocol

A reference implementation of the DOMP protocol for trustless peer-to-peer commerce.
Built on Bitcoin Lightning Network and Nostr protocol.
"""

__version__ = "0.1.0"
__author__ = "DOMP Protocol Contributors"

from .events import Event, ProductListing, BidSubmission, BidAcceptance, PaymentConfirmation, ReceiptConfirmation
from .crypto import KeyPair, sign_event, verify_event
from .validation import validate_event, validate_event_chain
from .client import DOMPClient

__all__ = [
    "Event",
    "ProductListing", 
    "BidSubmission",
    "BidAcceptance",
    "PaymentConfirmation",
    "ReceiptConfirmation",
    "KeyPair",
    "sign_event",
    "verify_event", 
    "validate_event",
    "validate_event_chain",
    "DOMPClient",
]