"""
DOMP client for interacting with the protocol.
Handles relay connections, event publishing, and transaction management.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable, Set
import websockets
import aiohttp
from .events import Event, create_event_from_dict
from .crypto import KeyPair
from .validation import validate_event, ValidationError


class DOMPClient:
    """DOMP protocol client."""
    
    def __init__(self, keypair: KeyPair, relays: List[str] = None):
        self.keypair = keypair
        self.relays = relays or ["wss://relay.damus.io", "wss://nos.lol"]
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.event_handlers: List[Callable[[Event], None]] = []
        self.running = False
        
    async def connect(self) -> None:
        """Connect to all configured relays."""
        self.running = True
        tasks = []
        
        for relay_url in self.relays:
            task = asyncio.create_task(self._connect_relay(relay_url))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def disconnect(self) -> None:
        """Disconnect from all relays."""
        self.running = False
        tasks = []
        
        for ws in self.connections.values():
            if not ws.closed:
                task = asyncio.create_task(ws.close())
                tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        self.connections.clear()
    
    async def _connect_relay(self, relay_url: str) -> None:
        """Connect to a single relay."""
        try:
            ws = await websockets.connect(relay_url)
            self.connections[relay_url] = ws
            
            # Start listening for messages
            asyncio.create_task(self._listen_relay(relay_url, ws))
            
        except Exception as e:
            print(f"Failed to connect to {relay_url}: {e}")
    
    async def _listen_relay(self, relay_url: str, ws: websockets.WebSocketServerProtocol) -> None:
        """Listen for messages from a relay."""
        try:
            while self.running and not ws.closed:
                message = await ws.recv()
                await self._handle_relay_message(relay_url, message)
                
        except websockets.ConnectionClosed:
            print(f"Connection to {relay_url} closed")
        except Exception as e:
            print(f"Error listening to {relay_url}: {e}")
        finally:
            if relay_url in self.connections:
                del self.connections[relay_url]
    
    async def _handle_relay_message(self, relay_url: str, message: str) -> None:
        """Handle incoming relay message."""
        try:
            data = json.loads(message)
            msg_type = data[0]
            
            if msg_type == "EVENT":
                subscription_id = data[1]
                event_data = data[2]
                
                # Validate event
                try:
                    validate_event(event_data)
                    event = create_event_from_dict(event_data)
                    
                    # Call event handlers
                    for handler in self.event_handlers:
                        try:
                            handler(event)
                        except Exception as e:
                            print(f"Event handler error: {e}")
                            
                except ValidationError as e:
                    print(f"Invalid event received: {e}")
            
            elif msg_type == "EOSE":
                # End of stored events
                subscription_id = data[1]
                print(f"End of stored events for subscription {subscription_id}")
            
            elif msg_type == "OK":
                # Event publish response
                event_id = data[1]
                success = data[2]
                message = data[3] if len(data) > 3 else ""
                
                if success:
                    print(f"Event {event_id[:8]}... published successfully")
                else:
                    print(f"Event {event_id[:8]}... rejected: {message}")
                    
        except json.JSONDecodeError:
            print(f"Invalid JSON from {relay_url}: {message}")
        except Exception as e:
            print(f"Error handling message from {relay_url}: {e}")
    
    async def publish_event(self, event: Event) -> bool:
        """
        Publish an event to all connected relays.
        
        Args:
            event: Event to publish
            
        Returns:
            True if published to at least one relay
        """
        if not event.id or not event.sig:
            event.sign(self.keypair)
        
        # Validate before publishing
        try:
            validate_event(event.to_dict())
        except ValidationError as e:
            print(f"Cannot publish invalid event: {e}")
            return False
        
        event_message = json.dumps(["EVENT", event.to_dict()])
        success_count = 0
        
        for relay_url, ws in self.connections.items():
            try:
                if not ws.closed:
                    await ws.send(event_message)
                    success_count += 1
            except Exception as e:
                print(f"Failed to publish to {relay_url}: {e}")
        
        return success_count > 0
    
    async def subscribe(self, 
                       subscription_id: str,
                       filters: List[Dict[str, Any]],
                       relays: List[str] = None) -> None:
        """
        Subscribe to events matching filters.
        
        Args:
            subscription_id: Unique subscription identifier
            filters: List of filter objects
            relays: Specific relays to subscribe to (or all if None)
        """
        target_relays = relays or list(self.connections.keys())
        
        req_message = json.dumps(["REQ", subscription_id] + filters)
        
        for relay_url in target_relays:
            if relay_url in self.connections and not self.connections[relay_url].closed:
                try:
                    await self.connections[relay_url].send(req_message)
                    self.subscriptions[subscription_id] = {
                        "filters": filters,
                        "relays": target_relays
                    }
                except Exception as e:
                    print(f"Failed to subscribe to {relay_url}: {e}")
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        if subscription_id not in self.subscriptions:
            return
        
        close_message = json.dumps(["CLOSE", subscription_id])
        subscription = self.subscriptions[subscription_id]
        
        for relay_url in subscription["relays"]:
            if relay_url in self.connections and not self.connections[relay_url].closed:
                try:
                    await self.connections[relay_url].send(close_message)
                except Exception as e:
                    print(f"Failed to unsubscribe from {relay_url}: {e}")
        
        del self.subscriptions[subscription_id]
    
    def add_event_handler(self, handler: Callable[[Event], None]) -> None:
        """Add an event handler function."""
        self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[Event], None]) -> None:
        """Remove an event handler function."""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    async def get_events(self, 
                        filters: List[Dict[str, Any]], 
                        timeout: int = 10) -> List[Event]:
        """
        Get events matching filters (one-time query).
        
        Args:
            filters: List of filter objects
            timeout: Timeout in seconds
            
        Returns:
            List of matching events
        """
        events = []
        subscription_id = f"temp_{int(time.time())}"
        
        # Add temporary handler to collect events
        def collect_events(event: Event):
            events.append(event)
        
        self.add_event_handler(collect_events)
        
        try:
            await self.subscribe(subscription_id, filters)
            await asyncio.sleep(timeout)
            await self.unsubscribe(subscription_id)
        finally:
            self.remove_event_handler(collect_events)
        
        return events
    
    async def get_product_listings(self, 
                                  limit: int = 100,
                                  since: int = None) -> List[Event]:
        """Get recent product listings."""
        filters = [{"kinds": [300], "limit": limit}]
        if since:
            filters[0]["since"] = since
            
        return await self.get_events(filters)
    
    async def get_transaction_events(self, product_id: str) -> List[Event]:
        """Get all events related to a product transaction."""
        filters = [
            {"kinds": [300], "ids": [product_id]},  # Original listing
            {"kinds": [301, 303, 311, 313], "#ref": [product_id]},  # Related events
        ]
        
        events = await self.get_events(filters)
        
        # Sort by created_at timestamp
        events.sort(key=lambda e: e.created_at)
        
        return events
    
    async def get_user_events(self, pubkey: str, kinds: List[int] = None) -> List[Event]:
        """Get events by a specific user."""
        filters = [{"authors": [pubkey]}]
        if kinds:
            filters[0]["kinds"] = kinds
            
        return await self.get_events(filters)
    
    async def check_relay_info(self, relay_url: str) -> Optional[Dict[str, Any]]:
        """Get relay information document (NIP-11)."""
        try:
            # Convert ws:// to http://
            http_url = relay_url.replace("ws://", "http://").replace("wss://", "https://")
            
            async with aiohttp.ClientSession() as session:
                headers = {"Accept": "application/nostr+json"}
                async with session.get(http_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                        
        except Exception as e:
            print(f"Failed to get relay info for {relay_url}: {e}")
            
        return None


class TransactionManager:
    """Manages DOMP transaction state and workflows."""
    
    def __init__(self, client: DOMPClient):
        self.client = client
        self.transactions: Dict[str, Dict[str, Any]] = {}
        
        # Add event handler to track transactions
        self.client.add_event_handler(self._handle_transaction_event)
    
    def _handle_transaction_event(self, event: Event) -> None:
        """Handle events to track transaction state."""
        if event.kind in [300, 301, 303, 311, 313]:
            content = json.loads(event.content)
            
            if event.kind == 300:
                # New product listing
                self.transactions[event.id] = {
                    "product_id": event.id,
                    "state": "LISTED",
                    "events": [event],
                    "seller_pubkey": event.pubkey
                }
            
            elif event.kind == 301:
                # Bid submission
                product_id = content.get("product_ref")
                if product_id in self.transactions:
                    tx = self.transactions[product_id]
                    tx["state"] = "BID_RECEIVED"
                    tx["events"].append(event)
                    tx["buyer_pubkey"] = event.pubkey
            
            elif event.kind == 303:
                # Bid acceptance
                bid_ref = content.get("bid_ref")
                tx = self._find_transaction_by_bid(bid_ref)
                if tx:
                    tx["state"] = "BID_ACCEPTED"
                    tx["events"].append(event)
            
            elif event.kind == 311:
                # Payment confirmation
                bid_ref = content.get("bid_ref")
                tx = self._find_transaction_by_acceptance(bid_ref)
                if tx:
                    tx["state"] = "PAYMENT_CONFIRMED"
                    tx["events"].append(event)
            
            elif event.kind == 313:
                # Receipt confirmation
                payment_ref = content.get("payment_ref")
                tx = self._find_transaction_by_payment(payment_ref)
                if tx:
                    tx["state"] = "COMPLETED"
                    tx["events"].append(event)
    
    def _find_transaction_by_bid(self, bid_id: str) -> Optional[Dict[str, Any]]:
        """Find transaction that contains the given bid ID."""
        for tx in self.transactions.values():
            for event in tx["events"]:
                if event.id == bid_id and event.kind == 301:
                    return tx
        return None
    
    def _find_transaction_by_acceptance(self, acceptance_id: str) -> Optional[Dict[str, Any]]:
        """Find transaction that contains the given acceptance ID."""
        for tx in self.transactions.values():
            for event in tx["events"]:
                if event.id == acceptance_id and event.kind == 303:
                    return tx
        return None
    
    def _find_transaction_by_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Find transaction that contains the given payment ID."""
        for tx in self.transactions.values():
            for event in tx["events"]:
                if event.id == payment_id and event.kind == 311:
                    return tx
        return None
    
    def get_transaction_state(self, product_id: str) -> Optional[str]:
        """Get current state of a transaction."""
        tx = self.transactions.get(product_id)
        return tx["state"] if tx else None
    
    def get_user_transactions(self, pubkey: str, role: str = "any") -> List[Dict[str, Any]]:
        """
        Get transactions for a user.
        
        Args:
            pubkey: User's public key
            role: "seller", "buyer", or "any"
            
        Returns:
            List of transaction objects
        """
        results = []
        
        for tx in self.transactions.values():
            if role == "any":
                if (tx.get("seller_pubkey") == pubkey or 
                    tx.get("buyer_pubkey") == pubkey):
                    results.append(tx)
            elif role == "seller" and tx.get("seller_pubkey") == pubkey:
                results.append(tx)
            elif role == "buyer" and tx.get("buyer_pubkey") == pubkey:
                results.append(tx)
        
        return results