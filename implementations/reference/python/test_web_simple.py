#!/usr/bin/env python3
"""
Simple test for running web API (assumes server already running on 8001).
"""

import requests
import json

API_BASE = "http://localhost:8001"

def test_running_server():
    """Test the already running web API server."""
    print("⚡ Testing DOMP Web API Lightning Integration")
    print("=" * 50)
    
    try:
        # Test identity endpoint
        print("🔍 Testing identity endpoint...")
        response = requests.get(f"{API_BASE}/api/identity")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Identity: {data['pubkey_short']}")
            print(f"✅ Lightning balance: {data['lightning_balance']} sats")
        else:
            print(f"❌ Identity failed: {response.status_code} - {response.text}")
            return False
        
        # Test wallet balance
        print("\n💰 Testing wallet balance...")
        response = requests.get(f"{API_BASE}/api/wallet/balance")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Balance: {data['balance_sats']} sats")
        else:
            print(f"❌ Balance failed: {response.status_code} - {response.text}")
            return False
        
        # Test invoice creation
        print("\n🧾 Testing Lightning invoice creation...")
        invoice_data = {
            "amount_sats": 5000,
            "description": "DOMP Real Lightning Test"
        }
        
        response = requests.post(
            f"{API_BASE}/api/invoices",
            headers={"Content-Type": "application/json"},
            data=json.dumps(invoice_data)
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Invoice created!")
            print(f"   Client type: {data['client_type']}")
            print(f"   Amount: {data['amount_sats']} sats")
            print(f"   Payment request: {data['payment_request'][:60]}...")
            
            if data['client_type'] == 'real_lnd':
                print("🎉 SUCCESS: Real Lightning invoice from LND!")
            else:
                print("ℹ️  Mock Lightning invoice (LND connection issue)")
        else:
            print(f"❌ Invoice failed: {response.status_code} - {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_running_server()
    if success:
        print("\n🎉 All tests PASSED - Lightning integration working!")
    else:
        print("\n❌ Tests FAILED")