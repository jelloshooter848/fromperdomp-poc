# DOMP Service Launcher

The DOMP Service Launcher (`domp_launcher.py`) is a unified management tool for the DOMP ecosystem, providing easy control over Lightning Network services, Web API, and testing.

## Features

- **🚀 Service Management**: Start/stop LND and Web API with health monitoring
- **🔐 Wallet Management**: Interactive and automated wallet unlocking
- **🧪 Test Integration**: Run comprehensive test suite with one command
- **📊 Real-time Status**: Live service status and uptime tracking
- **📄 Log Management**: Centralized logging and troubleshooting
- **⚡ Lightning Integration**: Seamless LND management with testnet support

## Quick Start

### Interactive Mode (Recommended)

```bash
python domp_launcher.py
```

This opens an interactive menu with numbered options:

```
⚡ DOMP SERVICE LAUNCHER
==================================================
Unified manager for DOMP marketplace services
==================================================

📊 SERVICE STATUS:
----------------------------------------
  ⚫ LND Lightning Node
  ⚫ DOMP Web API (port 8001)

🎮 DOMP SERVICE MENU:
  1. Start LND
  2. Start Web API
  3. Start All Services
  4. Stop LND
  5. Stop Web API
  6. Stop All Services
  7. Unlock Wallet
  8. Check Wallet Status
  9. Run Tests
  10. View Logs
  11. Restart All
  12. Help
  0. Exit

🔹 Select option (0-12):
```

### Command Line Mode

```bash
# Service management
python domp_launcher.py start        # Start all services
python domp_launcher.py stop         # Stop all services
python domp_launcher.py restart      # Restart all services
python domp_launcher.py status       # Show service status

# Individual services
python domp_launcher.py start-lnd    # Start LND only
python domp_launcher.py start-api    # Start Web API only
python domp_launcher.py stop-lnd     # Stop LND only
python domp_launcher.py stop-api     # Stop Web API only

# Wallet management
python domp_launcher.py unlock       # Interactive wallet unlock
python domp_launcher.py unlock-auto  # Automated wallet unlock

# Testing and logs
python domp_launcher.py test         # Run test suite
python domp_launcher.py logs lnd     # View LND logs
python domp_launcher.py logs web_api # View Web API logs
```

## Workflow Guide

### 1. First Time Setup

```bash
# Start the launcher
python domp_launcher.py

# Select option 3: "Start All Services"
# This will:
# - Start LND Lightning Network Daemon
# - Start DOMP Web API server
# - Show real-time status updates
```

### 2. Unlock Wallet

```bash
# After LND starts, select option 7: "Unlock Wallet"
# Enter your LND wallet password when prompted
```

### 3. Verify Everything Works

```bash
# Select option 9: "Run Tests"
# This runs all 11 tests and should show 100% pass rate
```

### 4. Access Web Interface

Open your browser to: **http://localhost:8001**

## Service Status Indicators

The launcher shows real-time service status:

- **⚫ STOPPED**: Service is not running
- **🟡 STARTING**: Service is initializing
- **🟢 RUNNING**: Service is operational
- **🔴 FAILED**: Service failed to start
- **⚪ UNKNOWN**: Service status unclear

### Wallet Status

When LND is running, wallet status is automatically displayed:

- **🔐 LND wallet is locked - needs unlocking**
- **✅ LND wallet is unlocked and operational**
- **❌ LND wallet error: [details]**

## Configuration

### Ports

- **LND gRPC**: `localhost:10009`
- **LND REST**: `localhost:8002`  
- **Web API**: `localhost:8001`

### Log Files

Logs are automatically created in the project directory:

- **LND logs**: `lnd.log`
- **Web API logs**: `web_api.log`

### Testnet Configuration

The launcher automatically configures LND for Bitcoin testnet:

- Uses `--network=testnet` flag for all `lncli` commands
- Connects to testnet Bitcoin network
- Creates testnet-specific macaroon files

## Advanced Usage

### Health Monitoring

The launcher performs comprehensive health checks:

```python
# Port connectivity tests
netstat -tln | grep :10009  # LND gRPC port
netstat -tln | grep :8001   # Web API port

# Service responsiveness  
curl http://localhost:8001/api/identity  # Web API health
lncli --network=testnet getinfo         # LND health
```

### Automatic Recovery

If services fail, the launcher provides recovery options:

1. **View Logs** (option 10): Check error details
2. **Restart All** (option 11): Clean restart of all services
3. **Individual Control**: Start/stop specific services

### Debugging

#### Service Won't Start

```bash
# Check logs for details
python domp_launcher.py logs lnd
python domp_launcher.py logs web_api

# Check port conflicts
netstat -tln | grep :10009
netstat -tln | grep :8001

# Manual service test
lnd  # Test LND startup manually
```

#### Wallet Issues

```bash
# Check wallet status manually
lncli --network=testnet getinfo

# Unlock wallet manually  
lncli --network=testnet unlock

# Check macaroon permissions
ls -la ~/.lnd/data/chain/bitcoin/testnet/
```

#### Test Failures

```bash
# Run tests individually to isolate issues
python test_lightning_client.py
python test_complete_domp_flow.py

# Check service status before testing
python domp_launcher.py status
```

## API Integration

### Service Status API

```python
from domp_launcher import DOMPLauncher

launcher = DOMPLauncher()
launcher.check_service_status()
launcher.check_service_health()

# Access service info
lnd_status = launcher.services["lnd"].status
api_status = launcher.services["web_api"].status
```

### Programmatic Control

```python
# Start services programmatically
launcher = DOMPLauncher()
success = launcher.start_all()

if success:
    # Services are running
    launcher.unlock_lnd_wallet(interactive=False)
    test_results = launcher.run_tests()
```

## Security Considerations

- **Wallet Password**: Never stored or logged by the launcher
- **Testnet Only**: Configured for Bitcoin testnet (no real money)
- **Local Access**: Services bind to localhost only
- **Process Isolation**: Each service runs in separate process
- **Clean Shutdown**: Graceful service termination

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Find conflicting process
netstat -tlnp | grep :10009
kill <PID>  # Kill conflicting process
```

**Permission Denied**
```bash
# Check file permissions
ls -la ~/.lnd/
chmod 600 ~/.lnd/data/chain/bitcoin/testnet/admin.macaroon
```

**Service Timeout**
- Increase timeout values in launcher configuration
- Check system resources (CPU, memory)
- Verify network connectivity

**Wallet Locked After Restart**
- This is normal LND behavior
- Use launcher option 7 to unlock
- Consider automating with `unlock-auto` command

### Getting Help

1. **Interactive Help**: Select option 12 in the launcher menu
2. **Command Help**: `python domp_launcher.py --help`
3. **Service Logs**: Use options 10 or `logs` command
4. **Test Debugging**: Run individual test files

## Development

### Extending the Launcher

The launcher is modular and can be extended:

```python
# Add new service
launcher.services["new_service"] = ServiceInfo(
    "New Service", ServiceStatus.STOPPED, port=8080
)

# Add custom health check
def check_custom_service():
    # Custom health check logic
    pass

# Add to launcher
launcher.check_custom_service = check_custom_service
```

### Contributing

When modifying the launcher:

1. Test all service combinations
2. Verify error handling  
3. Update help text and documentation
4. Test both interactive and command-line modes
5. Ensure graceful shutdown handling

## Production Notes

While the launcher is designed for development and testing:

- **Production**: Use systemd or Docker for service management
- **Monitoring**: Implement proper monitoring and alerting
- **Security**: Use mainnet with proper security measures
- **Scaling**: Consider load balancing for high-traffic scenarios

The launcher provides an excellent foundation for understanding service dependencies and can inform production deployment strategies.