#!/usr/bin/env python3
"""
Admin management tool for Multi-User Text Space System
Provides command-line interface for administrative tasks
"""
import asyncio
import json
import yaml
import os
import sys
from datetime import datetime
import argparse

# Try to import database modules
try:
    from database import DatabaseManager, UserRepository
    from auth import AuthenticationService
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

class AdminTool:
    def __init__(self, use_database=None):
        if use_database is None:
            use_database = DATABASE_AVAILABLE and os.getenv('USE_DATABASE', 'false').lower() == 'true'
        
        self.use_database = use_database
        
        if self.use_database:
            if not DATABASE_AVAILABLE:
                raise Exception("Database modules not available")
            self.db_manager = DatabaseManager()
            self.user_repo = UserRepository(self.db_manager)
            self.auth_service = AuthenticationService(self.db_manager)
        else:
            self.user_data_file = "users.json"
    
    async def list_users(self):
        """List all users"""
        if self.use_database:
            users = await self.user_repo.get_all_users()
            print(f"Database Users ({len(users)}):")
            for user in users:
                admin_flag = " [ADMIN]" if user.get('admin', False) else ""
                last_seen = user.get('last_seen', 'Never')
                print(f"  {user['name']}{admin_flag} - Last seen: {last_seen}")
        else:
            try:
                with open(self.user_data_file, 'r') as f:
                    users = json.load(f)
                print(f"Flat File Users ({len(users)}):")
                for username, data in users.items():
                    admin_flag = " [ADMIN]" if data.get('admin', False) else ""
                    room = data.get('room_id', 'lobby')
                    print(f"  {username}{admin_flag} - Room: {room}")
            except FileNotFoundError:
                print("No users found")
    
    async def promote_user(self, username):
        """Promote user to admin"""
        if self.use_database:
            user_data = await self.user_repo.get_user(username)
            if not user_data:
                print(f"User '{username}' not found")
                return False
            
            user_data['admin'] = True
            await self.user_repo.save_user(user_data)
            print(f"User '{username}' promoted to admin")
            return True
        else:
            try:
                with open(self.user_data_file, 'r') as f:
                    users = json.load(f)
                
                if username not in users:
                    print(f"User '{username}' not found")
                    return False
                
                users[username]['admin'] = True
                
                with open(self.user_data_file, 'w') as f:
                    json.dump(users, f, indent=2)
                
                print(f"User '{username}' promoted to admin")
                return True
            except FileNotFoundError:
                print("No users file found")
                return False
    
    async def demote_user(self, username):
        """Demote user from admin"""
        if username == "admin":
            print("Cannot demote the 'admin' user")
            return False
        
        if self.use_database:
            user_data = await self.user_repo.get_user(username)
            if not user_data:
                print(f"User '{username}' not found")
                return False
            
            user_data['admin'] = False
            await self.user_repo.save_user(user_data)
            print(f"User '{username}' demoted from admin")
            return True
        else:
            try:
                with open(self.user_data_file, 'r') as f:
                    users = json.load(f)
                
                if username not in users:
                    print(f"User '{username}' not found")
                    return False
                
                users[username]['admin'] = False
                
                with open(self.user_data_file, 'w') as f:
                    json.dump(users, f, indent=2)
                
                print(f"User '{username}' demoted from admin")
                return True
            except FileNotFoundError:
                print("No users file found")
                return False
    
    async def reset_user_location(self, username, room_id='lobby'):
        """Reset user location to specified room"""
        if self.use_database:
            user_data = await self.user_repo.get_user(username)
            if not user_data:
                print(f"User '{username}' not found")
                return False
            
            user_data['room_id'] = room_id
            await self.user_repo.save_user(user_data)
            print(f"User '{username}' location reset to '{room_id}'")
            return True
        else:
            try:
                with open(self.user_data_file, 'r') as f:
                    users = json.load(f)
                
                if username not in users:
                    print(f"User '{username}' not found")
                    return False
                
                users[username]['room_id'] = room_id
                
                with open(self.user_data_file, 'w') as f:
                    json.dump(users, f, indent=2)
                
                print(f"User '{username}' location reset to '{room_id}'")
                return True
            except FileNotFoundError:
                print("No users file found")
                return False
    
    async def clear_user_inventory(self, username):
        """Clear user's inventory"""
        if self.use_database:
            user_data = await self.user_repo.get_user(username)
            if not user_data:
                print(f"User '{username}' not found")
                return False
            
            user_data['inventory'] = []
            await self.user_repo.save_user(user_data)
            print(f"User '{username}' inventory cleared")
            return True
        else:
            try:
                with open(self.user_data_file, 'r') as f:
                    users = json.load(f)
                
                if username not in users:
                    print(f"User '{username}' not found")
                    return False
                
                users[username]['inventory'] = []
                
                with open(self.user_data_file, 'w') as f:
                    json.dump(users, f, indent=2)
                
                print(f"User '{username}' inventory cleared")
                return True
            except FileNotFoundError:
                print("No users file found")
                return False
    
    async def create_user(self, username, password=None, admin=False):
        """Create a new user"""
        if self.use_database:
            if not password:
                password = f"{username}123"
            
            try:
                # Create authentication
                self.auth_service.create_user(username, password, admin)
                
                # Create user data
                user_data = {
                    'name': username,
                    'room_id': 'lobby',
                    'inventory': [],
                    'admin': admin,
                    'created_at': datetime.utcnow(),
                    'last_seen': datetime.utcnow()
                }
                
                await self.user_repo.save_user(user_data)
                print(f"User '{username}' created (password: {password})")
                return True
            except Exception as e:
                print(f"Error creating user: {e}")
                return False
        else:
            try:
                with open(self.user_data_file, 'r') as f:
                    users = json.load(f)
            except FileNotFoundError:
                users = {}
            
            if username in users:
                print(f"User '{username}' already exists")
                return False
            
            users[username] = {
                'room_id': 'lobby',
                'inventory': [],
                'admin': admin
            }
            
            with open(self.user_data_file, 'w') as f:
                json.dump(users, f, indent=2)
            
            print(f"User '{username}' created")
            return True
    
    def show_system_info(self):
        """Show system information"""
        print("Multi-User Text Space System - Admin Tool")
        print("=" * 50)
        print(f"Backend: {'Database' if self.use_database else 'Flat Files'}")
        
        if self.use_database:
            if DATABASE_AVAILABLE:
                try:
                    if self.db_manager.test_connections():
                        print("Database Status: ✅ Connected")
                    else:
                        print("Database Status: ❌ Connection Failed")
                except Exception as e:
                    print(f"Database Status: ❌ Error - {e}")
            else:
                print("Database Status: ❌ Modules Not Available")
        
        # Check configuration files
        config_files = ['rooms.yaml', 'bots.yaml', 'items.yaml', 'scripts.yaml']
        print("\nConfiguration Files:")
        for filename in config_files:
            status = "✅" if os.path.exists(filename) else "❌"
            print(f"  {filename}: {status}")
        
        # Check user data
        if not self.use_database:
            user_status = "✅" if os.path.exists(self.user_data_file) else "❌"
            print(f"  {self.user_data_file}: {user_status}")

async def main():
    parser = argparse.ArgumentParser(description='Admin tool for Text Space System')
    parser.add_argument('--database', action='store_true', help='Use database backend')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List users
    subparsers.add_parser('list', help='List all users')
    
    # Promote user
    promote_parser = subparsers.add_parser('promote', help='Promote user to admin')
    promote_parser.add_argument('username', help='Username to promote')
    
    # Demote user
    demote_parser = subparsers.add_parser('demote', help='Demote user from admin')
    demote_parser.add_argument('username', help='Username to demote')
    
    # Reset location
    reset_parser = subparsers.add_parser('reset-location', help='Reset user location')
    reset_parser.add_argument('username', help='Username')
    reset_parser.add_argument('--room', default='lobby', help='Room ID (default: lobby)')
    
    # Clear inventory
    clear_parser = subparsers.add_parser('clear-inventory', help='Clear user inventory')
    clear_parser.add_argument('username', help='Username')
    
    # Create user
    create_parser = subparsers.add_parser('create', help='Create new user')
    create_parser.add_argument('username', help='Username')
    create_parser.add_argument('--password', help='Password (default: username123)')
    create_parser.add_argument('--admin', action='store_true', help='Make user admin')
    
    # System info
    subparsers.add_parser('info', help='Show system information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        admin_tool = AdminTool(use_database=args.database)
        
        if args.command == 'list':
            await admin_tool.list_users()
        elif args.command == 'promote':
            await admin_tool.promote_user(args.username)
        elif args.command == 'demote':
            await admin_tool.demote_user(args.username)
        elif args.command == 'reset-location':
            await admin_tool.reset_user_location(args.username, args.room)
        elif args.command == 'clear-inventory':
            await admin_tool.clear_user_inventory(args.username)
        elif args.command == 'create':
            await admin_tool.create_user(args.username, args.password, args.admin)
        elif args.command == 'info':
            admin_tool.show_system_info()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
