#!/usr/bin/env python3
"""
Authentication system for Text Space
Handles password hashing, login, and session management
"""
import os
import logging
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from database import DatabaseManager, UserRepository, SessionManager

logger = logging.getLogger(__name__)

class PasswordManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

class AuthenticationService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_repo = UserRepository(db_manager)
        self.session_manager = SessionManager(db_manager)
        self.redis = db_manager.redis_client
        
        # Rate limiting settings
        self.max_login_attempts = 5
        self.lockout_duration = 300  # 5 minutes
    
    def register_user(self, username: str, password: str, email: str = None, admin: bool = False) -> Tuple[bool, str]:
        """Register a new user"""
        try:
            # Validate input
            if not username or len(username) < 3:
                return False, "Username must be at least 3 characters"
            
            if not password or len(password) < 6:
                return False, "Password must be at least 6 characters"
            
            # Check if user exists
            if self.user_repo.get_user(username):
                return False, "Username already exists"
            
            # Hash password and create user
            password_hash = PasswordManager.hash_password(password)
            self.user_repo.create_user(username, password_hash, email, admin)
            
            logger.info(f"User '{username}' registered successfully")
            return True, "User registered successfully"
            
        except Exception as e:
            logger.error(f"Registration error for '{username}': {e}")
            return False, "Registration failed"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate a user login"""
        try:
            # Check rate limiting
            if self._is_rate_limited(username):
                return False, "Too many login attempts. Please try again later.", None
            
            # Get user
            user = self.user_repo.get_user(username)
            if not user:
                self._record_failed_attempt(username)
                return False, "Invalid username or password", None
            
            # Verify password
            if not PasswordManager.verify_password(password, user['password_hash']):
                self._record_failed_attempt(username)
                return False, "Invalid username or password", None
            
            # Clear failed attempts and update last login
            self._clear_failed_attempts(username)
            self.user_repo.update_last_login(username)
            
            # Remove password hash from returned user data
            user_safe = {k: v for k, v in user.items() if k != 'password_hash'}
            
            logger.info(f"User '{username}' authenticated successfully")
            return True, "Authentication successful", user_safe
            
        except Exception as e:
            logger.error(f"Authentication error for '{username}': {e}")
            return False, "Authentication failed", None
    
    def create_session(self, username: str, connection_type: str = "tcp") -> str:
        """Create a session for authenticated user"""
        session_data = {
            "connection_type": connection_type,
            "ip_address": "localhost",  # Could be enhanced with real IP
            "user_agent": connection_type
        }
        
        session_id = self.session_manager.create_session(username, session_data)
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate and return session data"""
        session = self.session_manager.get_session(session_id)
        if session:
            # Extend session on activity
            self.session_manager.extend_session(session_id)
            return session
        return None
    
    def logout_user(self, session_id: str):
        """Logout user and destroy session"""
        session = self.session_manager.get_session(session_id)
        if session:
            username = session.get('username')
            self.session_manager.delete_session(session_id)
            logger.info(f"User '{username}' logged out")
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            # Authenticate with old password
            success, message, user = self.authenticate_user(username, old_password)
            if not success:
                return False, "Current password is incorrect"
            
            # Validate new password
            if len(new_password) < 6:
                return False, "New password must be at least 6 characters"
            
            # Hash and update password
            new_hash = PasswordManager.hash_password(new_password)
            if self.user_repo.update_user(username, {"password_hash": new_hash}):
                logger.info(f"Password changed for user '{username}'")
                return True, "Password changed successfully"
            else:
                return False, "Failed to update password"
                
        except Exception as e:
            logger.error(f"Password change error for '{username}': {e}")
            return False, "Password change failed"
    
    def _is_rate_limited(self, username: str) -> bool:
        """Check if user is rate limited"""
        key = f"login_attempts:{username}"
        attempts = self.redis.get(key)
        return attempts and int(attempts) >= self.max_login_attempts
    
    def _record_failed_attempt(self, username: str):
        """Record a failed login attempt"""
        key = f"login_attempts:{username}"
        current = self.redis.get(key)
        
        if current:
            attempts = int(current) + 1
        else:
            attempts = 1
        
        self.redis.setex(key, self.lockout_duration, attempts)
        
        if attempts >= self.max_login_attempts:
            logger.warning(f"User '{username}' locked out due to too many failed attempts")
    
    def _clear_failed_attempts(self, username: str):
        """Clear failed login attempts"""
        self.redis.delete(f"login_attempts:{username}")

class PermissionManager:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def is_admin(self, username: str) -> bool:
        """Check if user has admin privileges"""
        user = self.user_repo.get_user(username)
        return user and user.get('admin', False)
    
    def require_admin(self, username: str) -> bool:
        """Require admin privileges (raises exception if not admin)"""
        if not self.is_admin(username):
            raise PermissionError(f"User '{username}' does not have admin privileges")
        return True
    
    def can_access_room(self, username: str, room_id: str) -> bool:
        """Check if user can access a room (extensible for future room permissions)"""
        # For now, all authenticated users can access all rooms
        return True
    
    def can_modify_item(self, username: str, item_id: str) -> bool:
        """Check if user can modify an item"""
        # For now, only admins can modify items
        return self.is_admin(username)
