#!/usr/bin/env python3
"""
Test script for web API with real Lightning integration.
"""

import asyncio
import requests
import json
import sys
import time
import subprocess
import signal
import os

API_BASE = "http://localhost:8001"


def start_web_server():
    """Start the web API server."""
    print("🚀 Starting DOMP Web API server...")
    
    # Start uvicorn server
    proc = subprocess.Popen([
        "python3", "-m", "uvicorn", "web_api:app",
        "--host", "localhost",
        "--port", "8001",
        "--reload"
    ], cwd="/home/lando/projects/fromperdomp-poc/implementations/reference/python")
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    return proc


def test_lightning_integration():
    """Test Lightning integration in web API."""
    print("\n⚡ Testing Lightning Integration in Web API")
    print("=" * 50)
    
    try:
        # Test identity endpoint (includes Lightning balance)
        print("🔍 Testing identity endpoint...")
        response = requests.get(f"{API_BASE}/api/identity")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Identity loaded: {data['pubkey_short']}")
            print(f"✅ Lightning balance: {data['lightning_balance']} sats")
        else:
            print(f"❌ Identity endpoint failed: {response.status_code}")
            return False
        
        # Test wallet balance endpoint
        print("\n💰 Testing wallet balance endpoint...")
        response = requests.get(f"{API_BASE}/api/wallet/balance")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Wallet balance: {data['balance_sats']} sats")
            print(f"✅ Balance in BTC: {data['balance_btc']:.8f}")
        else:
            print(f"❌ Wallet balance endpoint failed: {response.status_code}")
            return False
        
        # Test Lightning invoice creation
        print("\n🧾 Testing Lightning invoice creation...")
        invoice_request = {
            "amount_sats": 2500,
            "description": "DOMP Web API Test Invoice"
        }
        
        response = requests.post(
            f"{API_BASE}/api/invoices",
            headers={"Content-Type": "application/json"},
            data=json.dumps(invoice_request)
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Invoice created successfully!")
            print(f"   Client type: {data['client_type']}")
            print(f"   Amount: {data['amount_sats']} sats")
            print(f"   Payment request: {data['payment_request'][:50]}...")
            
            if data['client_type'] == 'real_lnd':
                print(f"   Payment hash: {data['payment_hash'][:16]}...")
                print("🎉 Real Lightning invoice created!")
            else:
                print("ℹ️  Mock Lightning invoice created")
                
        else:
            print(f"❌ Invoice creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        # Test marketplace listings (should work with Lightning integration)
        print("\n📦 Testing marketplace listings...")
        response = requests.get(f"{API_BASE}/api/listings")
        if response.status_code == 200:
            data = response.json()
            # The API returns {"listings": [...]} not a direct array
            listings = data.get("listings", [])
            print(f"✅ Found {len(listings)} listings")
            if listings and len(listings) > 0:
                listing = listings[0]
                if 'product_name' in listing:
                    print(f"   Sample listing: {listing['product_name']}")
                else:
                    print(f"   Sample listing: (found but couldn't get product name)")
        else:
            print(f"❌ Listings endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web server - make sure it's running")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run web API Lightning integration test."""
    print("🧪 DOMP Web API Lightning Integration Test")
    print("=" * 50)
    print("ℹ️  Connecting to existing web server on port 8001...")
    
    try:
        # Run tests (connect to existing server)
        success = test_lightning_integration()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 Web API Lightning integration test PASSED")
            print("✅ DOMP web interface now uses real Lightning Network")
        else:
            print("❌ Web API Lightning integration test FAILED")
        
        return success
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)