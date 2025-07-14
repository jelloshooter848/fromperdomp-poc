# DOMP Quick Setup Guide

Get the DOMP P2P marketplace running on any computer in under 10 minutes!

## 🚀 New Computer Setup (One Command)

If you're setting up DOMP on a fresh computer:

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/fromperdomp-poc.git
cd fromperdomp-poc/implementations/reference/python

# 2. Setup Python environment  
python -m venv domp-env
source domp-env/bin/activate  # On Windows: domp-env\Scripts\activate
pip install -r requirements.txt

# 3. Check what needs to be installed
python domp_launcher.py check-deps

# 4. Complete automated setup (if dependencies are installed)
python domp_launcher.py setup
```

## 📦 What's Included vs What to Install

### ✅ Included in Repository
- Complete DOMP marketplace implementation
- Python dependencies (installed via `pip install -r requirements.txt`)
- Nostr client and protocol implementation
- Lightning Network integration code
- Web interface and API
- Service launcher and management tools
- Comprehensive test suite

### 📥 Needs Separate Installation
- **LND (Lightning Network Daemon)** - The actual Lightning node software
- **Python 3.8+** - Programming language runtime
- **Git** - Version control (for cloning)

**Note**: LND is a separate project (~50MB) that provides Lightning Network functionality. DOMP integrates with it but doesn't include it to keep the repository lightweight.

## Prerequisites

1. **Python 3.8+** installed
2. **LND (Lightning Network Daemon)** - automatically checked and instructions provided
3. **Git** for cloning the repository

### Install LND

```bash
# On Ubuntu/Debian
curl -L https://github.com/lightningnetwork/lnd/releases/download/v0.17.0-beta/lnd-linux-amd64-v0.17.0-beta.tar.gz | tar xzf -
sudo install lnd-linux-amd64-v0.17.0-beta/lnd /usr/local/bin/
sudo install lnd-linux-amd64-v0.17.0-beta/lncli /usr/local/bin/

# On macOS  
brew install lnd

# Verify installation
lnd --version
lncli --version
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/domp-protocol/domp
cd domp/implementations/reference/python
```

### 2. Setup Environment

```bash
# Create virtual environment
python -m venv domp-env
source domp-env/bin/activate  # On Windows: domp-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure LND

Create LND configuration file:

```bash
# Create LND directory
mkdir -p ~/.lnd

# Create basic configuration
cat > ~/.lnd/lnd.conf << EOF
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

## Quick Start

### 1. Start DOMP Launcher

```bash
python domp_launcher.py
```

### 2. Start All Services

In the launcher menu, select **option 3**: "Start All Services"

This will:
- ✅ Start LND Lightning Network Daemon
- ✅ Start DOMP Web API server  
- ✅ Show real-time status updates

### 3. Unlock Wallet

Select **option 7**: "Unlock Wallet"

- If this is your first time, LND will prompt you to create a new wallet
- Enter a secure password when prompted
- **Save your seed phrase securely!**

### 4. Verify Everything Works

Select **option 9**: "Run Tests"

You should see:
```
🎯 FINAL VERDICT:
  🎉 ALL TESTS PASSED! DOMP system is fully functional!
  ✅ Ready for production deployment
  🚀 No regressions detected
```

### 5. Access Web Interface

Open your browser to: **http://localhost:8001**

You'll see the DOMP marketplace with:
- Sample product listings
- Real Lightning integration
- Interactive bid/purchase flow

## First Wallet Setup

If this is your first time running LND:

### 1. Create Wallet

When you first unlock the wallet, LND will prompt:

```
Input wallet password: [enter secure password]
Confirm password: [confirm password]

Do you have an existing cipher seed mnemonic or extended master root key you want to use?
Enter 'y' to use an existing cipher seed mnemonic, 'x' to use an extended master root key 
or 'n' to create a new seed (Enter y/x/n):
```

Choose **'n'** to create a new seed.

### 2. Save Seed Phrase

LND will display a 24-word seed phrase:

```
!!!YOU MUST WRITE DOWN THIS SEED TO BE ABLE TO RESTORE THE WALLET!!!

1. abandon   2. ability   3. able      4. about     
5. above     6. absent    7. absorb    8. abstract  
[... continue writing down all 24 words ...]

!!!YOU MUST WRITE DOWN THIS SEED TO BE ABLE TO RESTORE THE WALLET!!!
```

**⚠️ Critical**: Write down these words in order and store them securely!

### 3. Verify Seed

Re-enter some words to verify you wrote them down correctly.

## Command Line Quick Start

For automation or scripting:

```bash
# Start all services
python domp_launcher.py start

# Check status  
python domp_launcher.py status

# Unlock wallet (interactive)
python domp_launcher.py unlock

# Run tests
python domp_launcher.py test

# Stop all services
python domp_launcher.py stop
```

## Verification Checklist

✅ **LND Running**: `lncli --network=testnet getinfo` works  
✅ **Wallet Unlocked**: Shows node info instead of "wallet locked"  
✅ **Web API Running**: http://localhost:8001 loads  
✅ **Tests Passing**: All 11 tests show ✅ PASS  
✅ **Lightning Balance**: Shows balance (even if 0 sats)  

## Troubleshooting

### LND Won't Start

```bash
# Check if already running
ps aux | grep lnd

# Check logs
tail -f ~/.lnd/logs/bitcoin/testnet/lnd.log

# Kill existing process
pkill lnd
```

### Port Conflicts

```bash
# Check what's using ports
netstat -tlnp | grep :10009  # LND gRPC
netstat -tlnp | grep :8001   # Web API

# Kill conflicting processes
sudo kill <PID>
```

### Wallet Issues

```bash
# Manual wallet unlock
lncli --network=testnet unlock

# Check wallet status
lncli --network=testnet getinfo

# Reset wallet (⚠️ will lose funds!)
rm -rf ~/.lnd/data/chain/bitcoin/testnet/wallet.db
```

### Test Failures

```bash
# Run individual tests to isolate issues
python test_lightning_client.py
python test_complete_domp_flow.py

# Check service status
python domp_launcher.py status
```

## Getting Help

- **Launcher Help**: Select option 12 in the interactive menu
- **Documentation**: See [LAUNCHER.md](LAUNCHER.md) for detailed documentation
- **LND Help**: https://docs.lightning.engineering/
- **Issues**: Check service logs with launcher option 10

## Next Steps

Once everything is running:

1. **Explore Web Interface**: Browse sample listings at http://localhost:8001
2. **Try Marketplace Flow**: Place bids, see Lightning invoices generated
3. **Development**: Modify code and re-run tests to verify changes
4. **Lightning Testnet**: Get testnet coins to try real payments
5. **Production**: Consider mainnet deployment for real marketplace

## Security Reminders

- **Testnet Only**: This setup uses Bitcoin testnet (no real money)
- **Save Seed Phrase**: Required to recover your Lightning wallet
- **Secure Password**: Use a strong wallet password
- **Local Only**: Services bind to localhost (not accessible remotely)

You're now ready to develop with the DOMP Lightning marketplace! 🚀