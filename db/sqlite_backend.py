"""
SQLite database backend implementation
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from .models import User, Room, Item, Bot

class SQLiteDatabase:
    def __init__(self, db_path: str = "textspace.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    name TEXT PRIMARY KEY,
                    room_id TEXT DEFAULT 'lobby',
                    inventory TEXT DEFAULT '[]',
                    admin BOOLEAN DEFAULT FALSE,
                    password_hash TEXT,
                    session_id TEXT,
                    last_seen TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    exits TEXT DEFAULT '{}',
                    items TEXT DEFAULT '[]'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    is_container BOOLEAN DEFAULT FALSE,
                    contents TEXT DEFAULT '[]',
                    script TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bots (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    responses TEXT DEFAULT '[]',
                    visible BOOLEAN DEFAULT TRUE,
                    inventory TEXT DEFAULT '[]'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
    
    # User operations
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM users WHERE name = ?", (username,)
            )
            row = cursor.fetchone()
            if row:
                return User(
                    name=row['name'],
                    room_id=row['room_id'],
                    inventory=json.loads(row['inventory']),
                    admin=bool(row['admin']),
                    password_hash=row['password_hash'],
                    session_id=row['session_id'],
                    last_seen=datetime.fromisoformat(row['last_seen']) if row['last_seen'] else None,
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                )
        return None
    
    def save_user(self, user: User):
        """Save or update user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (name, room_id, inventory, admin, password_hash, session_id, last_seen, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.name,
                user.room_id,
                json.dumps(user.inventory),
                user.admin,
                user.password_hash,
                user.session_id,
                user.last_seen.isoformat() if user.last_seen else None,
                user.created_at.isoformat() if user.created_at else None
            ))
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        users = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users")
            for row in cursor.fetchall():
                users.append(User(
                    name=row['name'],
                    room_id=row['room_id'],
                    inventory=json.loads(row['inventory']),
                    admin=bool(row['admin']),
                    password_hash=row['password_hash'],
                    session_id=row['session_id'],
                    last_seen=datetime.fromisoformat(row['last_seen']) if row['last_seen'] else None,
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                ))
        return users
    
    # Room operations
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
            row = cursor.fetchone()
            if row:
                return Room(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    exits=json.loads(row['exits']),
                    items=json.loads(row['items'])
                )
        return None
    
    def save_room(self, room: Room):
        """Save or update room"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO rooms (id, name, description, exits, items)
                VALUES (?, ?, ?, ?, ?)
            """, (
                room.id,
                room.name,
                room.description,
                json.dumps(room.exits),
                json.dumps(room.items)
            ))
    
    def get_all_rooms(self) -> List[Room]:
        """Get all rooms"""
        rooms = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM rooms")
            for row in cursor.fetchall():
                rooms.append(Room(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    exits=json.loads(row['exits']),
                    items=json.loads(row['items'])
                ))
        return rooms
    
    # Item operations
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                return Item(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    tags=json.loads(row['tags']),
                    is_container=bool(row['is_container']),
                    contents=json.loads(row['contents']),
                    script=row['script']
                )
        return None
    
    def save_item(self, item: Item):
        """Save or update item"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO items (id, name, description, tags, is_container, contents, script)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id,
                item.name,
                item.description,
                json.dumps(item.tags),
                item.is_container,
                json.dumps(item.contents),
                item.script
            ))
    
    def get_all_items(self) -> List[Item]:
        """Get all items"""
        items = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM items")
            for row in cursor.fetchall():
                items.append(Item(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    tags=json.loads(row['tags']),
                    is_container=bool(row['is_container']),
                    contents=json.loads(row['contents']),
                    script=row['script']
                ))
        return items
    
    # Bot operations
    def get_bot(self, bot_id: str) -> Optional[Bot]:
        """Get bot by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
            row = cursor.fetchone()
            if row:
                return Bot(
                    id=row['id'],
                    name=row['name'],
                    room_id=row['room_id'],
                    description=row['description'],
                    responses=json.loads(row['responses']),
                    visible=bool(row['visible']),
                    inventory=json.loads(row['inventory'])
                )
        return None
    
    def save_bot(self, bot: Bot):
        """Save or update bot"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO bots (id, name, room_id, description, responses, visible, inventory)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bot.id,
                bot.name,
                bot.room_id,
                bot.description,
                json.dumps(bot.responses),
                bot.visible,
                json.dumps(bot.inventory)
            ))
    
    def get_all_bots(self) -> List[Bot]:
        """Get all bots"""
        bots = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM bots")
            for row in cursor.fetchall():
                bots.append(Bot(
                    id=row['id'],
                    name=row['name'],
                    room_id=row['room_id'],
                    description=row['description'],
                    responses=json.loads(row['responses']),
                    visible=bool(row['visible']),
                    inventory=json.loads(row['inventory'])
                ))
        return bots
    
    # Session operations
    def create_session(self, session_id: str, username: str, expires_at: datetime = None):
        """Create user session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions (session_id, username, expires_at)
                VALUES (?, ?, ?)
            """, (
                session_id,
                username,
                expires_at.isoformat() if expires_at else None
            ))
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'session_id': row['session_id'],
                    'username': row['username'],
                    'created_at': row['created_at'],
                    'expires_at': row['expires_at']
                }
        return None
    
    def delete_session(self, session_id: str):
        """Delete session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
