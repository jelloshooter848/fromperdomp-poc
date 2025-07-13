"""
DOMP Reputation System
Provides decentralized reputation scoring and verification for marketplace participants.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

from .crypto import KeyPair
from .events import Event


class ReputationMetric(Enum):
    """Types of reputation metrics."""
    TRANSACTION_SUCCESS = "transaction_success"
    ITEM_QUALITY = "item_quality" 
    SHIPPING_SPEED = "shipping_speed"
    COMMUNICATION = "communication"
    DISPUTE_RESOLUTION = "dispute_resolution"
    PAYMENT_RELIABILITY = "payment_reliability"


@dataclass
class ReputationScore:
    """Individual reputation score from a transaction."""
    
    # Transaction reference
    transaction_id: str
    reviewer_pubkey: str
    reviewed_pubkey: str
    
    # Metrics (1-5 scale)
    overall_rating: int
    item_quality: Optional[int] = None
    shipping_speed: Optional[int] = None
    communication: Optional[int] = None
    payment_reliability: Optional[int] = None
    
    # Context
    transaction_amount_sats: int = 0
    review_timestamp: int = 0
    review_text: str = ""
    
    # Verification
    verified_purchase: bool = False
    escrow_completed: bool = False
    
    def __post_init__(self):
        if self.review_timestamp == 0:
            self.review_timestamp = int(time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class AggregatedReputation:
    """Aggregated reputation for a marketplace participant."""
    
    pubkey: str
    
    # Overall metrics
    overall_score: float = 0.0
    total_transactions: int = 0
    total_volume_sats: int = 0
    
    # Detailed metrics
    avg_item_quality: float = 0.0
    avg_shipping_speed: float = 0.0
    avg_communication: float = 0.0
    avg_payment_reliability: float = 0.0
    
    # Trust indicators
    verified_purchases: int = 0
    completed_escrows: int = 0
    dispute_rate: float = 0.0
    
    # Time-based metrics
    first_transaction: int = 0
    last_transaction: int = 0
    transactions_last_30d: int = 0
    
    # Reviewer diversity
    unique_reviewers: int = 0
    review_concentration: float = 0.0  # Gini coefficient of review distribution
    
    def __post_init__(self):
        if self.total_transactions > 0:
            self.dispute_rate = min(self.dispute_rate, 1.0)
            self.review_concentration = min(self.review_concentration, 1.0)


class ReputationSystem:
    """DOMP reputation aggregation and scoring system."""
    
    def __init__(self):
        self.reputation_scores: Dict[str, List[ReputationScore]] = defaultdict(list)
        self.aggregated_reputation: Dict[str, AggregatedReputation] = {}
        
        # Reputation algorithm parameters
        self.decay_factor = 0.95  # Older reviews count less
        self.min_reviews_for_reliability = 5
        self.volume_weight_factor = 0.1  # Weight based on transaction volume
        self.verified_purchase_bonus = 0.2  # Bonus for verified purchases
        
    def add_reputation_score(self, score: ReputationScore) -> None:
        """Add a new reputation score."""
        pubkey = score.reviewed_pubkey
        
        # Validate score
        if not self._validate_score(score):
            raise ValueError("Invalid reputation score")
        
        # Add to scores
        self.reputation_scores[pubkey].append(score)
        
        # Update aggregated reputation
        self._update_aggregated_reputation(pubkey)
    
    def _validate_score(self, score: ReputationScore) -> bool:
        """Validate reputation score parameters."""
        # Check rating bounds
        if not (1 <= score.overall_rating <= 5):
            return False
        
        # Check optional ratings
        for rating in [score.item_quality, score.shipping_speed, 
                      score.communication, score.payment_reliability]:
            if rating is not None and not (1 <= rating <= 5):
                return False
        
        # Check transaction amount
        if score.transaction_amount_sats < 0:
            return False
        
        return True
    
    def _update_aggregated_reputation(self, pubkey: str) -> None:
        """Update aggregated reputation for a user."""
        scores = self.reputation_scores[pubkey]
        
        if not scores:
            return
        
        # Initialize aggregated reputation
        agg_rep = AggregatedReputation(pubkey=pubkey)
        
        # Calculate basic metrics
        agg_rep.total_transactions = len(scores)
        agg_rep.total_volume_sats = sum(s.transaction_amount_sats for s in scores)
        
        # Time-based metrics
        timestamps = [s.review_timestamp for s in scores]
        agg_rep.first_transaction = min(timestamps)
        agg_rep.last_transaction = max(timestamps)
        
        # Recent activity
        thirty_days_ago = int(time.time()) - (30 * 24 * 3600)
        agg_rep.transactions_last_30d = sum(1 for t in timestamps if t > thirty_days_ago)
        
        # Verification metrics
        agg_rep.verified_purchases = sum(1 for s in scores if s.verified_purchase)
        agg_rep.completed_escrows = sum(1 for s in scores if s.escrow_completed)
        
        # Calculate weighted averages
        agg_rep.overall_score = self._calculate_weighted_average(
            scores, lambda s: s.overall_rating
        )
        
        # Optional metric averages
        agg_rep.avg_item_quality = self._calculate_optional_average(
            scores, lambda s: s.item_quality
        )
        agg_rep.avg_shipping_speed = self._calculate_optional_average(
            scores, lambda s: s.shipping_speed
        )
        agg_rep.avg_communication = self._calculate_optional_average(
            scores, lambda s: s.communication
        )
        agg_rep.avg_payment_reliability = self._calculate_optional_average(
            scores, lambda s: s.payment_reliability
        )
        
        # Reviewer diversity
        reviewers = [s.reviewer_pubkey for s in scores]
        agg_rep.unique_reviewers = len(set(reviewers))
        agg_rep.review_concentration = self._calculate_gini_coefficient(reviewers)
        
        # Store aggregated reputation
        self.aggregated_reputation[pubkey] = agg_rep
    
    def _calculate_weighted_average(self, scores: List[ReputationScore], 
                                  value_func) -> float:
        """Calculate time-decay and volume-weighted average."""
        current_time = int(time.time())
        total_weight = 0.0
        weighted_sum = 0.0
        
        for score in scores:
            # Time decay weight
            days_old = (current_time - score.review_timestamp) / (24 * 3600)
            time_weight = self.decay_factor ** days_old
            
            # Volume weight (logarithmic scale)
            volume_weight = 1.0 + (self.volume_weight_factor * 
                                 (score.transaction_amount_sats / 1_000_000))  # Per 0.01 BTC
            
            # Verification bonus
            verification_weight = 1.0
            if score.verified_purchase:
                verification_weight += self.verified_purchase_bonus
            if score.escrow_completed:
                verification_weight += self.verified_purchase_bonus
            
            # Combined weight
            weight = time_weight * volume_weight * verification_weight
            
            total_weight += weight
            weighted_sum += value_func(score) * weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_optional_average(self, scores: List[ReputationScore],
                                  value_func) -> float:
        """Calculate average for optional metrics."""
        values = [value_func(s) for s in scores if value_func(s) is not None]
        return sum(values) / len(values) if values else 0.0
    
    def _calculate_gini_coefficient(self, reviewers: List[str]) -> float:
        """Calculate Gini coefficient for review concentration."""
        from collections import Counter
        
        if not reviewers:
            return 0.0
        
        # Count reviews per reviewer
        review_counts = list(Counter(reviewers).values())
        review_counts.sort()
        
        n = len(review_counts)
        cumsum = sum((i + 1) * count for i, count in enumerate(review_counts))
        
        return (2 * cumsum) / (n * sum(review_counts)) - (n + 1) / n
    
    def get_reputation(self, pubkey: str) -> Optional[AggregatedReputation]:
        """Get aggregated reputation for a user."""
        return self.aggregated_reputation.get(pubkey)
    
    def get_reputation_summary(self, pubkey: str) -> Dict[str, Any]:
        """Get human-readable reputation summary."""
        rep = self.get_reputation(pubkey)
        if not rep:
            return {
                "pubkey": pubkey[:16] + "...",
                "status": "No reputation data",
                "overall_score": 0.0,
                "total_transactions": 0
            }
        
        # Calculate reliability indicators
        reliability = "Unknown"
        if rep.total_transactions >= self.min_reviews_for_reliability:
            if rep.overall_score >= 4.5:
                reliability = "Excellent"
            elif rep.overall_score >= 4.0:
                reliability = "Good"
            elif rep.overall_score >= 3.5:
                reliability = "Average"
            elif rep.overall_score >= 2.5:
                reliability = "Below Average"
            else:
                reliability = "Poor"
        elif rep.total_transactions > 0:
            reliability = "New Seller" if rep.total_transactions < 3 else "Limited Data"
        
        return {
            "pubkey": pubkey[:16] + "...",
            "overall_score": round(rep.overall_score, 2),
            "reliability": reliability,
            "total_transactions": rep.total_transactions,
            "total_volume_btc": rep.total_volume_sats / 100_000_000,
            "verified_purchases": rep.verified_purchases,
            "completed_escrows": rep.completed_escrows,
            "item_quality": round(rep.avg_item_quality, 2) if rep.avg_item_quality else None,
            "shipping_speed": round(rep.avg_shipping_speed, 2) if rep.avg_shipping_speed else None,
            "communication": round(rep.avg_communication, 2) if rep.avg_communication else None,
            "payment_reliability": round(rep.avg_payment_reliability, 2) if rep.avg_payment_reliability else None,
            "unique_reviewers": rep.unique_reviewers,
            "review_concentration": round(rep.review_concentration, 3),
            "recent_activity": rep.transactions_last_30d,
            "account_age_days": (int(time.time()) - rep.first_transaction) // (24 * 3600) if rep.first_transaction else 0
        }
    
    def compare_sellers(self, pubkeys: List[str]) -> List[Dict[str, Any]]:
        """Compare multiple sellers by reputation."""
        summaries = []
        for pubkey in pubkeys:
            summary = self.get_reputation_summary(pubkey)
            summaries.append(summary)
        
        # Sort by overall score (descending)
        summaries.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return summaries
    
    def get_trust_score(self, pubkey: str) -> float:
        """Calculate overall trust score (0-1) considering all factors."""
        rep = self.get_reputation(pubkey)
        if not rep:
            return 0.0
        
        # Base score from ratings
        base_score = rep.overall_score / 5.0
        
        # Transaction volume factor
        volume_factor = min(1.0, rep.total_volume_sats / 100_000_000)  # Cap at 1 BTC
        
        # Verification factor
        verification_rate = (rep.verified_purchases + rep.completed_escrows) / (2 * rep.total_transactions) if rep.total_transactions > 0 else 0
        
        # Diversity factor (low concentration is good)
        diversity_factor = 1.0 - rep.review_concentration
        
        # Recency factor
        if rep.last_transaction > 0:
            days_since_last = (int(time.time()) - rep.last_transaction) / (24 * 3600)
            recency_factor = max(0.1, 1.0 - (days_since_last / 365))  # Decay over a year
        else:
            recency_factor = 0.1
        
        # Combine factors
        trust_score = (
            base_score * 0.4 +
            volume_factor * 0.2 +
            verification_rate * 0.2 +
            diversity_factor * 0.1 +
            recency_factor * 0.1
        )
        
        return min(1.0, trust_score)


def create_reputation_from_receipt_confirmation(receipt_event: Dict[str, Any],
                                              transaction_context: Dict[str, Any] = None) -> ReputationScore:
    """Create reputation score from DOMP receipt confirmation event."""
    content = json.loads(receipt_event["content"])
    
    # Extract metrics from receipt confirmation
    overall_rating = content.get("rating", 5)
    item_quality = 5 if content.get("item_condition") == "as_described" else 3
    shipping_speed = content.get("shipping_rating", 5)
    communication = content.get("communication_rating", 5)
    
    # Transaction context
    transaction_amount = transaction_context.get("amount_sats", 0) if transaction_context else 0
    
    return ReputationScore(
        transaction_id=content.get("payment_ref", "unknown"),
        reviewer_pubkey=receipt_event["pubkey"],
        reviewed_pubkey=transaction_context.get("seller_pubkey", "") if transaction_context else "",
        overall_rating=overall_rating,
        item_quality=item_quality,
        shipping_speed=shipping_speed,
        communication=communication,
        payment_reliability=5,  # Assume good if transaction completed
        transaction_amount_sats=transaction_amount,
        review_text=content.get("feedback", ""),
        verified_purchase=True,  # Receipt confirmations are verified purchases
        escrow_completed=True,   # Implies escrow was used
        review_timestamp=receipt_event["created_at"]
    )


def aggregate_marketplace_reputation(events: List[Dict[str, Any]]) -> Dict[str, AggregatedReputation]:
    """Aggregate reputation from a list of DOMP events."""
    reputation_system = ReputationSystem()
    
    # Extract transactions and their contexts
    transactions = {}
    
    # First pass: collect transaction context
    for event in events:
        if event["kind"] == 300:  # Product listing
            content = json.loads(event["content"])
            transactions[event["id"]] = {
                "seller_pubkey": event["pubkey"],
                "amount_sats": content.get("price_satoshis", 0)
            }
        elif event["kind"] == 313:  # Receipt confirmation
            content = json.loads(event["content"])
            payment_ref = content.get("payment_ref")
            if payment_ref in transactions:
                # Create reputation score
                reputation_score = create_reputation_from_receipt_confirmation(
                    event, transactions[payment_ref]
                )
                reputation_system.add_reputation_score(reputation_score)
    
    return reputation_system.aggregated_reputation