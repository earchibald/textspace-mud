#!/usr/bin/env python3
"""
Migration tools to convert flat files to database
"""
import os
import yaml
import json
import logging
from typing import Dict, List
from database import DatabaseManager, UserRepository, RoomRepository, ItemRepository
from auth import AuthenticationService, PasswordManager

logger = logging.getLogger(__name__)

class MigrationManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.user_repo = UserRepository(self.db_manager)
        self.room_repo = RoomRepository(self.db_manager)
        self.item_repo = ItemRepository(self.db_manager)
        self.auth_service = AuthenticationService(self.db_manager)
    
    def migrate_all(self):
        """Run complete migration from flat files to database"""
        logger.info("Starting complete migration...")
        
        try:
            # Test database connections
            if not self.db_manager.test_connections():
                raise Exception("Database connections failed")
            
            # Migrate in order (rooms first, then items, then users)
            self.migrate_rooms()
            self.migrate_items()
            self.migrate_users()
            self.migrate_bots()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def migrate_rooms(self):
        """Migrate rooms from rooms.yaml"""
        logger.info("Migrating rooms...")
        
        try:
            with open('rooms.yaml', 'r') as f:
                data = yaml.safe_load(f)
            
            rooms_data = data.get('rooms', {})
            migrated = 0
            
            for room_id, room_info in rooms_data.items():
                try:
                    self.room_repo.create_room(
                        room_id=room_id,
                        name=room_info['name'],
                        description=room_info['description'],
                        exits=room_info.get('exits', {}),
                        items=room_info.get('items', [])
                    )
                    migrated += 1
                except ValueError as e:
                    logger.warning(f"Room {room_id} already exists, skipping")
                except Exception as e:
                    logger.error(f"Error migrating room {room_id}: {e}")
            
            logger.info(f"Migrated {migrated} rooms")
            
        except FileNotFoundError:
            logger.warning("rooms.yaml not found, skipping room migration")
        except Exception as e:
            logger.error(f"Room migration failed: {e}")
            raise
    
    def migrate_items(self):
        """Migrate items from items.yaml"""
        logger.info("Migrating items...")
        
        try:
            with open('items.yaml', 'r') as f:
                data = yaml.safe_load(f)
            
            items_data = data.get('items', {})
            migrated = 0
            
            for item_id, item_info in items_data.items():
                try:
                    self.item_repo.create_item(
                        item_id=item_id,
                        name=item_info['name'],
                        description=item_info['description'],
                        tags=item_info.get('tags', []),
                        is_container=item_info.get('is_container', False),
                        contents=item_info.get('contents', []),
                        script=item_info.get('script')
                    )
                    migrated += 1
                except ValueError as e:
                    logger.warning(f"Item {item_id} already exists, skipping")
                except Exception as e:
                    logger.error(f"Error migrating item {item_id}: {e}")
            
            logger.info(f"Migrated {migrated} items")
            
        except FileNotFoundError:
            logger.warning("items.yaml not found, skipping item migration")
        except Exception as e:
            logger.error(f"Item migration failed: {e}")
            raise
    
    def migrate_users(self):
        """Migrate users from users.json"""
        logger.info("Migrating users...")
        
        try:
            with open('users.json', 'r') as f:
                users_data = json.load(f)
            
            migrated = 0
            
            for username, user_info in users_data.items():
                try:
                    # Generate a temporary password for existing users
                    temp_password = f"temp_{username}_123"
                    
                    success, message = self.auth_service.register_user(
                        username=username,
                        password=temp_password,
                        admin=user_info.get('admin', False)
                    )
                    
                    if success:
                        # Update user with existing data
                        updates = {
                            'room_id': user_info.get('room_id', 'lobby'),
                            'inventory': user_info.get('inventory', [])
                        }
                        self.user_repo.update_user(username, updates)
                        migrated += 1
                        
                        logger.info(f"User '{username}' migrated with temporary password: {temp_password}")
                    else:
                        logger.warning(f"Failed to migrate user {username}: {message}")
                        
                except Exception as e:
                    logger.error(f"Error migrating user {username}: {e}")
            
            logger.info(f"Migrated {migrated} users")
            
            if migrated > 0:
                logger.warning("IMPORTANT: All migrated users have temporary passwords!")
                logger.warning("Users should change their passwords on first login.")
            
        except FileNotFoundError:
            logger.warning("users.json not found, skipping user migration")
        except Exception as e:
            logger.error(f"User migration failed: {e}")
            raise
    
    def migrate_bots(self):
        """Migrate bots from bots.yaml"""
        logger.info("Migrating bots...")
        
        try:
            with open('bots.yaml', 'r') as f:
                data = yaml.safe_load(f)
            
            bots_data = data.get('bots', {})
            migrated = 0
            
            for bot_id, bot_info in bots_data.items():
                try:
                    bot_doc = {
                        "_id": bot_id,
                        "name": bot_info['name'],
                        "room_id": bot_info['room'],
                        "description": bot_info['description'],
                        "responses": bot_info.get('responses', []),
                        "visible": bot_info.get('visible', True),
                        "inventory": bot_info.get('inventory', []),
                        "created_at": "2025-12-21T00:00:00"  # Migration timestamp
                    }
                    
                    self.db_manager.bots.insert_one(bot_doc)
                    migrated += 1
                    
                except Exception as e:
                    logger.error(f"Error migrating bot {bot_id}: {e}")
            
            logger.info(f"Migrated {migrated} bots")
            
        except FileNotFoundError:
            logger.warning("bots.yaml not found, skipping bot migration")
        except Exception as e:
            logger.error(f"Bot migration failed: {e}")
            raise
    
    def create_admin_user(self, username: str = "admin", password: str = "admin123"):
        """Create initial admin user"""
        logger.info("Creating admin user...")
        
        success, message = self.auth_service.register_user(
            username=username,
            password=password,
            admin=True
        )
        
        if success:
            logger.info(f"Admin user '{username}' created with password '{password}'")
            logger.warning("CHANGE THE ADMIN PASSWORD IMMEDIATELY!")
        else:
            logger.error(f"Failed to create admin user: {message}")
        
        return success
    
    def verify_migration(self):
        """Verify migration was successful"""
        logger.info("Verifying migration...")
        
        try:
            # Count migrated data
            room_count = self.db_manager.rooms.count_documents({})
            item_count = self.db_manager.items.count_documents({})
            user_count = self.db_manager.users.count_documents({})
            bot_count = self.db_manager.bots.count_documents({})
            
            logger.info(f"Migration verification:")
            logger.info(f"  Rooms: {room_count}")
            logger.info(f"  Items: {item_count}")
            logger.info(f"  Users: {user_count}")
            logger.info(f"  Bots: {bot_count}")
            
            return room_count > 0 or item_count > 0 or user_count > 0
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False

def main():
    """Run migration from command line"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Text Space Migration Tool")
    print("=" * 40)
    
    migrator = MigrationManager()
    
    # Run migration
    if migrator.migrate_all():
        print("\n✅ Migration completed successfully!")
        
        # Create admin user
        print("\nCreating admin user...")
        migrator.create_admin_user()
        
        # Verify migration
        print("\nVerifying migration...")
        if migrator.verify_migration():
            print("✅ Migration verification passed!")
        else:
            print("⚠️  Migration verification failed!")
    else:
        print("\n❌ Migration failed!")
        return 1
    
    print("\n" + "=" * 40)
    print("Migration complete!")
    print("Next steps:")
    print("1. Start MongoDB and Redis services")
    print("2. Update your .env file with database URLs")
    print("3. Change the admin password")
    print("4. Test the new system")
    
    return 0

if __name__ == "__main__":
    exit(main())
