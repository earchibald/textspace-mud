#!/usr/bin/env python3
"""
Backup and restore tool for Multi-User Text Space System
"""
import asyncio
import json
import yaml
import os
import shutil
import tarfile
import argparse
from datetime import datetime
import tempfile

# Try to import database modules
try:
    from database import DatabaseManager, UserRepository, RoomRepository, ItemRepository
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

class BackupTool:
    def __init__(self, use_database=None):
        if use_database is None:
            use_database = DATABASE_AVAILABLE and os.getenv('USE_DATABASE', 'false').lower() == 'true'
        
        self.use_database = use_database
        
        if self.use_database and DATABASE_AVAILABLE:
            self.db_manager = DatabaseManager()
            self.user_repo = UserRepository(self.db_manager)
            self.room_repo = RoomRepository(self.db_manager)
            self.item_repo = ItemRepository(self.db_manager)
    
    def create_flat_file_backup(self, backup_dir):
        """Create backup of flat files"""
        files_to_backup = [
            'rooms.yaml', 'bots.yaml', 'items.yaml', 'scripts.yaml', 
            'users.json', 'textspace.log'
        ]
        
        backed_up = []
        
        for filename in files_to_backup:
            if os.path.exists(filename):
                dest_path = os.path.join(backup_dir, filename)
                shutil.copy2(filename, dest_path)
                backed_up.append(filename)
        
        # Copy templates directory if it exists
        if os.path.exists('templates'):
            dest_templates = os.path.join(backup_dir, 'templates')
            shutil.copytree('templates', dest_templates)
            backed_up.append('templates/')
        
        return backed_up
    
    async def create_database_backup(self, backup_dir):
        """Create backup of database data"""
        if not self.use_database or not DATABASE_AVAILABLE:
            return []
        
        try:
            backed_up = []
            
            # Export users
            users = await self.user_repo.get_all_users()
            users_file = os.path.join(backup_dir, 'users_export.json')
            with open(users_file, 'w') as f:
                json.dump(users, f, indent=2, default=str)
            backed_up.append('users_export.json')
            
            # Export rooms
            rooms = await self.room_repo.get_all_rooms()
            rooms_file = os.path.join(backup_dir, 'rooms_export.json')
            with open(rooms_file, 'w') as f:
                json.dump(rooms, f, indent=2, default=str)
            backed_up.append('rooms_export.json')
            
            # Export items
            items = await self.item_repo.get_all_items()
            items_file = os.path.join(backup_dir, 'items_export.json')
            with open(items_file, 'w') as f:
                json.dump(items, f, indent=2, default=str)
            backed_up.append('items_export.json')
            
            # Export bots
            bots = list(await self.db_manager.bots.find({}).to_list(None))
            bots_file = os.path.join(backup_dir, 'bots_export.json')
            with open(bots_file, 'w') as f:
                json.dump(bots, f, indent=2, default=str)
            backed_up.append('bots_export.json')
            
            return backed_up
            
        except Exception as e:
            print(f"Error creating database backup: {e}")
            return []
    
    async def create_backup(self, backup_name=None):
        """Create complete system backup"""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"textspace_backup_{timestamp}"
        
        backup_dir = backup_name
        
        try:
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)
            
            print(f"Creating backup: {backup_name}")
            
            # Backup flat files
            print("Backing up configuration files...")
            flat_files = self.create_flat_file_backup(backup_dir)
            
            # Backup database if using it
            if self.use_database:
                print("Backing up database data...")
                db_files = await self.create_database_backup(backup_dir)
            else:
                db_files = []
            
            # Create backup manifest
            manifest = {
                'created': datetime.now().isoformat(),
                'backend': 'database' if self.use_database else 'flat_files',
                'files': {
                    'flat_files': flat_files,
                    'database_exports': db_files
                }
            }
            
            manifest_file = os.path.join(backup_dir, 'backup_manifest.json')
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create compressed archive
            archive_name = f"{backup_name}.tar.gz"
            with tarfile.open(archive_name, 'w:gz') as tar:
                tar.add(backup_dir, arcname=backup_name)
            
            # Clean up temporary directory
            shutil.rmtree(backup_dir)
            
            print(f"✅ Backup created: {archive_name}")
            print(f"   Files backed up: {len(flat_files + db_files)}")
            
            return archive_name
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            return None
    
    async def restore_backup(self, backup_file, force=False):
        """Restore from backup"""
        if not os.path.exists(backup_file):
            print(f"Backup file not found: {backup_file}")
            return False
        
        # Extract backup
        temp_dir = tempfile.mkdtemp()
        
        try:
            print(f"Restoring from: {backup_file}")
            
            # Extract archive
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Find backup directory (should be only one)
            backup_dirs = [d for d in os.listdir(temp_dir) 
                          if os.path.isdir(os.path.join(temp_dir, d))]
            
            if not backup_dirs:
                print("No backup directory found in archive")
                return False
            
            backup_dir = os.path.join(temp_dir, backup_dirs[0])
            
            # Read manifest
            manifest_file = os.path.join(backup_dir, 'backup_manifest.json')
            if os.path.exists(manifest_file):
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                print(f"Backup created: {manifest['created']}")
                print(f"Backup backend: {manifest['backend']}")
            else:
                print("Warning: No backup manifest found")
                manifest = None
            
            # Check if we should proceed
            if not force:
                response = input("This will overwrite existing data. Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Restore cancelled")
                    return False
            
            # Restore flat files
            print("Restoring configuration files...")
            restored_files = []
            
            config_files = ['rooms.yaml', 'bots.yaml', 'items.yaml', 'scripts.yaml']
            for filename in config_files:
                src_path = os.path.join(backup_dir, filename)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, filename)
                    restored_files.append(filename)
                    print(f"  Restored: {filename}")
            
            # Restore users.json if not using database
            if not self.use_database:
                users_file = os.path.join(backup_dir, 'users.json')
                if os.path.exists(users_file):
                    shutil.copy2(users_file, 'users.json')
                    restored_files.append('users.json')
                    print(f"  Restored: users.json")
            
            # Restore templates
            templates_dir = os.path.join(backup_dir, 'templates')
            if os.path.exists(templates_dir):
                if os.path.exists('templates'):
                    shutil.rmtree('templates')
                shutil.copytree(templates_dir, 'templates')
                restored_files.append('templates/')
                print(f"  Restored: templates/")
            
            # Restore database data if using database
            if self.use_database and DATABASE_AVAILABLE:
                print("Restoring database data...")
                
                # Note: This would require implementing database restore
                # For now, we'll just mention it
                print("  Database restore not yet implemented")
                print("  Use migration tools to import exported data")
            
            print(f"✅ Restore completed")
            print(f"   Files restored: {len(restored_files)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
        
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def list_backups(self, backup_dir='.'):
        """List available backups"""
        backup_files = [f for f in os.listdir(backup_dir) 
                       if f.startswith('textspace_backup_') and f.endswith('.tar.gz')]
        
        if not backup_files:
            print("No backups found")
            return
        
        print("Available backups:")
        for backup_file in sorted(backup_files):
            file_path = os.path.join(backup_dir, backup_file)
            stat = os.stat(file_path)
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            print(f"  {backup_file}")
            print(f"    Size: {size_mb:.1f} MB")
            print(f"    Created: {modified.strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    parser = argparse.ArgumentParser(description='Backup and restore tool for Text Space System')
    parser.add_argument('--database', action='store_true', help='Use database backend')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create backup
    backup_parser = subparsers.add_parser('create', help='Create backup')
    backup_parser.add_argument('--name', help='Backup name (default: auto-generated)')
    
    # Restore backup
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_file', help='Backup file to restore')
    restore_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # List backups
    list_parser = subparsers.add_parser('list', help='List available backups')
    list_parser.add_argument('--dir', default='.', help='Directory to search for backups')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        backup_tool = BackupTool(use_database=args.database)
        
        if args.command == 'create':
            await backup_tool.create_backup(args.name)
        elif args.command == 'restore':
            await backup_tool.restore_backup(args.backup_file, args.force)
        elif args.command == 'list':
            backup_tool.list_backups(args.dir)
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
