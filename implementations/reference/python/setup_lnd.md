# LND Setup Guide for DOMP Development

This guide helps you set up a Lightning Network Daemon (LND) node for DOMP development and testing.

## Quick Setup (Recommended)

### 1. Install LND

#### Option A: Download Binary (Easiest)
```bash
# Download LND v0.17.0 (adjust version as needed)
cd /tmp
wget https://github.com/lightningnetwork/lnd/releases/download/v0.17.0-beta/lnd-linux-amd64-v0.17.0-beta.tar.gz

# Extract
tar -xzf lnd-linux-amd64-v0.17.0-beta.tar.gz

# Move to system path
sudo mv lnd-linux-amd64-v0.17.0-beta/lnd /usr/local/bin/
sudo mv lnd-linux-amd64-v0.17.0-beta/lncli /usr/local/bin/

# Verify installation
lnd --version
lncli --version
```

#### Option B: Using Go (if you have Go installed)
```bash
go install github.com/lightningnetwork/lnd@latest
```

### 2. Create LND Configuration

```bash
# Create LND directory
mkdir -p ~/.lnd

# Create configuration file
cat > ~/.lnd/lnd.conf << EOF
[Application Options]
# Allow localhost connections
rpclisten=localhost:10009
restlisten=localhost:8080

# Debugging
debuglevel=info

[Bitcoin]
bitcoin.active=1
bitcoin.testnet=1
bitcoin.node=neutrino

[Neutrino]
neutrino.connect=testnet1-btcd.zaphq.io
neutrino.connect=testnet2-btcd.zaphq.io

[Protocol Options]
protocol.wumbo-channels=1
EOF
```

### 3. Start LND Node

```bash
# Start LND (run in separate terminal or use screen/tmux)
lnd

# The node will start and show logs
# Look for: "Waiting for wallet encryption password. Use `lncli create` to create a wallet"
```

### 4. Create Wallet (First Time Only)

In a new terminal:
```bash
# Create wallet (you'll be prompted for password)
lncli create

# Follow prompts:
# - Enter wallet password (remember this!)
# - Enter passphrase (optional, can leave empty)
# - Choose 'n' for existing seed (we're creating new)
# - IMPORTANT: Save the seed words shown!
```

### 5. Unlock Wallet (Every Restart)

```bash
# Unlock wallet after restart
lncli unlock

# Enter the wallet password you created
```

### 6. Check Node Status

```bash
# Check if node is running and synced
lncli getinfo

# Check wallet balance
lncli walletbalance

# Get new address to receive testnet Bitcoin
lncli newaddress p2wkh
```

### 7. Get Testnet Bitcoin

1. Use the address from `lncli newaddress p2wkh`
2. Go to a testnet faucet: https://testnet-faucet.mempool.co/
3. Send testnet Bitcoin to your address
4. Wait for confirmation: `lncli walletbalance`

## Testing LND Connection

Once LND is running, test our DOMP connection:

```bash
cd implementations/reference/python
source domp-env/bin/activate
python3 test_lightning_client.py
```

You should see:
- "✅ Connected to LND at localhost:10009" (instead of timeout)
- Real node information when testing

## Quick Commands Reference

```bash
# Start LND
lnd

# Unlock wallet (in another terminal)
lncli unlock

# Check status
lncli getinfo

# Check balance
lncli walletbalance

# Create invoice
lncli addinvoice --amt 1000 --memo "Test invoice"

# Pay invoice
lncli payinvoice <bolt11_invoice>

# Stop LND
lncli stop
```

## Troubleshooting

### Connection Issues
- Make sure LND is running: `ps aux | grep lnd`
- Check if port 10009 is open: `netstat -tlnp | grep 10009`
- Check LND logs for errors

### Wallet Issues
- If wallet is locked: `lncli unlock`
- If you forgot password: You'll need to restore from seed

### Sync Issues
- LND needs to sync with Bitcoin testnet
- Check sync status: `lncli getinfo` (look for `synced_to_chain: true`)

## Production Notes

For production use:
- Use mainnet configuration
- Set up proper TLS certificates
- Configure proper authentication
- Use a reliable Bitcoin backend (not neutrino)
- Set up monitoring and backups

## Next Steps

Once LND is running:
1. Test the connection with our DOMP client
2. Implement real Lightning operations
3. Test invoice creation and payment
4. Integrate with DOMP escrow system

---

**Need Help?**
- LND Documentation: https://docs.lightning.engineering/
- LND GitHub: https://github.com/lightningnetwork/lnd
- Lightning Network Slack: https://lightningcommunity.slack.com/