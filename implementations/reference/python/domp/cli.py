"""
Command-line interface for DOMP protocol.
Provides tools for creating, validating, and publishing events.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Optional, List

import click
from .crypto import KeyPair, generate_pow_nonce, sign_event
from .events import ProductListing, BidSubmission, BidAcceptance, PaymentConfirmation, ReceiptConfirmation
from .client import DOMPClient, TransactionManager
from .validation import validate_event, validate_event_chain, ValidationError


@click.group()
@click.version_option()
def main():
    """DOMP Protocol CLI - Decentralized Online Marketplace Protocol tools."""
    pass


@main.group()
def keys():
    """Key management commands."""
    pass


@keys.command()
@click.option('--output', '-o', help='Output file for private key')
def generate(output: Optional[str]):
    """Generate a new keypair."""
    keypair = KeyPair()
    
    click.echo(f"Public key:  {keypair.public_key_hex}")
    click.echo(f"Private key: {keypair.private_key_hex}")
    
    if output:
        with open(output, 'w') as f:
            f.write(keypair.private_key_hex)
        click.echo(f"Private key saved to {output}")


@keys.command()
@click.argument('private_key_file')
def show(private_key_file: str):
    """Show public key from private key file."""
    try:
        with open(private_key_file) as f:
            private_key_hex = f.read().strip()
        
        keypair = KeyPair.from_hex(private_key_hex)
        click.echo(f"Public key: {keypair.public_key_hex}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def event():
    """Event creation and validation commands."""
    pass


@event.command()
@click.option('--key-file', '-k', required=True, help='Private key file')
@click.option('--product-name', '-n', required=True, help='Product name')
@click.option('--description', '-d', required=True, help='Product description')
@click.option('--price', '-p', required=True, type=int, help='Price in satoshis')
@click.option('--category', '-c', help='Product category')
@click.option('--pow-difficulty', type=int, default=20, help='PoW difficulty for anti-spam')
@click.option('--output', '-o', help='Output file for event JSON')
def create_listing(key_file: str, product_name: str, description: str, price: int, 
                  category: Optional[str], pow_difficulty: int, output: Optional[str]):
    """Create a product listing event."""
    try:
        # Load keypair
        with open(key_file) as f:
            private_key_hex = f.read().strip()
        keypair = KeyPair.from_hex(private_key_hex)
        
        # Create event
        event = ProductListing(
            product_name=product_name,
            description=description,
            price_satoshis=price,
            category=category or "",
            listing_id=f"listing-{int(time.time())}"
        )
        
        # Generate PoW
        click.echo(f"Generating proof-of-work (difficulty {pow_difficulty})...")
        event_data = event.to_dict()
        event_data.pop('id', None)
        event_data.pop('sig', None)
        
        event_id, nonce = generate_pow_nonce(event_data, pow_difficulty)
        
        # Reconstruct the complete event with PoW proof included
        event_data["tags"] = event_data["tags"] + [["anti_spam_proof", "pow", nonce, str(pow_difficulty)]]
        event_data["pubkey"] = keypair.public_key_hex
        event_data["id"] = event_id
        event_data["sig"] = sign_event(event_data, keypair)
        
        # Output the computed event_data directly (don't use event.to_dict())
        event_json = json.dumps(event_data, indent=2)
        
        if output:
            with open(output, 'w') as f:
                f.write(event_json)
            click.echo(f"Event saved to {output}")
        else:
            click.echo(event_json)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@event.command()
@click.argument('event_file')
def validate(event_file: str):
    """Validate an event file."""
    try:
        with open(event_file) as f:
            event_data = json.load(f)
        
        validate_event(event_data)
        click.echo("✓ Event is valid")
        
    except ValidationError as e:
        click.echo(f"✗ Event is invalid: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@event.command()
@click.argument('events_file')
def validate_chain(events_file: str):
    """Validate a transaction event chain."""
    try:
        with open(events_file) as f:
            events_data = json.load(f)
        
        if not isinstance(events_data, list):
            raise ValueError("Events file must contain an array of events")
        
        validate_event_chain(events_data)
        click.echo("✓ Event chain is valid")
        
    except ValidationError as e:
        click.echo(f"✗ Event chain is invalid: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def client():
    """Client commands for interacting with relays."""
    pass


@client.command()
@click.option('--key-file', '-k', required=True, help='Private key file')
@click.option('--relays', '-r', multiple=True, help='Relay URLs')
@click.option('--limit', '-l', type=int, default=10, help='Number of listings to show')
def list_products(key_file: str, relays: List[str], limit: int):
    """List recent product listings."""
    async def run():
        try:
            # Load keypair
            with open(key_file) as f:
                private_key_hex = f.read().strip()
            keypair = KeyPair.from_hex(private_key_hex)
            
            # Create client
            relay_list = list(relays) if relays else None
            client = DOMPClient(keypair, relay_list)
            
            # Connect and get listings
            await client.connect()
            events = await client.get_product_listings(limit=limit)
            await client.disconnect()
            
            # Display results
            if not events:
                click.echo("No product listings found")
                return
            
            click.echo(f"Found {len(events)} product listings:")
            click.echo()
            
            for event in events:
                content = json.loads(event.content)
                click.echo(f"ID: {event.id[:16]}...")
                click.echo(f"Product: {content.get('product_name', 'Unknown')}")
                click.echo(f"Price: {content.get('price_satoshis', 0):,} sats")
                click.echo(f"Seller: {event.pubkey[:16]}...")
                click.echo(f"Time: {time.ctime(event.created_at)}")
                click.echo("─" * 50)
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())


@client.command()
@click.option('--key-file', '-k', required=True, help='Private key file')
@click.option('--relays', '-r', multiple=True, help='Relay URLs') 
@click.argument('event_file')
def publish(key_file: str, relays: List[str], event_file: str):
    """Publish an event to relays."""
    async def run():
        try:
            # Load keypair
            with open(key_file) as f:
                private_key_hex = f.read().strip()
            keypair = KeyPair.from_hex(private_key_hex)
            
            # Load event
            with open(event_file) as f:
                event_data = json.load(f)
            
            # Validate event
            validate_event(event_data)
            
            # Create client and publish
            relay_list = list(relays) if relays else None
            client = DOMPClient(keypair, relay_list)
            
            await client.connect()
            
            from .events import create_event_from_dict
            event = create_event_from_dict(event_data)
            
            success = await client.publish_event(event)
            await client.disconnect()
            
            if success:
                click.echo(f"✓ Event published: {event.id}")
            else:
                click.echo("✗ Failed to publish event", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())


@client.command()
@click.option('--key-file', '-k', required=True, help='Private key file')
@click.option('--relays', '-r', multiple=True, help='Relay URLs')
@click.argument('product_id')
def track_transaction(key_file: str, relays: List[str], product_id: str):
    """Track a transaction by product ID."""
    async def run():
        try:
            # Load keypair
            with open(key_file) as f:
                private_key_hex = f.read().strip()
            keypair = KeyPair.from_hex(private_key_hex)
            
            # Create client
            relay_list = list(relays) if relays else None
            client = DOMPClient(keypair, relay_list)
            
            await client.connect()
            events = await client.get_transaction_events(product_id)
            await client.disconnect()
            
            if not events:
                click.echo(f"No events found for product {product_id}")
                return
            
            click.echo(f"Transaction timeline for {product_id}:")
            click.echo()
            
            states = {
                300: "LISTED",
                301: "BID_RECEIVED", 
                303: "BID_ACCEPTED",
                311: "PAYMENT_CONFIRMED",
                313: "COMPLETED"
            }
            
            for event in events:
                state = states.get(event.kind, "UNKNOWN")
                timestamp = time.ctime(event.created_at)
                click.echo(f"{timestamp} - {state} (kind-{event.kind})")
                
                if event.kind == 300:
                    content = json.loads(event.content)
                    click.echo(f"  Product: {content.get('product_name')}")
                    click.echo(f"  Price: {content.get('price_satoshis'):,} sats")
                
                elif event.kind == 313:
                    content = json.loads(event.content)
                    click.echo(f"  Status: {content.get('status')}")
                    if content.get('rating'):
                        click.echo(f"  Rating: {content.get('rating')}/5")
                
                click.echo()
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())


@main.group()
def pow():
    """Proof-of-work utilities."""
    pass


@pow.command()
@click.argument('event_file')
@click.option('--difficulty', '-d', type=int, default=20, help='PoW difficulty')
@click.option('--output', '-o', help='Output file for modified event')
def generate(event_file: str, difficulty: int, output: Optional[str]):
    """Generate proof-of-work for an event."""
    try:
        with open(event_file) as f:
            event_data = json.load(f)
        
        # Remove existing PoW proof and signature
        event_data.pop('id', None)
        event_data.pop('sig', None)
        
        # Remove existing anti_spam_proof tags
        event_data['tags'] = [tag for tag in event_data['tags'] 
                             if not (len(tag) > 0 and tag[0] == 'anti_spam_proof')]
        
        click.echo(f"Generating proof-of-work (difficulty {difficulty})...")
        
        event_id, nonce = generate_pow_nonce(event_data, difficulty)
        
        # Add PoW proof
        event_data['tags'].append(['anti_spam_proof', 'pow', nonce, str(difficulty)])
        event_data['id'] = event_id
        
        # Output
        event_json = json.dumps(event_data, indent=2)
        
        if output:
            with open(output, 'w') as f:
                f.write(event_json)
            click.echo(f"Event with PoW saved to {output}")
        else:
            click.echo(event_json)
            
        click.echo(f"✓ PoW generated: {nonce} (ID: {event_id[:16]}...)")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
def relay_info():
    """Show information about common DOMP relays."""
    click.echo("Common DOMP-compatible relays:")
    click.echo()
    
    relays = [
        ("wss://relay.damus.io", "General Nostr relay"),
        ("wss://nos.lol", "General Nostr relay"),
        ("wss://relay.snort.social", "General Nostr relay"),
        ("wss://relay.primal.net", "General Nostr relay"),
    ]
    
    for url, description in relays:
        click.echo(f"{url}")
        click.echo(f"  {description}")
        click.echo()


if __name__ == '__main__':
    main()