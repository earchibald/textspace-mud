"""
Database module for Multi-User Text Space System
Provides unified interface for database operations
"""
import os
from .sqlite_backend import SQLiteDatabase
from .models import User, Room, Item, Bot

class Database:
    """Main database interface"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'textspace.db')
        
        self.backend = SQLiteDatabase(db_path)
    
    # User operations
    def get_user(self, username: str):
        return self.backend.get_user(username)
    
    def save_user(self, user: User):
        return self.backend.save_user(user)
    
    def get_all_users(self):
        return self.backend.get_all_users()
    
    # Room operations
    def get_room(self, room_id: str):
        return self.backend.get_room(room_id)
    
    def save_room(self, room: Room):
        return self.backend.save_room(room)
    
    def get_all_rooms(self):
        return self.backend.get_all_rooms()
    
    # Item operations
    def get_item(self, item_id: str):
        return self.backend.get_item(item_id)
    
    def save_item(self, item: Item):
        return self.backend.save_item(item)
    
    def get_all_items(self):
        return self.backend.get_all_items()
    
    # Bot operations
    def get_bot(self, bot_id: str):
        return self.backend.get_bot(bot_id)
    
    def save_bot(self, bot: Bot):
        return self.backend.save_bot(bot)
    
    def get_all_bots(self):
        return self.backend.get_all_bots()
    
    # Session operations
    def create_session(self, session_id: str, username: str, expires_at=None):
        return self.backend.create_session(session_id, username, expires_at)
    
    def get_session(self, session_id: str):
        return self.backend.get_session(session_id)
    
    def delete_session(self, session_id: str):
        return self.backend.delete_session(session_id)
    
    def test_connection(self):
        return self.backend.test_connection()

# Convenience imports
__all__ = ['Database', 'User', 'Room', 'Item', 'Bot']
