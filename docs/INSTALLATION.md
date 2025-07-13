# DOMP Installation & Setup Guide

Complete installation guide for setting up DOMP (Decentralized Online Marketplace Protocol) development environment and running the reference implementation.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Setup](#detailed-setup)
- [Development Environment](#development-environment)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## System Requirements

### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Python**: 3.8 or higher
- **Memory**: 512MB RAM
- **Storage**: 100MB free space
- **Network**: Internet connection for dependencies and relay communication

### Recommended Requirements
- **Operating System**: Ubuntu 20.04+ or macOS 12+
- **Python**: 3.11 or higher
- **Memory**: 2GB RAM
- **Storage**: 1GB free space
- **Network**: Stable broadband connection

### Development Requirements
- **Git**: For repository management
- **Code Editor**: VS Code, PyCharm, or similar
- **Terminal**: Command line access

## Quick Installation

### 1. Clone Repository
```bash
# Clone the DOMP repository
git clone https://github.com/your-org/fromperdomp-poc.git
cd fromperdomp-poc/implementations/reference/python
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python3 -m venv domp-env

# Activate virtual environment
source domp-env/bin/activate  # Linux/macOS
# OR
domp-env\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Alternative: Install packages individually
pip install fastapi uvicorn websockets secp256k1 pydantic
```

### 4. Run Applications
```bash
# Start web interface
python3 web_api.py
# Visit http://localhost:8080

# OR start CLI client
python3 domp_marketplace_cli.py
```

## Detailed Setup

### Python Installation

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install build tools (required for secp256k1)
sudo apt install build-essential pkg-config libsecp256k1-dev

# Verify installation
python3.11 --version
```

#### macOS
```bash
# Using Homebrew
brew install python@3.11
brew install secp256k1

# Verify installation
python3 --version
```

#### Windows (WSL2)
```bash
# Install WSL2 with Ubuntu
wsl --install -d Ubuntu

# Follow Ubuntu instructions above
```

### Dependency Installation

#### Core Dependencies
```bash
# Essential packages
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install websockets==12.0
pip install pydantic==2.5.0

# Cryptography
pip install secp256k1==0.14.0

# Optional: Development tools
pip install pytest==7.4.3
pip install black==23.11.0
pip install flake8==6.1.0
```

#### Build Requirements for secp256k1

**Ubuntu/Debian:**
```bash
sudo apt install build-essential
sudo apt install pkg-config
sudo apt install libsecp256k1-dev
sudo apt install libffi-dev
```

**macOS:**
```bash
# Install Xcode command line tools
xcode-select --install

# Install secp256k1 via Homebrew
brew install secp256k1
brew install libffi
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install pkgconfig
sudo yum install libsecp256k1-devel
sudo yum install libffi-devel
```

### Environment Setup

#### Virtual Environment Best Practices
```bash
# Create isolated environment
python3 -m venv domp-env

# Activate environment
source domp-env/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Create requirements.txt if it doesn't exist
pip freeze > requirements.txt
```

#### Environment Variables
```bash
# Create .env file for configuration
cat > .env << EOF
# DOMP Configuration
DOMP_ENV=development
DOMP_LOG_LEVEL=INFO
DOMP_WEB_PORT=8080
DOMP_WEB_HOST=0.0.0.0

# Lightning Configuration (for real Lightning integration)
LIGHTNING_RPC_PATH=/path/to/lightning-rpc
LIGHTNING_NETWORK=testnet

# Nostr Configuration
DEFAULT_NOSTR_RELAYS=wss://relay.damus.io,wss://nos.lol,wss://relay.snort.social

# Security
DOMP_PRIVATE_KEY_FILE=domp_identity.json
DOMP_MAX_EVENT_SIZE=65536
DOMP_POW_DIFFICULTY=20
EOF
```

## Development Environment

### IDE Configuration

#### VS Code Setup
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./domp-env/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/domp-env": true,
        "**/*.pyc": true
    }
}
```

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "DOMP Web API",
            "type": "python",
            "request": "launch",
            "program": "web_api.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/implementations/reference/python",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/implementations/reference/python"
            }
        },
        {
            "name": "DOMP CLI",
            "type": "python",
            "request": "launch",
            "program": "domp_marketplace_cli.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/implementations/reference/python"
        }
    ]
}
```

#### PyCharm Setup
1. Open the project folder
2. Go to Settings → Project → Python Interpreter
3. Add interpreter from `domp-env/bin/python`
4. Set run configurations for `web_api.py` and `domp_marketplace_cli.py`

### Code Quality Tools

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        args: [--line-length=88]
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --ignore=E203,W503]
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]
EOF

# Install hooks
pre-commit install
```

#### Testing Setup
```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov

# Create pytest.ini
cat > pytest.ini << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = --strict-markers --cov=domp --cov-report=html --cov-report=term
EOF

# Run tests
pytest
```

## Configuration

### Application Configuration

#### Web API Configuration
```python
# config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Web server
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    
    # DOMP protocol
    pow_difficulty: int = 20
    max_event_size: int = 65536
    event_cache_ttl: int = 300
    
    # Lightning
    lightning_network: str = "testnet"
    lightning_rpc_path: str = ""
    
    # Nostr relays
    default_relays: list = [
        "wss://relay.damus.io",
        "wss://nos.lol", 
        "wss://relay.snort.social"
    ]
    
    # Database
    database_url: str = "sqlite:///domp.db"
    
    # Security
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    private_key_file: str = "domp_identity.json"
    
    class Config:
        env_file = ".env"
        env_prefix = "DOMP_"

# Usage
settings = Settings()
```

#### CLI Configuration
```python
# cli_config.py
import json
import os

class CLIConfig:
    def __init__(self, config_file="domp_cli_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        defaults = {
            "identity_file": "domp_identity.json",
            "preferred_relays": [
                "wss://relay.damus.io",
                "wss://nos.lol"
            ],
            "lightning_network": "testnet",
            "ui_theme": "dark",
            "auto_accept_bids": False,
            "notification_sound": True,
            "default_category": "general",
            "max_price_sats": 100_000_000
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    defaults.update(user_config)
            except Exception:
                pass
        
        return defaults
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
    
    def get(self, key, default=None):
        return self.config.get(key, default)
```

### Network Configuration

#### Firewall Rules (Linux)
```bash
# Allow DOMP web interface
sudo ufw allow 8080/tcp

# Allow Lightning Network (if using real Lightning)
sudo ufw allow 9735/tcp

# Allow Nostr relay connections (outbound only)
# No additional rules needed for outbound WebSocket connections
```

#### Nginx Reverse Proxy (Production)
```nginx
# /etc/nginx/sites-available/domp
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Database Setup (Optional)

#### SQLite (Default)
```python
# database.py
import sqlite3
import json
from typing import List, Dict, Optional

class DOMPDatabase:
    def __init__(self, db_path: str = "domp.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                pubkey TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                kind INTEGER NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                sig TEXT NOT NULL,
                received_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # Reputation scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reputation_scores (
                id TEXT PRIMARY KEY,
                transaction_id TEXT NOT NULL,
                reviewer_pubkey TEXT NOT NULL,
                reviewed_pubkey TEXT NOT NULL,
                overall_rating INTEGER NOT NULL,
                item_quality INTEGER,
                shipping_speed INTEGER,
                communication INTEGER,
                payment_reliability INTEGER,
                transaction_amount_sats INTEGER NOT NULL,
                verified_purchase BOOLEAN DEFAULT FALSE,
                escrow_completed BOOLEAN DEFAULT FALSE,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_pubkey ON events(pubkey)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reputation_reviewed ON reputation_scores(reviewed_pubkey)')
        
        conn.commit()
        conn.close()
```

#### PostgreSQL (Production)
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE domp;
CREATE USER domp_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE domp TO domp_user;
\q

# Update configuration
pip install psycopg2-binary
export DATABASE_URL="postgresql://domp_user:your_password@localhost/domp"
```

## Verification

### Installation Verification

#### Basic Functionality Test
```bash
# Test Python environment
python3 -c "import sys; print(f'Python {sys.version}')"

# Test dependencies
python3 -c "
import fastapi
import uvicorn
import websockets
import secp256k1
import pydantic
print('✅ All dependencies imported successfully')
"

# Test DOMP imports
python3 -c "
import sys
sys.path.insert(0, '.')
from domp.crypto import KeyPair
from domp.events import ProductListing
from domp.validation import validate_event
print('✅ DOMP modules imported successfully')
"
```

#### Cryptography Test
```bash
# Test key generation and signing
python3 -c "
from domp.crypto import KeyPair
from domp.events import ProductListing

# Generate keypair
keypair = KeyPair()
print(f'✅ Generated keypair: {keypair.public_key_hex[:16]}...')

# Create and sign event
listing = ProductListing(
    product_name='Test Item',
    description='Test description',
    price_satoshis=1000000,
    category='test',
    seller_collateral_satoshis=100000,
    listing_id='test_123'
)
listing.sign(keypair)
print('✅ Event created and signed successfully')

# Validate event
from domp.validation import validate_event
is_valid = validate_event(listing.to_dict())
print(f'✅ Event validation: {is_valid}')
"
```

#### Network Connectivity Test
```bash
# Test Nostr relay connectivity
python3 -c "
import asyncio
import websockets
import json

async def test_relay():
    try:
        websocket = await websockets.connect('wss://relay.damus.io')
        print('✅ Connected to Nostr relay')
        
        # Test subscription
        sub = ['REQ', 'test', {'kinds': [1], 'limit': 1}]
        await websocket.send(json.dumps(sub))
        
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        print('✅ Received response from relay')
        
        await websocket.close()
    except Exception as e:
        print(f'❌ Relay test failed: {e}')

asyncio.run(test_relay())
"
```

### Application Testing

#### Web Interface Test
```bash
# Start web server in background
python3 web_api.py &
WEB_PID=$!

# Wait for server to start
sleep 3

# Test endpoints
curl -f http://localhost:8080/api/identity && echo "✅ Identity endpoint working"
curl -f http://localhost:8080/api/listings && echo "✅ Listings endpoint working"
curl -f http://localhost:8080/ && echo "✅ Web interface accessible"

# Clean up
kill $WEB_PID
```

#### CLI Test
```bash
# Test CLI startup
timeout 5s python3 domp_marketplace_cli.py << EOF || echo "✅ CLI started successfully"
q
EOF
```

## Troubleshooting

### Common Issues

#### 1. secp256k1 Installation Fails

**Error:** `Failed building wheel for secp256k1`

**Solutions:**
```bash
# Ubuntu/Debian
sudo apt install build-essential pkg-config libsecp256k1-dev libffi-dev

# macOS
brew install secp256k1 libffi
export LDFLAGS="-L$(brew --prefix libffi)/lib"
export CPPFLAGS="-I$(brew --prefix libffi)/include"
pip install secp256k1

# Alternative: Use conda
conda install -c conda-forge secp256k1
```

#### 2. Port Already in Use

**Error:** `[Errno 98] Address already in use`

**Solutions:**
```bash
# Find process using port 8080
lsof -i :8080
sudo netstat -tulpn | grep :8080

# Kill existing process
kill -9 PID_NUMBER

# Or use different port
export DOMP_WEB_PORT=8081
python3 web_api.py
```

#### 3. Permission Denied

**Error:** `Permission denied: 'domp_identity.json'`

**Solutions:**
```bash
# Fix file permissions
chmod 600 domp_identity.json

# Fix directory permissions
chmod 755 .
```

#### 4. Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'domp'`

**Solutions:**
```bash
# Ensure you're in the correct directory
cd implementations/reference/python

# Add to Python path
export PYTHONPATH="$PWD:$PYTHONPATH"

# Or use absolute imports
python3 -c "import sys; sys.path.insert(0, '.'); import domp"
```

#### 5. WebSocket Connection Fails

**Error:** Connection refused to WebSocket

**Solutions:**
```bash
# Check firewall
sudo ufw status

# Test direct connection
telnet localhost 8080

# Check proxy settings
unset http_proxy https_proxy

# Test with different relay
python3 -c "
import asyncio
import websockets
async def test():
    ws = await websockets.connect('wss://nos.lol')
    print('Connected successfully')
    await ws.close()
asyncio.run(test())
"
```

### Debugging Tools

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in environment
export DOMP_LOG_LEVEL=DEBUG
```

#### Network Debugging
```bash
# Monitor network connections
netstat -tulpn | grep python

# Monitor WebSocket traffic
tcpdump -i any port 443 and host relay.damus.io

# Test DNS resolution
nslookup relay.damus.io
```

#### Performance Monitoring
```bash
# Monitor resource usage
top -p $(pgrep -f "python3 web_api.py")

# Monitor disk I/O
iotop -p $(pgrep -f "python3")

# Profile Python application
python3 -m cProfile -o profile.stats web_api.py
```

## Production Deployment

### Security Hardening

#### Application Security
```bash
# Create dedicated user
sudo useradd -r -s /bin/false domp
sudo mkdir /opt/domp
sudo chown domp:domp /opt/domp

# Set file permissions
chmod 700 /opt/domp
chmod 600 /opt/domp/domp_identity.json

# Run as non-root user
sudo -u domp python3 web_api.py
```

#### Network Security
```bash
# Restrict firewall rules
sudo ufw deny incoming
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Use reverse proxy
# See Nginx configuration above
```

#### Environment Variables
```bash
# Use systemd environment file
sudo tee /etc/systemd/system/domp.env << EOF
DOMP_ENV=production
DOMP_LOG_LEVEL=WARNING
DOMP_WEB_HOST=127.0.0.1
DOMP_WEB_PORT=8080
DOMP_PRIVATE_KEY_FILE=/opt/domp/domp_identity.json
DATABASE_URL=postgresql://domp_user:password@localhost/domp
EOF

sudo chmod 600 /etc/systemd/system/domp.env
```

### Systemd Service

#### Service Configuration
```ini
# /etc/systemd/system/domp.service
[Unit]
Description=DOMP Marketplace API
After=network.target postgresql.service

[Service]
Type=simple
User=domp
Group=domp
WorkingDirectory=/opt/domp
Environment=PYTHONPATH=/opt/domp
EnvironmentFile=/etc/systemd/system/domp.env
ExecStart=/opt/domp/domp-env/bin/python3 /opt/domp/web_api.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/domp

[Install]
WantedBy=multi-user.target
```

#### Service Management
```bash
# Install and start service
sudo systemctl daemon-reload
sudo systemctl enable domp
sudo systemctl start domp

# Check status
sudo systemctl status domp

# View logs
sudo journalctl -u domp -f
```

### Monitoring

#### Log Management
```bash
# Configure log rotation
sudo tee /etc/logrotate.d/domp << EOF
/var/log/domp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 domp domp
    postrotate
        systemctl reload domp
    endscript
}
EOF
```

#### Health Monitoring
```bash
# Create health check script
sudo tee /opt/domp/health_check.sh << EOF
#!/bin/bash
curl -f http://localhost:8080/api/identity > /dev/null 2>&1
exit $?
EOF

sudo chmod +x /opt/domp/health_check.sh

# Add to crontab for monitoring
echo "*/5 * * * * /opt/domp/health_check.sh || systemctl restart domp" | sudo crontab -
```

### Backup Strategy

#### Data Backup
```bash
# Backup script
sudo tee /opt/domp/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/domp/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup identity
cp /opt/domp/domp_identity.json $BACKUP_DIR/identity_$TIMESTAMP.json

# Backup database (if using PostgreSQL)
pg_dump domp > $BACKUP_DIR/database_$TIMESTAMP.sql

# Backup configuration
cp /etc/systemd/system/domp.env $BACKUP_DIR/config_$TIMESTAMP.env

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*" -type f -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
EOF

sudo chmod +x /opt/domp/backup.sh

# Schedule daily backups
echo "0 2 * * * /opt/domp/backup.sh" | sudo crontab -
```

---

This installation guide covers everything from basic setup to production deployment. For additional help, consult the [Developer Guide](DEVELOPER_GUIDE.md) or [API Documentation](API.md).