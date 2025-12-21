#!/usr/bin/env python
"""
Monitoring and health check tool for Multi-User Text Space System
"""
import asyncio
import json
import yaml
import os
import time
import socket
import psutil
from datetime import datetime, timedelta
import argparse

# Try to import database modules
try:
    from database import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

class HealthMonitor:
    def __init__(self, use_database=None):
        if use_database is None:
            use_database = DATABASE_AVAILABLE and os.getenv('USE_DATABASE', 'false').lower() == 'true'
        
        self.use_database = use_database
        
        if self.use_database and DATABASE_AVAILABLE:
            self.db_manager = DatabaseManager()
    
    def check_tcp_port(self, host='localhost', port=8888):
        """Check if TCP server is running"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def check_web_port(self, host='localhost', port=5000):
        """Check if web server is running"""
        return self.check_tcp_port(host, port)
    
    def check_config_files(self):
        """Check configuration files"""
        required_files = ['rooms.yaml', 'bots.yaml', 'items.yaml', 'scripts.yaml']
        results = {}
        
        for filename in required_files:
            try:
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        yaml.safe_load(f)
                    results[filename] = {'status': 'ok', 'error': None}
                else:
                    results[filename] = {'status': 'missing', 'error': 'File not found'}
            except yaml.YAMLError as e:
                results[filename] = {'status': 'error', 'error': f'YAML error: {e}'}
            except Exception as e:
                results[filename] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def check_user_data(self):
        """Check user data file"""
        if self.use_database:
            return {'status': 'database', 'error': None}
        
        try:
            if os.path.exists('users.json'):
                with open('users.json', 'r') as f:
                    data = json.load(f)
                return {'status': 'ok', 'count': len(data), 'error': None}
            else:
                return {'status': 'missing', 'error': 'users.json not found'}
        except json.JSONDecodeError as e:
            return {'status': 'error', 'error': f'JSON error: {e}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def check_database(self):
        """Check database connectivity"""
        if not self.use_database or not DATABASE_AVAILABLE:
            return {'status': 'disabled', 'error': None}
        
        try:
            if self.db_manager.test_connections():
                # Get collection counts
                users_count = await self.db_manager.users.count_documents({})
                rooms_count = await self.db_manager.rooms.count_documents({})
                items_count = await self.db_manager.items.count_documents({})
                bots_count = await self.db_manager.bots.count_documents({})
                
                return {
                    'status': 'ok',
                    'counts': {
                        'users': users_count,
                        'rooms': rooms_count,
                        'items': items_count,
                        'bots': bots_count
                    },
                    'error': None
                }
            else:
                return {'status': 'error', 'error': 'Connection failed'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_log_file(self):
        """Check log file"""
        log_file = 'textspace.log'
        
        try:
            if os.path.exists(log_file):
                stat = os.stat(log_file)
                size_mb = stat.st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                # Check for recent activity (last 5 minutes)
                recent_activity = datetime.now() - modified < timedelta(minutes=5)
                
                return {
                    'status': 'ok',
                    'size_mb': round(size_mb, 2),
                    'last_modified': modified.isoformat(),
                    'recent_activity': recent_activity,
                    'error': None
                }
            else:
                return {'status': 'missing', 'error': 'Log file not found'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_system_resources(self):
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            return {
                'status': 'ok',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'error': None
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def run_health_check(self):
        """Run complete health check"""
        print("Multi-User Text Space System - Health Check")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Backend: {'Database' if self.use_database else 'Flat Files'}")
        print()
        
        # Check servers
        print("🌐 Server Status:")
        tcp_status = "✅ Running" if self.check_tcp_port() else "❌ Not Running"
        web_status = "✅ Running" if self.check_web_port() else "❌ Not Running"
        print(f"  TCP Server (8888): {tcp_status}")
        print(f"  Web Server (5000): {web_status}")
        print()
        
        # Check configuration files
        print("📁 Configuration Files:")
        config_results = self.check_config_files()
        for filename, result in config_results.items():
            if result['status'] == 'ok':
                print(f"  {filename}: ✅ OK")
            else:
                print(f"  {filename}: ❌ {result['error']}")
        print()
        
        # Check user data
        print("👥 User Data:")
        user_result = self.check_user_data()
        if user_result['status'] == 'ok':
            print(f"  users.json: ✅ OK ({user_result['count']} users)")
        elif user_result['status'] == 'database':
            print("  Using database backend")
        else:
            print(f"  users.json: ❌ {user_result['error']}")
        print()
        
        # Check database
        if self.use_database:
            print("🗄️  Database:")
            db_result = await self.check_database()
            if db_result['status'] == 'ok':
                counts = db_result['counts']
                print(f"  MongoDB: ✅ Connected")
                print(f"    Users: {counts['users']}")
                print(f"    Rooms: {counts['rooms']}")
                print(f"    Items: {counts['items']}")
                print(f"    Bots: {counts['bots']}")
            else:
                print(f"  Database: ❌ {db_result['error']}")
            print()
        
        # Check log file
        print("📝 Log File:")
        log_result = self.check_log_file()
        if log_result['status'] == 'ok':
            activity = "✅ Active" if log_result['recent_activity'] else "⚠️  Inactive"
            print(f"  textspace.log: ✅ OK ({log_result['size_mb']} MB, {activity})")
        else:
            print(f"  textspace.log: ❌ {log_result['error']}")
        print()
        
        # Check system resources
        print("💻 System Resources:")
        sys_result = self.check_system_resources()
        if sys_result['status'] == 'ok':
            cpu_status = "✅" if sys_result['cpu_percent'] < 80 else "⚠️"
            mem_status = "✅" if sys_result['memory_percent'] < 80 else "⚠️"
            disk_status = "✅" if sys_result['disk_percent'] < 90 else "⚠️"
            
            print(f"  CPU Usage: {cpu_status} {sys_result['cpu_percent']:.1f}%")
            print(f"  Memory Usage: {mem_status} {sys_result['memory_percent']:.1f}% ({sys_result['memory_available_gb']} GB free)")
            print(f"  Disk Usage: {disk_status} {sys_result['disk_percent']:.1f}% ({sys_result['disk_free_gb']} GB free)")
        else:
            print(f"  System Resources: ❌ {sys_result['error']}")
        print()
        
        # Overall status
        all_good = (
            self.check_tcp_port() and
            all(r['status'] == 'ok' for r in config_results.values()) and
            user_result['status'] in ['ok', 'database']
        )
        
        if self.use_database:
            db_result = await self.check_database()
            all_good = all_good and db_result['status'] == 'ok'
        
        print("🎯 Overall Status:")
        if all_good:
            print("  ✅ System is healthy")
        else:
            print("  ⚠️  System has issues - check details above")
        
        return all_good
    
    async def monitor_continuous(self, interval=60):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running health check...")
                
                # Quick check
                tcp_ok = self.check_tcp_port()
                web_ok = self.check_web_port()
                
                if self.use_database and DATABASE_AVAILABLE:
                    try:
                        db_ok = self.db_manager.test_connections()
                    except:
                        db_ok = False
                else:
                    db_ok = True  # Not using database
                
                if tcp_ok and web_ok and db_ok:
                    print("✅ All services running")
                else:
                    print("❌ Service issues detected:")
                    if not tcp_ok:
                        print("  - TCP server not responding")
                    if not web_ok:
                        print("  - Web server not responding")
                    if not db_ok:
                        print("  - Database connection failed")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")

async def main():
    parser = argparse.ArgumentParser(description='Health monitoring for Text Space System')
    parser.add_argument('--database', action='store_true', help='Use database backend')
    parser.add_argument('--monitor', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    try:
        monitor = HealthMonitor(use_database=args.database)
        
        if args.monitor:
            await monitor.monitor_continuous(args.interval)
        else:
            await monitor.run_health_check()
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
