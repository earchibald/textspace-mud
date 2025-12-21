#!/usr/bin/env python
"""
Setup and management script for Multi-User Text Space System
Provides easy setup, configuration, and management commands
"""
import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

class TextSpaceSetup:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.venv_dir = self.project_dir / "venv"
    
    def check_python_version(self):
        """Check Python version compatibility"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        return True
    
    def create_virtual_environment(self):
        """Create Python virtual environment"""
        if self.venv_dir.exists():
            print("✅ Virtual environment already exists")
            return True
        
        try:
            print("Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], check=True)
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def get_pip_command(self):
        """Get pip command for the virtual environment"""
        if os.name == 'nt':  # Windows
            return str(self.venv_dir / "Scripts" / "pip")
        else:  # Unix-like
            return str(self.venv_dir / "bin" / "pip")
    
    def install_dependencies(self, include_database=False):
        """Install Python dependencies"""
        pip_cmd = self.get_pip_command()
        
        try:
            # Install core dependencies
            print("Installing core dependencies...")
            subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
            print("✅ Core dependencies installed")
            
            # Install database dependencies if requested
            if include_database:
                print("Installing database dependencies...")
                subprocess.run([pip_cmd, "install", "-r", "requirements-db.txt"], check=True)
                print("✅ Database dependencies installed")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_env_file(self):
        """Create .env file from template"""
        env_file = Path(".env")
        env_example = Path(".env.example")
        
        if env_file.exists():
            print("✅ .env file already exists")
            return True
        
        if env_example.exists():
            try:
                content = env_example.read_text()
                env_file.write_text(content)
                print("✅ .env file created from template")
                print("   Edit .env to configure your settings")
                return True
            except Exception as e:
                print(f"❌ Failed to create .env file: {e}")
                return False
        else:
            # Create basic .env file
            basic_env = """# Multi-User Text Space System Configuration

# Backend Selection
USE_DATABASE=false

# Database Configuration (if USE_DATABASE=true)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=textspace
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# Security
SECRET_KEY=change-this-secret-key
PASSWORD_SALT_ROUNDS=12

# Optional: Database Authentication
# MONGODB_USERNAME=textspace
# MONGODB_PASSWORD=textspace123
# REDIS_PASSWORD=your-redis-password
"""
            try:
                env_file.write_text(basic_env)
                print("✅ Basic .env file created")
                print("   Edit .env to configure your settings")
                return True
            except Exception as e:
                print(f"❌ Failed to create .env file: {e}")
                return False
    
    def check_config_files(self):
        """Check if configuration files exist"""
        required_files = ['rooms.yaml', 'bots.yaml', 'items.yaml', 'scripts.yaml']
        missing_files = []
        
        for filename in required_files:
            if not Path(filename).exists():
                missing_files.append(filename)
        
        if missing_files:
            print(f"❌ Missing configuration files: {', '.join(missing_files)}")
            return False
        else:
            print("✅ All configuration files present")
            return True
    
    def run_tests(self):
        """Run test suite"""
        try:
            python_cmd = str(self.venv_dir / "bin" / "python") if os.name != 'nt' else str(self.venv_dir / "Scripts" / "python")
            
            print("Running test suite...")
            result = subprocess.run([python_cmd, "test_suite.py"], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ All tests passed")
                return True
            else:
                print("❌ Some tests failed")
                print(result.stdout)
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ Failed to run tests: {e}")
            return False
    
    def setup_flat_file_mode(self):
        """Set up system for flat file mode"""
        print("\n🔧 Setting up Flat File Mode")
        print("=" * 40)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing core dependencies", lambda: self.install_dependencies(False)),
            ("Creating .env file", self.create_env_file),
            ("Checking configuration files", self.check_config_files),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        print("\n🎉 Flat File Mode setup complete!")
        print("\nNext steps:")
        print("1. Activate virtual environment:")
        if os.name == 'nt':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("2. Start the server:")
        print("   python server.py")
        print("3. Connect via terminal: nc localhost 8888")
        print("4. Connect via web: http://localhost:5000")
        
        return True
    
    def setup_database_mode(self):
        """Set up system for database mode"""
        print("\n🔧 Setting up Database Mode")
        print("=" * 40)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing all dependencies", lambda: self.install_dependencies(True)),
            ("Creating .env file", self.create_env_file),
            ("Checking configuration files", self.check_config_files),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        print("\n🎉 Database Mode setup complete!")
        print("\nNext steps:")
        print("1. Set up MongoDB and Redis (see DEPLOYMENT.md)")
        print("2. Edit .env file with database settings")
        print("3. Set USE_DATABASE=true in .env")
        print("4. Run migration: python migrate_v2.py migrate")
        print("5. Start the server: python server_v2.py")
        
        return True
    
    def show_status(self):
        """Show current system status"""
        print("\n📊 System Status")
        print("=" * 30)
        
        # Check virtual environment
        venv_status = "✅ Exists" if self.venv_dir.exists() else "❌ Missing"
        print(f"Virtual Environment: {venv_status}")
        
        # Check .env file
        env_status = "✅ Exists" if Path(".env").exists() else "❌ Missing"
        print(f".env Configuration: {env_status}")
        
        # Check configuration files
        config_files = ['rooms.yaml', 'bots.yaml', 'items.yaml', 'scripts.yaml']
        config_count = sum(1 for f in config_files if Path(f).exists())
        config_status = f"✅ {config_count}/{len(config_files)}" if config_count == len(config_files) else f"⚠️  {config_count}/{len(config_files)}"
        print(f"Configuration Files: {config_status}")
        
        # Check backend mode
        try:
            if Path(".env").exists():
                with open(".env", "r") as f:
                    env_content = f.read()
                    if "USE_DATABASE=true" in env_content:
                        backend = "Database"
                    else:
                        backend = "Flat Files"
            else:
                backend = "Unknown"
        except:
            backend = "Unknown"
        
        print(f"Backend Mode: {backend}")
        
        # Check if servers are running
        import socket
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                return result == 0
            except:
                return False
        
        tcp_status = "✅ Running" if check_port(8888) else "❌ Not Running"
        web_status = "✅ Running" if check_port(5000) else "❌ Not Running"
        
        print(f"TCP Server (8888): {tcp_status}")
        print(f"Web Server (5000): {web_status}")

def main():
    parser = argparse.ArgumentParser(description='Setup and management for Text Space System')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup commands
    subparsers.add_parser('setup-flat', help='Set up for flat file mode')
    subparsers.add_parser('setup-db', help='Set up for database mode')
    
    # Management commands
    subparsers.add_parser('status', help='Show system status')
    subparsers.add_parser('test', help='Run test suite')
    
    # Quick start
    subparsers.add_parser('start', help='Start the server (auto-detect mode)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\nQuick start:")
        print("  python setup.py setup-flat    # Set up flat file mode")
        print("  python setup.py setup-db      # Set up database mode")
        print("  python setup.py status        # Check system status")
        return
    
    setup = TextSpaceSetup()
    
    try:
        if args.command == 'setup-flat':
            setup.setup_flat_file_mode()
        elif args.command == 'setup-db':
            setup.setup_database_mode()
        elif args.command == 'status':
            setup.show_status()
        elif args.command == 'test':
            setup.run_tests()
        elif args.command == 'start':
            # Auto-detect mode and start appropriate server
            if Path(".env").exists():
                with open(".env", "r") as f:
                    if "USE_DATABASE=true" in f.read():
                        print("Starting database mode server...")
                        os.system("python server_v2.py")
                    else:
                        print("Starting flat file mode server...")
                        os.system("python server.py")
            else:
                print("Starting default server...")
                os.system("python server.py")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
