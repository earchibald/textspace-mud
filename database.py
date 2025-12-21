#!/usr/bin/env python3
"""
Database layer for Text Space System
Handles MongoDB and Redis operations
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pymongo
import redis
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # MongoDB connection
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/textspace')
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client.get_default_database()
        
        # Redis connection
        self.redis_uri = os.getenv('REDIS_URI', 'redis://localhost:6379/0')
        self.redis_client = redis.from_url(self.redis_uri, decode_responses=True)
        
        # Initialize collections
        self.users = self.db.users
        self.rooms = self.db.rooms
        self.items = self.db.items
        self.bots = self.db.bots
        self.scripts = self.db.scripts
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            self.users.create_index("username", unique=True)
            self.users.create_index("email", unique=True, sparse=True)
            self.rooms.create_index("_id", unique=True)
            self.items.create_index("_id", unique=True)
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def test_connections(self):
        """Test database connections"""
        try:
            # Test MongoDB
            self.mongo_client.admin.command('ping')
            logger.info("MongoDB connection successful")
            
            # Test Redis
            self.redis_client.ping()
            logger.info("Redis connection successful")
            
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

class UserRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.users = db_manager.users
        self.redis = db_manager.redis_client
    
    def create_user(self, username: str, password_hash: str, email: str = None, admin: bool = False) -> Dict:
        """Create a new user"""
        user_data = {
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "room_id": "lobby",
            "inventory": [],
            "admin": admin,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "preferences": {}
        }
        
        try:
            result = self.users.insert_one(user_data)
            user_data["_id"] = result.inserted_id
            logger.info(f"User '{username}' created successfully")
            return user_data
        except pymongo.errors.DuplicateKeyError:
            raise ValueError(f"Username '{username}' already exists")
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        # Try cache first
        cached = self.redis.get(f"cache:user:{username}")
        if cached:
            import json
            return json.loads(cached)
        
        # Get from database
        user = self.users.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string
            # Cache for 5 minutes
            import json
            self.redis.setex(f"cache:user:{username}", 300, json.dumps(user, default=str))
        
        return user
    
    def update_user(self, username: str, updates: Dict) -> bool:
        """Update user data"""
        try:
            result = self.users.update_one(
                {"username": username},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                # Invalidate cache
                self.redis.delete(f"cache:user:{username}")
                logger.info(f"User '{username}' updated successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating user '{username}': {e}")
            return False
    
    def update_last_login(self, username: str):
        """Update user's last login time"""
        self.update_user(username, {"last_login": datetime.utcnow()})
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        users = list(self.users.find({}, {"password_hash": 0}))  # Exclude password
        for user in users:
            user["_id"] = str(user["_id"])
        return users

class RoomRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.rooms = db_manager.rooms
        self.redis = db_manager.redis_client
    
    def create_room(self, room_id: str, name: str, description: str, exits: Dict = None, items: List = None) -> Dict:
        """Create a new room"""
        room_data = {
            "_id": room_id,
            "name": name,
            "description": description,
            "exits": exits or {},
            "items": items or [],
            "properties": {},
            "created_at": datetime.utcnow()
        }
        
        try:
            self.rooms.insert_one(room_data)
            logger.info(f"Room '{room_id}' created successfully")
            return room_data
        except pymongo.errors.DuplicateKeyError:
            raise ValueError(f"Room '{room_id}' already exists")
    
    def get_room(self, room_id: str) -> Optional[Dict]:
        """Get room by ID"""
        # Try cache first
        cached = self.redis.get(f"cache:room:{room_id}")
        if cached:
            import json
            return json.loads(cached)
        
        # Get from database
        room = self.rooms.find_one({"_id": room_id})
        if room:
            # Cache for 10 minutes
            import json
            self.redis.setex(f"cache:room:{room_id}", 600, json.dumps(room, default=str))
        
        return room
    
    def update_room(self, room_id: str, updates: Dict) -> bool:
        """Update room data"""
        try:
            result = self.rooms.update_one(
                {"_id": room_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                # Invalidate cache
                self.redis.delete(f"cache:room:{room_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating room '{room_id}': {e}")
            return False
    
    def get_all_rooms(self) -> List[Dict]:
        """Get all rooms"""
        return list(self.rooms.find({}))
    
    def add_user_to_room(self, room_id: str, username: str):
        """Add user to room's active user set (Redis)"""
        self.redis.sadd(f"room:users:{room_id}", username)
    
    def remove_user_from_room(self, room_id: str, username: str):
        """Remove user from room's active user set (Redis)"""
        self.redis.srem(f"room:users:{room_id}", username)
    
    def get_room_users(self, room_id: str) -> List[str]:
        """Get active users in room (Redis)"""
        return list(self.redis.smembers(f"room:users:{room_id}"))

class ItemRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.items = db_manager.items
    
    def create_item(self, item_id: str, name: str, description: str, tags: List = None, 
                   is_container: bool = False, contents: List = None, script: str = None) -> Dict:
        """Create a new item"""
        item_data = {
            "_id": item_id,
            "name": name,
            "description": description,
            "tags": tags or [],
            "is_container": is_container,
            "contents": contents or [],
            "script": script,
            "created_at": datetime.utcnow()
        }
        
        try:
            self.items.insert_one(item_data)
            logger.info(f"Item '{item_id}' created successfully")
            return item_data
        except pymongo.errors.DuplicateKeyError:
            raise ValueError(f"Item '{item_id}' already exists")
    
    def get_item(self, item_id: str) -> Optional[Dict]:
        """Get item by ID"""
        return self.items.find_one({"_id": item_id})
    
    def get_all_items(self) -> List[Dict]:
        """Get all items"""
        return list(self.items.find({}))

class SessionManager:
    def __init__(self, db_manager: DatabaseManager):
        self.redis = db_manager.redis_client
        self.timeout = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour default
    
    def create_session(self, username: str, session_data: Dict = None) -> str:
        """Create a new session"""
        import uuid
        session_id = str(uuid.uuid4())
        
        data = {
            "username": username,
            "created_at": datetime.utcnow().isoformat(),
            **(session_data or {})
        }
        
        import json
        self.redis.setex(
            f"session:{session_id}",
            self.timeout,
            json.dumps(data, default=str)
        )
        
        logger.info(f"Session created for user '{username}'")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        data = self.redis.get(f"session:{session_id}")
        if data:
            import json
            return json.loads(data)
        return None
    
    def update_session(self, session_id: str, updates: Dict):
        """Update session data"""
        session = self.get_session(session_id)
        if session:
            session.update(updates)
            import json
            self.redis.setex(
                f"session:{session_id}",
                self.timeout,
                json.dumps(session, default=str)
            )
    
    def delete_session(self, session_id: str):
        """Delete session"""
        self.redis.delete(f"session:{session_id}")
    
    def extend_session(self, session_id: str):
        """Extend session timeout"""
        self.redis.expire(f"session:{session_id}", self.timeout)
