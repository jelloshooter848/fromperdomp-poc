# DOMP Live Two-Computer Testing Checklist

**Objective**: Demonstrate real P2P marketplace functionality between two computers  
**Time Required**: 20-30 minutes (15-20 min setup + 10 min testing)  
**What You'll Prove**: Cross-computer listings, bidding, Lightning invoices, and real-time sync

---

## 🖥️ Computer A (Primary - Already Setup)

### ✅ Quick Verification
- [ ] Navigate to project: `cd ~/projects/fromperdomp-poc/implementations/reference/python`
- [ ] Activate environment: `source domp-env/bin/activate`
- [ ] Start launcher: `python domp_launcher.py`
- [ ] Start all services: Choose option `3`
- [ ] Verify web interface: Open `http://localhost:8001`
- [ ] Note Computer A identity (top-right corner of web interface)

**Expected**: Services running, web interface loads, unique identity visible

---

## 💻 Computer B (Secondary - Fresh Install)

### 📦 Step 1: System Dependencies (2 minutes)
```bash
# Ubuntu/Debian/WSL:
sudo apt update && sudo apt install python3 python3-pip python3-venv git curl

# macOS:
brew install python3 git
```
- [ ] Python 3.8+ installed: `python3 --version`
- [ ] Git installed: `git --version`

### ⚡ Step 2: Install LND (3 minutes)
```bash
# Linux:
curl -L https://github.com/lightningnetwork/lnd/releases/download/v0.17.0-beta/lnd-linux-amd64-v0.17.0-beta.tar.gz | tar xzf -
sudo install lnd-linux-amd64-v0.17.0-beta/lnd /usr/local/bin/
sudo install lnd-linux-amd64-v0.17.0-beta/lncli /usr/local/bin/

# macOS:
brew install lnd
```
- [ ] LND installed: `lnd --version`
- [ ] LN CLI installed: `lncli --version`

### 📁 Step 3: Clone Repository (1 minute)
```bash
git clone <your-repo-url>
cd fromperdomp-poc/implementations/reference/python
```
- [ ] Repository cloned successfully
- [ ] In correct directory: `ls` shows `domp_launcher.py`

### 🐍 Step 4: Python Environment (8 minutes)
```bash
python3 -m venv domp-env
source domp-env/bin/activate
pip install -r requirements.txt
```
- [ ] Virtual environment created
- [ ] Environment activated (prompt shows `(domp-env)`)
- [ ] All dependencies installed (24 packages)

### ⚙️ Step 5: Configure LND (1 minute)
```bash
mkdir -p ~/.lnd
cat > ~/.lnd/lnd.conf << 'EOF'
[Application Options]
listen=localhost:9735
rpclisten=localhost:10009
restlisten=localhost:8002
maxpendingchannels=10

[Bitcoin]
bitcoin.active=1
bitcoin.testnet=1
bitcoin.node=neutrino

[Neutrino]
neutrino.connect=testnet1-btcd.zaphq.io
neutrino.connect=testnet2-btcd.zaphq.io
EOF
```
- [ ] LND config directory created
- [ ] Configuration file written

### 🚀 Step 6: Start DOMP Services (3 minutes)
```bash
python domp_launcher.py check-deps
python domp_launcher.py
```
- [ ] Dependencies check passed
- [ ] Launcher started
- [ ] Choose option `3` (Start All Services)
- [ ] LND starts successfully
- [ ] Web API starts successfully

### 🔐 Step 7: Create Wallet (2 minutes)
- [ ] In launcher menu, choose option `7` (Unlock Wallet)
- [ ] Create new wallet when prompted
- [ ] Enter secure password
- [ ] **SAVE SEED PHRASE SECURELY**
- [ ] Wallet unlocked successfully

### 🌐 Step 8: Verify Web Interface
- [ ] Open browser: `http://localhost:8001`
- [ ] Web interface loads
- [ ] Note Computer B identity (different from Computer A)

---

## 🧪 Cross-Computer Testing Scenarios

### Test 1: Service Verification ✅
**Time**: 1 minute

**Computer A**:
- [ ] Web interface loads at `http://localhost:8001`
- [ ] Identity shows in top-right

**Computer B**:
- [ ] Web interface loads at `http://localhost:8001`
- [ ] Identity different from Computer A

**Pass Criteria**: Both interfaces load with unique identities

---

### Test 2: Cross-Computer Listing Sync ✅
**Time**: 2 minutes

**Computer A (Seller)**:
- [ ] Create listing: "Two-Computer Test - 100 sats"
- [ ] Description: "Live test from Computer A"
- [ ] Submit listing
- [ ] Note listing ID from response

**Computer B (Buyer)**:
- [ ] Wait 10 seconds
- [ ] Refresh listings page
- [ ] **VERIFY**: See "Two-Computer Test" listing
- [ ] **VERIFY**: Shows Computer A as seller

**Pass Criteria**: Listing appears on Computer B within 30 seconds

---

### Test 3: Cross-Computer Bidding ✅
**Time**: 2 minutes

**Computer B (Buyer)**:
- [ ] Click on Computer A's listing
- [ ] Place bid: 100 sats
- [ ] Message: "Bid from Computer B"
- [ ] Submit bid

**Computer A (Seller)**:
- [ ] Check "Manage Bids" or refresh
- [ ] **VERIFY**: See pending bid from Computer B
- [ ] **VERIFY**: Bid message displays correctly

**Pass Criteria**: Bid appears on Computer A within 30 seconds

---

### Test 4: Lightning Invoice Generation ✅
**Time**: 2 minutes

**Computer A (Seller)**:
- [ ] Accept bid from Computer B
- [ ] **VERIFY**: Transaction created
- [ ] **VERIFY**: Status shows "awaiting_payment"
- [ ] **VERIFY**: Lightning invoice generated (starts with "lntb")
- [ ] Copy payment request

**Computer B (Buyer)**:
- [ ] Check "My Transactions"
- [ ] **VERIFY**: See transaction with "awaiting_payment"
- [ ] **VERIFY**: Lightning invoice displayed
- [ ] **VERIFY**: Payment hash visible

**Pass Criteria**: Real Lightning invoice generated on both computers

---

### Test 5: Real-Time WebSocket Updates ✅
**Time**: 2 minutes

**Setup**: Open both browsers side-by-side

**Computer A**:
- [ ] Create second listing: "WebSocket Test - 50 sats"

**Computer B**:
- [ ] **VERIFY**: New listing appears WITHOUT refresh
- [ ] **VERIFY**: Update happens within 5 seconds

**Computer B**:
- [ ] Place bid on new listing

**Computer A**:
- [ ] **VERIFY**: Bid notification appears WITHOUT refresh
- [ ] **VERIFY**: Update happens within 5 seconds

**Pass Criteria**: Real-time updates work in both directions

---

### Test 6: Payment Status Sync ✅
**Time**: 1 minute

**Both Computers**:
- [ ] Monitor same transaction
- [ ] **VERIFY**: Both show identical status
- [ ] **VERIFY**: Status changes sync between computers

**Pass Criteria**: Transaction status identical on both computers

---

## 🚨 Troubleshooting Quick Reference

### Service Issues
```bash
# Check if ports are free:
netstat -tulpn | grep -E "(8001|10009)"

# Restart services:
# In launcher: 6. Stop All Services → 3. Start All Services

# Check service status:
curl http://localhost:8001/api/identity
```

### Common Installation Fixes
```bash
# If secp256k1 fails:
sudo apt install libsecp256k1-dev  # Linux
brew install libsecp256k1          # macOS

# If cryptography fails:
sudo apt install build-essential libssl-dev libffi-dev
```

### LND Issues
```bash
# Check LND is running:
ps aux | grep lnd

# Check LND logs:
tail -f ~/.lnd/logs/bitcoin/testnet/lnd.log

# Restart LND:
# In launcher: 4. Stop LND → 1. Start LND → 7. Unlock Wallet
```

---

## ✅ Success Criteria

### Minimum Success (Proves P2P Communication):
- [ ] Computer B setup completed without errors
- [ ] Both web interfaces accessible on port 8001
- [ ] Listings sync between computers (within 30 seconds)
- [ ] Bids placed on one computer appear on other
- [ ] Lightning invoices generate on both computers

### Full Success (Production Ready):
- [ ] All tests complete within time estimates
- [ ] Real-time WebSocket updates working
- [ ] No errors in browser console
- [ ] Multiple transactions work smoothly
- [ ] Status synchronization instant across computers

---

## 🎯 Expected Timeline

| Phase | Time | Description |
|-------|------|-------------|
| Computer B Setup | 15-20 min | Dependencies + LND + Python + Config |
| Service Verification | 2 min | Both computers running |
| Cross-Computer Tests | 10 min | All 6 test scenarios |
| **Total** | **30 min** | Complete P2P demonstration |

---

## 🎉 Success Indicators

**You've successfully demonstrated DOMP when**:
- ✅ Two independent computers running DOMP
- ✅ Real-time marketplace synchronization via Nostr
- ✅ Cross-computer bidding and acceptance
- ✅ Real Lightning Network invoice generation
- ✅ WebSocket real-time updates working
- ✅ Decentralized P2P marketplace fully operational

**This proves**: DOMP works as a true peer-to-peer marketplace with no central server dependency!