(domp-env) lando@jellynose:~/projects/fromperdomp-poc/implementations/reference/python$ python3 test_real_lightning.py
🧪 DOMP Real Lightning Integration Test
==================================================
⚡ Testing Real Lightning Network Operations
==================================================
🔗 Connecting to LND...
✅ Connected to LND at localhost:10009

📊 Getting node information...
✅ Node ID: 03ef9bd9383bd3db...
✅ Alias: 03ef9bd9383bd3dbdeb2
✅ Network: testnet
✅ Synced to chain: True
✅ Block height: 4551852

💰 Getting wallet balance...
✅ Wallet balance: 0 sats

🧾 Creating test invoice...
✅ Created invoice:
   Payment request: lntb10u1p58gtuwpp5sd3jrce0vczstau6xv0yczg38cq456dx...
   Payment hash: 836321e32f660505...
   Amount: 1000 sats

🎉 All Lightning operations successful!
✅ Real Lightning integration working

🔌 Disconnected from LND

==================================================
🎉 Lightning integration test PASSED
✅ Ready to implement DOMP escrow with real Lightning