#!/usr/bin/env python3
"""
Enhanced Migration tool to convert flat files to database
Supports both one-time migration and parallel operation
"""
import json
import yaml
import asyncio
import os
from datetime import datetime

# Try to import database modules
try:
    from database import DatabaseManager, UserRepository, RoomRepository, ItemRepository
    from auth import AuthenticationService
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("WARNING: Database modules not available. Install dependencies first:")
    print("pip install pymongo redis bcrypt python-dotenv")

class MigrationTool:
    def __init__(self):
        if not DATABASE_AVAILABLE:
            raise Exception("Database modules not available")
        
        self.db_manager = DatabaseManager()
        self.user_repo = UserRepository(self.db_manager)
        self.room_repo = RoomRepository(self.db_manager)
        self.item_repo = ItemRepository(self.db_manager)
        self.auth_service = AuthenticationService(self.db_manager)
    
    async def backup_flat_files(self):
        """Create backup of flat files before migration"""
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_{timestamp}"
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            files_to_backup = ['users.json', 'rooms.yaml', 'bots.yaml', 'items.yaml', 'scripts.yaml']
            backed_up = 0
            
            for filename in files_to_backup:
                if os.path.exists(filename):
                    shutil.copy2(filename, os.path.join(backup_dir, filename))
                    backed_up += 1
            
            print(f"Backed up {backed_up} files to {backup_dir}/")
            return backup_dir
            
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return None
    
    async def migrate_users(self):
        """Migrate users from users.json to database"""
        try:
            with open('users.json', 'r') as f:
                users_data = json.load(f)
            
            migrated = 0
            for username, user_data in users_data.items():
                # Check if user already exists
                existing_user = await self.user_repo.get_user(username)
                if existing_user:
                    print(f"User {username} already exists in database, skipping")
                    continue
                
                # Create user document
                user_doc = {
                    'name': username,
                    'room_id': user_data.get('room_id', 'lobby'),
                    'inventory': user_data.get('inventory', []),
                    'admin': user_data.get('admin', False),
                    'created_at': datetime.utcnow(),
                    'last_seen': datetime.utcnow()
                }
                
                await self.user_repo.save_user(user_doc)
                
                # Create authentication entry with default password
                default_password = f"{username}123"  # Users should change this
                try:
                    self.auth_service.create_user(username, default_password, user_data.get('admin', False))
                    print(f"Migrated user: {username} (default password: {default_password})")
                except Exception as e:
                    print(f"Warning: Could not create auth for {username}: {e}")
                
                migrated += 1
            
            print(f"Successfully migrated {migrated} users")
            
        except FileNotFoundError:
            print("No users.json file found")
        except Exception as e:
            print(f"Error migrating users: {e}")
    
    async def migrate_rooms(self):
        """Migrate rooms from rooms.yaml to database"""
        try:
            with open('rooms.yaml', 'r') as f:
                rooms_data = yaml.safe_load(f)
            
            migrated = 0
            for room_id, room_data in rooms_data['rooms'].items():
                # Check if room already exists
                existing_room = await self.room_repo.get_room(room_id)
                if existing_room:
                    print(f"Room {room_id} already exists in database, skipping")
                    continue
                
                room_doc = {
                    '_id': room_id,
                    'name': room_data['name'],
                    'description': room_data['description'],
                    'exits': room_data.get('exits', {}),
                    'items': room_data.get('items', []),
                    'created_at': datetime.utcnow()
                }
                
                await self.room_repo.save_room(room_doc)
                migrated += 1
                print(f"Migrated room: {room_id}")
            
            print(f"Successfully migrated {migrated} rooms")
            
        except FileNotFoundError:
            print("No rooms.yaml file found")
        except Exception as e:
            print(f"Error migrating rooms: {e}")
    
    async def migrate_items(self):
        """Migrate items from items.yaml to database"""
        try:
            with open('items.yaml', 'r') as f:
                items_data = yaml.safe_load(f)
            
            migrated = 0
            for item_id, item_data in items_data['items'].items():
                # Check if item already exists
                existing_item = await self.item_repo.get_item(item_id)
                if existing_item:
                    print(f"Item {item_id} already exists in database, skipping")
                    continue
                
                item_doc = {
                    '_id': item_id,
                    'name': item_data['name'],
                    'description': item_data['description'],
                    'tags': item_data.get('tags', []),
                    'is_container': item_data.get('is_container', False),
                    'contents': item_data.get('contents', []),
                    'script': item_data.get('script'),
                    'created_at': datetime.utcnow()
                }
                
                await self.item_repo.save_item(item_doc)
                migrated += 1
                print(f"Migrated item: {item_id}")
            
            print(f"Successfully migrated {migrated} items")
            
        except FileNotFoundError:
            print("No items.yaml file found")
        except Exception as e:
            print(f"Error migrating items: {e}")
    
    async def migrate_bots(self):
        """Migrate bots from bots.yaml to database"""
        try:
            with open('bots.yaml', 'r') as f:
                bots_data = yaml.safe_load(f)
            
            migrated = 0
            for bot_id, bot_data in bots_data['bots'].items():
                # Check if bot already exists
                existing_bot = await self.db_manager.bots.find_one({'_id': bot_id})
                if existing_bot:
                    print(f"Bot {bot_id} already exists in database, skipping")
                    continue
                
                bot_doc = {
                    '_id': bot_id,
                    'name': bot_data['name'],
                    'room_id': bot_data['room'],
                    'description': bot_data['description'],
                    'responses': bot_data.get('responses', []),
                    'visible': bot_data.get('visible', True),
                    'inventory': bot_data.get('inventory', []),
                    'created_at': datetime.utcnow()
                }
                
                # Insert directly into MongoDB
                await self.db_manager.bots.replace_one(
                    {'_id': bot_id}, bot_doc, upsert=True
                )
                migrated += 1
                print(f"Migrated bot: {bot_id}")
            
            print(f"Successfully migrated {migrated} bots")
            
        except FileNotFoundError:
            print("No bots.yaml file found")
        except Exception as e:
            print(f"Error migrating bots: {e}")
    
    async def verify_migration(self):
        """Verify that migration was successful"""
        print("\nVerifying migration...")
        
        try:
            # Count records in database
            users_count = await self.db_manager.users.count_documents({})
            rooms_count = await self.db_manager.rooms.count_documents({})
            items_count = await self.db_manager.items.count_documents({})
            bots_count = await self.db_manager.bots.count_documents({})
            
            print(f"Database contains:")
            print(f"  Users: {users_count}")
            print(f"  Rooms: {rooms_count}")
            print(f"  Items: {items_count}")
            print(f"  Bots: {bots_count}")
            
            # Count records in flat files
            flat_counts = {}
            
            try:
                with open('users.json', 'r') as f:
                    flat_counts['users'] = len(json.load(f))
            except:
                flat_counts['users'] = 0
            
            try:
                with open('rooms.yaml', 'r') as f:
                    flat_counts['rooms'] = len(yaml.safe_load(f)['rooms'])
            except:
                flat_counts['rooms'] = 0
            
            try:
                with open('items.yaml', 'r') as f:
                    flat_counts['items'] = len(yaml.safe_load(f)['items'])
            except:
                flat_counts['items'] = 0
            
            try:
                with open('bots.yaml', 'r') as f:
                    flat_counts['bots'] = len(yaml.safe_load(f)['bots'])
            except:
                flat_counts['bots'] = 0
            
            print(f"Flat files contain:")
            print(f"  Users: {flat_counts['users']}")
            print(f"  Rooms: {flat_counts['rooms']}")
            print(f"  Items: {flat_counts['items']}")
            print(f"  Bots: {flat_counts['bots']}")
            
            # Check for discrepancies
            if (users_count >= flat_counts['users'] and 
                rooms_count >= flat_counts['rooms'] and
                items_count >= flat_counts['items'] and
                bots_count >= flat_counts['bots']):
                print("\n✅ Migration verification successful!")
                return True
            else:
                print("\n❌ Migration verification failed - some data may be missing")
                return False
                
        except Exception as e:
            print(f"Error during verification: {e}")
            return False
    
    async def run_migration(self, create_backup=True):
        """Run complete migration"""
        print("Starting migration from flat files to database...")
        
        # Test database connection
        if not self.db_manager.test_connections():
            print("ERROR: Cannot connect to database. Please check your configuration.")
            print("Make sure MongoDB and Redis are running and .env is configured correctly.")
            return False
        
        print("✅ Database connection successful")
        
        # Create backup
        if create_backup:
            backup_dir = await self.backup_flat_files()
            if backup_dir:
                print(f"✅ Backup created: {backup_dir}")
        
        # Run migrations
        print("\nMigrating data...")
        await self.migrate_rooms()
        await self.migrate_items()
        await self.migrate_bots()
        await self.migrate_users()
        
        # Verify migration
        success = await self.verify_migration()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Set USE_DATABASE=true in your .env file")
            print("2. Test the server with: python server_v2.py")
            print("3. Users will need to use their default passwords (username123)")
            print("4. Consider implementing password reset functionality")
        else:
            print("\n⚠️  Migration completed with warnings. Please review the output above.")
        
        return success

class ParallelOperationTool:
    """Tool to run both flat file and database systems in parallel"""
    
    def __init__(self):
        if not DATABASE_AVAILABLE:
            raise Exception("Database modules not available")
        
        self.db_manager = DatabaseManager()
        self.user_repo = UserRepository(self.db_manager)
    
    async def sync_user_data(self, username, user_data):
        """Sync user data from flat file system to database"""
        try:
            db_user_data = {
                'name': username,
                'room_id': user_data.get('room_id', 'lobby'),
                'inventory': user_data.get('inventory', []),
                'admin': user_data.get('admin', False),
                'last_seen': datetime.utcnow()
            }
            
            await self.user_repo.save_user(db_user_data)
            print(f"Synced user data for: {username}")
            
        except Exception as e:
            print(f"Error syncing user {username}: {e}")
    
    async def run_parallel_sync(self):
        """Run continuous sync between flat files and database"""
        print("Starting parallel operation sync...")
        
        if not self.db_manager.test_connections():
            print("ERROR: Cannot connect to database")
            return
        
        print("Database connection successful")
        print("Monitoring users.json for changes...")
        
        last_modified = 0
        
        while True:
            try:
                # Check if users.json has been modified
                if os.path.exists('users.json'):
                    current_modified = os.path.getmtime('users.json')
                    
                    if current_modified > last_modified:
                        print("Detected changes in users.json, syncing...")
                        
                        with open('users.json', 'r') as f:
                            users_data = json.load(f)
                        
                        for username, user_data in users_data.items():
                            await self.sync_user_data(username, user_data)
                        
                        last_modified = current_modified
                        print("Sync completed")
                
                # Wait before checking again
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                print("\nStopping parallel sync...")
                break
            except Exception as e:
                print(f"Error in parallel sync: {e}")
                await asyncio.sleep(10)

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration and sync tool for Text Space')
    parser.add_argument('command', choices=['migrate', 'sync', 'verify'], 
                       help='Command to run')
    parser.add_argument('--no-backup', action='store_true', 
                       help='Skip creating backup during migration')
    
    args = parser.parse_args()
    
    if not DATABASE_AVAILABLE:
        print("ERROR: Database modules not available")
        print("Install dependencies: pip install pymongo redis bcrypt python-dotenv")
        return
    
    if args.command == 'migrate':
        migration = MigrationTool()
        await migration.run_migration(create_backup=not args.no_backup)
    
    elif args.command == 'sync':
        sync_tool = ParallelOperationTool()
        await sync_tool.run_parallel_sync()
    
    elif args.command == 'verify':
        migration = MigrationTool()
        await migration.verify_migration()

if __name__ == "__main__":
    asyncio.run(main())
