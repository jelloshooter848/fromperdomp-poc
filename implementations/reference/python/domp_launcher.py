#!/usr/bin/env python3
"""
DOMP Service Launcher
Unified launcher and manager for the DOMP ecosystem services.
"""

import subprocess
import sys
import time
import os
import signal
import json
import requests
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

class ServiceStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class ServiceInfo:
    name: str
    status: ServiceStatus
    pid: Optional[int] = None
    port: Optional[int] = None
    process: Optional[subprocess.Popen] = None
    start_time: Optional[float] = None

class DOMPLauncher:
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {
            "lnd": ServiceInfo("LND Lightning Node", ServiceStatus.STOPPED),
            "web_api": ServiceInfo("DOMP Web API", ServiceStatus.STOPPED, port=8001)
        }
        self.project_dir = "/home/lando/projects/fromperdomp-poc/implementations/reference/python"
        
    def print_header(self):
        """Print the launcher header."""
        print("⚡ DOMP SERVICE LAUNCHER")
        print("=" * 50)
        print("Unified manager for DOMP marketplace services")
        print("=" * 50)
    
    def print_status(self):
        """Print current status of all services."""
        print("\n📊 SERVICE STATUS:")
        print("-" * 40)
        for name, service in self.services.items():
            status_icon = {
                ServiceStatus.STOPPED: "⚫",
                ServiceStatus.STARTING: "🟡", 
                ServiceStatus.RUNNING: "🟢",
                ServiceStatus.FAILED: "🔴",
                ServiceStatus.UNKNOWN: "⚪"
            }[service.status]
            
            port_info = f" (port {service.port})" if service.port else ""
            pid_info = f" [PID: {service.pid}]" if service.pid else ""
            uptime_info = ""
            if service.start_time and service.status == ServiceStatus.RUNNING:
                uptime = time.time() - service.start_time
                uptime_info = f" (up {uptime:.0f}s)"
            
            print(f"  {status_icon} {service.name}{port_info}{pid_info}{uptime_info}")
    
    def check_service_status(self):
        """Check actual status of services by process and port."""
        # Check for existing processes
        try:
            # Check LND
            result = subprocess.run(["pgrep", "-f", "lnd"], capture_output=True, text=True)
            if result.returncode == 0:
                lnd_pid = int(result.stdout.strip().split('\n')[0])
                self.services["lnd"].status = ServiceStatus.RUNNING
                self.services["lnd"].pid = lnd_pid
            else:
                self.services["lnd"].status = ServiceStatus.STOPPED
                self.services["lnd"].pid = None
            
            # Check Web API
            result = subprocess.run(["pgrep", "-f", "uvicorn.*web_api"], capture_output=True, text=True)
            if result.returncode == 0:
                api_pid = int(result.stdout.strip().split('\n')[0])
                self.services["web_api"].status = ServiceStatus.RUNNING
                self.services["web_api"].pid = api_pid
            else:
                self.services["web_api"].status = ServiceStatus.STOPPED
                self.services["web_api"].pid = None
                
        except Exception as e:
            print(f"⚠️  Error checking service status: {e}")
    
    def check_service_health(self):
        """Check if services are responding properly."""
        # Check LND health
        if self.services["lnd"].status == ServiceStatus.RUNNING:
            try:
                # Try to connect to LND gRPC port
                result = subprocess.run(
                    ["netstat", "-tln"], 
                    capture_output=True, text=True, timeout=5
                )
                if ":10009" in result.stdout:
                    self.services["lnd"].status = ServiceStatus.RUNNING
                else:
                    self.services["lnd"].status = ServiceStatus.FAILED
            except:
                self.services["lnd"].status = ServiceStatus.UNKNOWN
        
        # Check Web API health
        if self.services["web_api"].status == ServiceStatus.RUNNING:
            try:
                response = requests.get("http://localhost:8001/api/identity", timeout=3)
                if response.status_code == 200:
                    self.services["web_api"].status = ServiceStatus.RUNNING
                else:
                    self.services["web_api"].status = ServiceStatus.FAILED
            except:
                self.services["web_api"].status = ServiceStatus.FAILED
    
    def unlock_lnd_wallet(self, interactive: bool = True):
        """Unlock LND wallet to enable Lightning operations."""
        print("🔓 Unlocking LND wallet...")
        
        try:
            if interactive:
                # Interactive unlock - let user enter password
                print("🔑 Please enter your LND wallet password when prompted...")
                result = subprocess.run([
                    "lncli", "--network=testnet", "unlock"
                ], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
                
                if result.returncode == 0:
                    print("✅ LND wallet unlocked successfully")
                    return True
                else:
                    print("❌ Wallet unlock failed")
                    return False
            else:
                # Non-interactive unlock with echo (for automation)
                import getpass
                password = getpass.getpass("🔑 Enter LND wallet password: ")
                
                # Use expect-like approach for non-interactive unlock
                process = subprocess.Popen([
                    "lncli", "--network=testnet", "unlock"
                ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                stdout, stderr = process.communicate(input=password + "\n")
                
                if process.returncode == 0 or "wallet already unlocked" in stderr.lower():
                    print("✅ LND wallet unlocked successfully")
                    return True
                else:
                    print(f"❌ Wallet unlock failed: {stderr}")
                    return False
                
        except Exception as e:
            print(f"❌ Failed to unlock wallet: {e}")
            return False
    
    def start_lnd(self, show_logs: bool = False):
        """Start LND Lightning Network Daemon."""
        if self.services["lnd"].status == ServiceStatus.RUNNING:
            print("✅ LND is already running")
            print("ℹ️  Use 'unlock wallet' if wallet needs unlocking")
            return True
        
        print("🚀 Starting LND Lightning Network Daemon...")
        self.services["lnd"].status = ServiceStatus.STARTING
        
        try:
            # Start LND process with proper logging
            if show_logs:
                # Start LND with live output for debugging
                print("📄 Starting LND with live logs (Ctrl+C to stop logs, LND continues running)...")
                process = subprocess.Popen(
                    ["lnd"],
                    cwd=self.project_dir
                )
            else:
                # Start LND in background
                log_file = open(f"{self.project_dir}/lnd.log", "w")
                process = subprocess.Popen(
                    ["lnd"],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=self.project_dir
                )
            
            self.services["lnd"].process = process
            self.services["lnd"].start_time = time.time()
            
            # Wait for LND to start (check by port, not just process)
            print("⏳ Waiting for LND to initialize...")
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                
                # Check if LND is listening on port 10009
                try:
                    result = subprocess.run(
                        ["netstat", "-tln"], 
                        capture_output=True, text=True, timeout=5
                    )
                    if ":10009" in result.stdout and process.poll() is None:
                        self.services["lnd"].status = ServiceStatus.RUNNING
                        self.services["lnd"].pid = process.pid
                        print("✅ LND started successfully")
                        print("🔐 LND wallet needs to be unlocked for Lightning operations")
                        return True
                except:
                    pass
                
                # Check if process died
                if process.poll() is not None:
                    print(f"❌ LND process exited with code {process.returncode}")
                    print("📄 Check lnd.log for error details")
                    self.services["lnd"].status = ServiceStatus.FAILED
                    return False
                
                print(f"   Starting... ({i+1}/30)")
            
            print("❌ LND failed to start within 30 seconds")
            print("📄 Check lnd.log for error details")
            self.services["lnd"].status = ServiceStatus.FAILED
            return False
            
        except Exception as e:
            print(f"❌ Failed to start LND: {e}")
            self.services["lnd"].status = ServiceStatus.FAILED
            return False
    
    def start_web_api(self):
        """Start DOMP Web API server."""
        if self.services["web_api"].status == ServiceStatus.RUNNING:
            print("✅ Web API is already running")
            return True
        
        print("🚀 Starting DOMP Web API server...")
        self.services["web_api"].status = ServiceStatus.STARTING
        
        try:
            # Start uvicorn with logging
            log_file = open(f"{self.project_dir}/web_api.log", "w")
            process = subprocess.Popen([
                "python3", "-m", "uvicorn", "web_api:app", 
                "--host", "0.0.0.0", "--port", "8001"
            ], stdout=log_file, stderr=subprocess.STDOUT, cwd=self.project_dir)
            
            self.services["web_api"].process = process
            self.services["web_api"].start_time = time.time()
            
            # Wait for Web API to start
            print("⏳ Waiting for Web API to initialize...")
            for i in range(15):  # Wait up to 15 seconds
                time.sleep(1)
                self.check_service_status()
                if self.services["web_api"].status == ServiceStatus.RUNNING:
                    # Additional health check
                    self.check_service_health()
                    if self.services["web_api"].status == ServiceStatus.RUNNING:
                        print("✅ Web API started successfully")
                        print("🌐 Web interface: http://localhost:8001")
                        return True
                print(f"   Starting... ({i+1}/15)")
            
            print("❌ Web API failed to start within 15 seconds")
            self.services["web_api"].status = ServiceStatus.FAILED
            return False
            
        except Exception as e:
            print(f"❌ Failed to start Web API: {e}")
            self.services["web_api"].status = ServiceStatus.FAILED
            return False
    
    def stop_service(self, service_name: str):
        """Stop a specific service."""
        service = self.services.get(service_name)
        if not service:
            print(f"❌ Unknown service: {service_name}")
            return False
        
        if service.status == ServiceStatus.STOPPED:
            print(f"✅ {service.name} is already stopped")
            return True
        
        print(f"🛑 Stopping {service.name}...")
        
        try:
            # Try graceful shutdown first
            if service.process:
                service.process.terminate()
                service.process.wait(timeout=5)
            elif service.pid:
                os.kill(service.pid, signal.SIGTERM)
                time.sleep(2)
            
            # Force kill if still running
            self.check_service_status()
            if service.status == ServiceStatus.RUNNING and service.pid:
                os.kill(service.pid, signal.SIGKILL)
                time.sleep(1)
            
            service.status = ServiceStatus.STOPPED
            service.pid = None
            service.process = None
            service.start_time = None
            
            print(f"✅ {service.name} stopped")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping {service.name}: {e}")
            return False
    
    def start_all(self):
        """Start all DOMP services in correct order."""
        print("🚀 Starting DOMP ecosystem...")
        
        # Start LND first
        if not self.start_lnd():
            print("❌ Failed to start LND - aborting")
            return False
        
        # Wait a bit for LND to stabilize
        time.sleep(2)
        
        # Start Web API
        if not self.start_web_api():
            print("❌ Failed to start Web API")
            return False
        
        print("\n🎉 DOMP ecosystem started successfully!")
        print("🔗 Services are ready for testing")
        return True
    
    def stop_all(self):
        """Stop all DOMP services."""
        print("🛑 Stopping DOMP ecosystem...")
        
        # Stop in reverse order
        self.stop_service("web_api")
        self.stop_service("lnd")
        
        print("✅ All services stopped")
    
    def run_tests(self):
        """Run the comprehensive test suite."""
        print("🧪 Running DOMP test suite...")
        
        # Check if services are running
        self.check_service_status()
        self.check_service_health()
        
        if (self.services["lnd"].status != ServiceStatus.RUNNING or 
            self.services["web_api"].status != ServiceStatus.RUNNING):
            print("⚠️  Warning: Not all services are running")
            print("   Starting services first...")
            if not self.start_all():
                print("❌ Cannot run tests - services failed to start")
                return False
        
        try:
            print("▶️  Executing test suite...")
            result = subprocess.run([
                sys.executable, "run_all_tests.py"
            ], cwd=self.project_dir)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
    
    def show_logs(self, service_name: str):
        """Show logs for a specific service."""
        service = self.services.get(service_name)
        if not service:
            print(f"❌ Unknown service: {service_name}")
            return
        
        print(f"📄 Logs for {service.name}:")
        print("-" * 40)
        
        # Check for log files
        log_files = {
            "lnd": f"{self.project_dir}/lnd.log",
            "web_api": f"{self.project_dir}/web_api.log"
        }
        
        if service_name in log_files:
            log_file = log_files[service_name]
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        # Show last 50 lines
                        lines = f.readlines()
                        for line in lines[-50:]:
                            print(line.rstrip())
                else:
                    print(f"📄 No log file found: {log_file}")
            except Exception as e:
                print(f"❌ Error reading log file: {e}")
        else:
            print(f"📄 No log file configured for {service_name}")
    
    def check_wallet_status(self):
        """Check if LND wallet is unlocked."""
        try:
            # Use testnet flag since LND is running on testnet
            result = subprocess.run(
                ["lncli", "--network=testnet", "getinfo"], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("✅ LND wallet is unlocked and operational")
                return True
            else:
                if "wallet locked" in result.stderr.lower():
                    print("🔐 LND wallet is locked - needs unlocking")
                else:
                    print(f"❌ LND wallet error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Failed to check wallet status: {e}")
            return False

def interactive_menu():
    """Interactive menu interface."""
    launcher = DOMPLauncher()
    
    while True:
        # Clear screen for better UX (optional)
        print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
        
        launcher.print_header()
        launcher.check_service_status()
        launcher.check_service_health()
        launcher.print_status()
        
        # Show wallet status if LND is running
        if launcher.services["lnd"].status == ServiceStatus.RUNNING:
            print("\n🔐 WALLET STATUS:")
            launcher.check_wallet_status()
        
        print("\n🎮 DOMP SERVICE MENU:")
        print("  1. Start LND")
        print("  2. Start Web API") 
        print("  3. Start All Services")
        print("  4. Stop LND")
        print("  5. Stop Web API")
        print("  6. Stop All Services")
        print("  7. Unlock Wallet")
        print("  8. Check Wallet Status")
        print("  9. Run Tests")
        print("  10. View Logs")
        print("  11. Restart All")
        print("  12. Help")
        print("  0. Exit")
        
        try:
            choice = input("\n🔹 Select option (0-12): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                launcher.start_lnd()
            elif choice == "2":
                launcher.start_web_api()
            elif choice == "3":
                launcher.start_all()
            elif choice == "4":
                launcher.stop_service("lnd")
            elif choice == "5":
                launcher.stop_service("web_api")
            elif choice == "6":
                launcher.stop_all()
            elif choice == "7":
                launcher.check_service_status()
                if launcher.services["lnd"].status == ServiceStatus.RUNNING:
                    launcher.unlock_lnd_wallet(interactive=True)
                else:
                    print("❌ LND is not running. Start LND first.")
            elif choice == "8":
                launcher.check_service_status()
                if launcher.services["lnd"].status == ServiceStatus.RUNNING:
                    launcher.check_wallet_status()
                else:
                    print("❌ LND is not running. Start LND first.")
            elif choice == "9":
                launcher.run_tests()
            elif choice == "10":
                log_choice = input("View logs for (lnd/api): ").strip().lower()
                if log_choice in ["lnd", "api"]:
                    service_name = "lnd" if log_choice == "lnd" else "web_api"
                    launcher.show_logs(service_name)
                else:
                    print("❌ Invalid log choice")
            elif choice == "11":
                print("🔄 Restarting all services...")
                launcher.stop_all()
                time.sleep(2)
                launcher.start_all()
            elif choice == "12":
                print("\n📚 DOMP LAUNCHER HELP:")
                print("  🚀 Start services before running tests")
                print("  🔐 Unlock wallet after starting LND")
                print("  🧪 Run tests to verify everything works")
                print("  📄 Check logs if services fail to start")
                print("  🌐 Web interface: http://localhost:8001")
                print("  ⚡ Lightning gRPC: localhost:10009")
            else:
                print("❌ Invalid choice. Please select 0-12.")
            
            if choice != "0":
                input("\n⏸️  Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\n⏸️  Press Enter to continue...")

def main():
    """Main launcher interface."""
    launcher = DOMPLauncher()
    
    # Check if running in interactive mode or command mode
    if len(sys.argv) < 2:
        # No arguments - start interactive menu
        interactive_menu()
        return
    
    # Command line mode
    launcher.print_header()
    command = sys.argv[1].lower()
    
    # Always check current status first
    launcher.check_service_status()
    
    if command == "status":
        launcher.check_service_health()
        launcher.print_status()
        
    elif command == "start":
        launcher.start_all()
        launcher.print_status()
        
    elif command == "stop":
        launcher.stop_all()
        launcher.print_status()
        
    elif command == "restart":
        launcher.stop_all()
        time.sleep(2)
        launcher.start_all()
        launcher.print_status()
        
    elif command == "test":
        launcher.run_tests()
        
    elif command == "start-lnd":
        launcher.start_lnd()
        launcher.print_status()
        
    elif command == "start-api":
        launcher.start_web_api()
        launcher.print_status()
        
    elif command == "stop-lnd":
        launcher.stop_service("lnd")
        launcher.print_status()
        
    elif command == "stop-api":
        launcher.stop_service("web_api")
        launcher.print_status()
        
    elif command == "unlock":
        launcher.check_service_status()
        if launcher.services["lnd"].status == ServiceStatus.RUNNING:
            launcher.unlock_lnd_wallet(interactive=True)
        else:
            print("❌ LND is not running. Start LND first with: python domp_launcher.py start-lnd")
    
    elif command == "unlock-auto":
        launcher.check_service_status()
        if launcher.services["lnd"].status == ServiceStatus.RUNNING:
            launcher.unlock_lnd_wallet(interactive=False)
        else:
            print("❌ LND is not running. Start LND first with: python domp_launcher.py start-lnd")
    
    elif command == "logs":
        if len(sys.argv) < 3:
            print("❌ Please specify service: lnd or web_api")
        else:
            launcher.show_logs(sys.argv[2])
    
    else:
        print(f"❌ Unknown command: {command}")
        print("\n📚 Available commands:")
        print("  status        - Show service status")
        print("  start         - Start all services") 
        print("  stop          - Stop all services")
        print("  restart       - Restart all services")
        print("  start-lnd     - Start LND only")
        print("  start-api     - Start Web API only")
        print("  stop-lnd      - Stop LND only")
        print("  stop-api      - Stop Web API only")
        print("  unlock        - Unlock LND wallet (interactive)")
        print("  unlock-auto   - Unlock LND wallet (automated)")
        print("  test          - Run test suite")
        print("  logs <service> - Show logs for service")
        print("\n💡 Run without arguments for interactive menu")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Launcher error: {e}")
        sys.exit(1)