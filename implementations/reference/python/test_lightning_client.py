#!/usr/bin/env python3
"""
Test script for the new Lightning client structure.
Tests both mock and real Lightning clients.
"""

import asyncio
import sys
sys.path.insert(0, '/home/lando/projects/fromperdomp-poc/implementations/reference/python')

from domp.lightning import LightningClientFactory, RealLightningClient, MockLightningNode


async def test_mock_client():
    """Test mock Lightning client functionality."""
    print("🧪 Testing Mock Lightning Client")
    print("-" * 40)
    
    # Create mock client using factory
    client = LightningClientFactory.create_client(use_real=False, node_id="test_mock")
    
    # Test mock functionality
    try:
        # Test invoice creation
        invoice = client.create_invoice(
            amount_sats=100000,
            description="Test DOMP transaction"
        )
        print(f"✅ Created mock invoice: {invoice[:30]}...")
        
        # Test balance
        balance = client.get_balance()
        print(f"✅ Mock balance: {balance:,} sats")
        
        # Test payment (to self for testing)
        payment_hash = client.pay_invoice(invoice, client)
        print(f"✅ Mock payment hash: {payment_hash[:16]}...")
        
        # Test payment status
        status = client.get_payment_status(payment_hash)
        print(f"✅ Payment status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock client test failed: {e}")
        return False


async def test_real_client_structure():
    """Test real Lightning client structure (without actual node)."""
    print("\n🔌 Testing Real Lightning Client Structure")
    print("-" * 40)
    
    try:
        # Create real client using factory
        client = LightningClientFactory.create_client(
            use_real=True,
            node_type="lnd",
            grpc_host="localhost",
            grpc_port=10009
        )
        
        print(f"✅ Created RealLightningClient instance")
        print(f"   Node type: {client.node_type}")
        print(f"   gRPC address: {client.grpc_host}:{client.grpc_port}")
        print(f"   TLS cert path: {client.tls_cert_path}")
        print(f"   Macaroon path: {client.macaroon_path}")
        
        # Test connection attempt (will fail without actual LND, but structure should work)
        print("\n🔗 Testing connection (expected to fail without real LND)...")
        connected = await client.connect()
        if not connected:
            print("ℹ️  Connection failed as expected (no real LND node)")
        
        # Test client methods that require connection (will raise RuntimeError)
        try:
            await client.get_info()
            print("❌ Unexpected: get_info() should fail without connection")
        except RuntimeError as e:
            print(f"✅ Correctly raises RuntimeError: {e}")
        
        # Test disconnection
        await client.disconnect()
        print("✅ Disconnect completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Real client structure test failed: {e}")
        return False


async def test_factory_pattern():
    """Test the Lightning client factory pattern."""
    print("\n🏭 Testing Lightning Client Factory")
    print("-" * 40)
    
    try:
        # Test mock creation
        mock_client = LightningClientFactory.create_client(use_real=False)
        assert isinstance(mock_client, MockLightningNode)
        print("✅ Factory creates MockLightningNode when use_real=False")
        
        # Test real creation
        real_client = LightningClientFactory.create_client(use_real=True)
        assert isinstance(real_client, RealLightningClient)
        print("✅ Factory creates RealLightningClient when use_real=True")
        
        # Test parameter passing
        real_client_custom = LightningClientFactory.create_client(
            use_real=True,
            grpc_host="192.168.1.100",
            grpc_port=9735
        )
        assert real_client_custom.grpc_host == "192.168.1.100"
        assert real_client_custom.grpc_port == 9735
        print("✅ Factory correctly passes parameters to clients")
        
        return True
        
    except Exception as e:
        print(f"❌ Factory pattern test failed: {e}")
        return False


async def main():
    """Run all Lightning client tests."""
    print("⚡ DOMP Lightning Client Structure Test")
    print("=" * 50)
    
    tests = [
        ("Mock Client", test_mock_client),
        ("Real Client Structure", test_real_client_structure), 
        ("Factory Pattern", test_factory_pattern)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All Lightning client structure tests passed!")
        print("✅ Ready for next step: LND node setup")
    else:
        print("⚠️  Some tests failed - check implementation")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)