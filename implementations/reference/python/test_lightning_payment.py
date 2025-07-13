#!/usr/bin/env python3
"""
Test Lightning payment functionality.
Tests both invoice creation and payment.
"""

import asyncio
import requests
import json
import sys
import time

API_BASE = "http://localhost:8001"


def test_lightning_invoice_and_payment():
    """Test creating and paying Lightning invoices."""
    print("⚡ Testing Lightning Invoice Creation & Payment")
    print("=" * 50)
    
    try:
        # Step 1: Create a Lightning invoice
        print("📝 Step 1: Creating Lightning invoice...")
        invoice_request = {
            "amount_sats": 1000,
            "description": "DOMP Lightning Payment Test"
        }
        
        response = requests.post(
            f"{API_BASE}/api/invoices",
            headers={"Content-Type": "application/json"},
            data=json.dumps(invoice_request)
        )
        
        if response.status_code != 200:
            print(f"❌ Invoice creation failed: {response.status_code} - {response.text}")
            return False
        
        invoice_data = response.json()
        print(f"✅ Invoice created successfully!")
        print(f"   Client type: {invoice_data['client_type']}")
        print(f"   Amount: {invoice_data['amount_sats']} sats")
        print(f"   Payment request: {invoice_data['payment_request'][:60]}...")
        
        if invoice_data['client_type'] == 'real_lnd':
            print(f"   Payment hash: {invoice_data['payment_hash'][:16]}...")
        
        # Step 2: Pay the Lightning invoice
        print(f"\n💸 Step 2: Paying Lightning invoice...")
        payment_request = {
            "invoice": invoice_data["payment_request"]
        }
        
        response = requests.post(
            f"{API_BASE}/api/payments",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payment_request)
        )
        
        if response.status_code != 200:
            print(f"❌ Payment failed: {response.status_code} - {response.text}")
            return False
        
        payment_data = response.json()
        print(f"✅ Payment completed successfully!")
        print(f"   Client type: {payment_data['client_type']}")
        print(f"   Status: {payment_data['status']}")
        print(f"   Payment hash: {payment_data['payment_hash'][:16]}...")
        print(f"   Fee: {payment_data['fee_sat']} sats")
        
        if payment_data['client_type'] == 'real_lnd':
            print(f"   Payment preimage: {payment_data['payment_preimage'][:16]}...")
            if payment_data.get('payment_error'):
                print(f"   Payment error: {payment_data['payment_error']}")
        
        # Step 3: Verify payment was successful
        if payment_data['status'] == 'SUCCEEDED':
            print("\n🎉 Lightning payment flow completed successfully!")
            return True
        else:
            print(f"\n⚠️  Payment completed but status is: {payment_data['status']}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web server - make sure it's running on port 8001")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run Lightning payment test."""
    print("🧪 DOMP Lightning Payment Integration Test")
    print("=" * 50)
    
    success = test_lightning_invoice_and_payment()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Lightning payment test PASSED")
        print("✅ Ready for DOMP transaction integration")
    else:
        print("❌ Lightning payment test FAILED")
        print("⚠️  Check server logs for details")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)