#!/usr/bin/env python
"""
Enhanced Text Space Server with Database Support
Supports both flat file and database backends
"""
import asyncio
import json
import yaml
import logging
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional, List, Any
from script_engine import ScriptEngine
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading

# Try to import database modules (optional)
try:
    from db import Database, User as DBUser, Room as DBRoom, Item as DBItem, Bot as DBBot
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("Database modules not available, using flat file backend")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('textspace.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Item:
    id: str
    name: str
    description: str
    tags: list = None
    is_container: bool = False
    contents: list = None  # List of item IDs if container
    script: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.contents is None:
            self.contents = []

@dataclass
class Bot:
    name: str
    room_id: str
    description: str
    responses: list
    visible: bool = True
    inventory: list = None  # List of item IDs
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

@dataclass
class Event:
    type: str  # "enter_room", "leave_room"
    room_id: str
    user_name: str
    data: dict = None

@dataclass
class Room:
    id: str
    name: str
    description: str
    exits: Dict[str, str]
    users: set = None
    items: list = None  # List of item IDs
    
    def __post_init__(self):
        if self.users is None:
            self.users = set()
        if self.items is None:
            self.items = []

@dataclass
class WebUser:
    name: str
    session_id: str
    room_id: str = "lobby"
    authenticated: bool = False
    admin: bool = False
    inventory: list = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

@dataclass
class User:
    name: str
    writer: asyncio.StreamWriter
    room_id: str = "lobby"
    authenticated: bool = False
    admin: bool = False
    inventory: list = None  # List of item IDs
    session_id: str = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

class TextSpaceServer:
    def __init__(self, use_database: bool = None):
        # Determine backend type
        if use_database is None:
            use_database = DATABASE_AVAILABLE and os.getenv('USE_DATABASE', 'false').lower() == 'true'
        
        self.use_database = use_database
        logger.info(f"Using {'database' if use_database else 'flat file'} backend")
        
        # Initialize data structures
        self.users: Dict[str, User] = {}
        self.connections: Dict[asyncio.StreamWriter, Optional[str]] = {}
        self.web_users: Dict[str, WebUser] = {}  # Web users by session_id
        self.web_sessions: Dict[str, str] = {}  # session_id -> username
        self.rooms: Dict[str, Room] = {}
        self.bots: Dict[str, Bot] = {}
        self.items: Dict[str, Item] = {}
        self.script_engine = ScriptEngine(self)
        self.scripts: Dict[str, dict] = {}
        self.event_handlers: Dict[str, list] = {}  # event_type -> list of script names
        
        # Initialize backend
        if self.use_database:
            self._init_database_backend()
        else:
            self._init_flat_file_backend()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'textspace-secret')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.setup_web_routes()
    
    def _init_database_backend(self):
        """Initialize database backend"""
        try:
            self.db = Database()
            
            if not self.db.test_connection():
                raise Exception("Database connection failed")
            
            self.load_from_database()
            logger.info("Database backend initialized successfully")
            
        except Exception as e:
            logger.error(f"Database backend initialization failed: {e}")
            logger.info("Falling back to flat file backend")
            self.use_database = False
            self._init_flat_file_backend()
    
    def _init_flat_file_backend(self):
        """Initialize flat file backend"""
        self.user_data_file = "users.json"
        self.persistent_users = {}
        self.load_rooms()
        self.load_bots()
        self.load_items()
        self.load_scripts()
        self.load_user_data()
        logger.info("Flat file backend initialized")
    
    def load_from_database(self):
        """Load data from database into memory"""
        try:
            # Load rooms
            rooms_data = self.db.get_all_rooms()
            for room in rooms_data:
                self.rooms[room.id] = Room(
                    id=room.id,
                    name=room.name,
                    description=room.description,
                    exits=room.exits,
                    items=room.items
                )
            
            # Load items
            items_data = self.db.get_all_items()
            for item in items_data:
                self.items[item.id] = Item(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    tags=item.tags,
                    is_container=item.is_container,
                    contents=item.contents,
                    script=item.script
                )
            
            # Load bots
            bots_data = self.db.get_all_bots()
            for bot in bots_data:
                self.bots[bot.id] = Bot(
                    name=bot.name,
                    room_id=bot.room_id,
                    description=bot.description,
                    responses=bot.responses,
                    visible=bot.visible,
                    inventory=bot.inventory
                )
            
            # Load scripts (keep in memory for now)
            self.load_scripts()
            
            logger.info(f"Loaded from database: {len(self.rooms)} rooms, {len(self.items)} items, {len(self.bots)} bots")
            
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            raise
    
    def load_rooms(self):
        """Load rooms from YAML file"""
        try:
            with open('rooms.yaml', 'r') as f:
                data = yaml.safe_load(f)
                for room_id, room_data in data['rooms'].items():
                    self.rooms[room_id] = Room(
                        id=room_id,
                        name=room_data['name'],
                        description=room_data['description'],
                        exits=room_data.get('exits', {}),
                        items=room_data.get('items', [])
                    )
            logger.info(f"Loaded {len(self.rooms)} rooms from rooms.yaml")
        except Exception as e:
            logger.error(f"Error loading rooms: {e}")
    
    def load_bots(self):
        """Load bots from YAML file"""
        try:
            with open('bots.yaml', 'r') as f:
                data = yaml.safe_load(f)
                for bot_id, bot_data in data['bots'].items():
                    self.bots[bot_id] = Bot(
                        name=bot_data['name'],
                        room_id=bot_data['room'],
                        description=bot_data['description'],
                        responses=bot_data.get('responses', []),
                        visible=bot_data.get('visible', True),
                        inventory=bot_data.get('inventory', [])
                    )
            logger.info(f"Loaded {len(self.bots)} bots from bots.yaml")
        except Exception as e:
            logger.error(f"Error loading bots: {e}")
    
    def load_items(self):
        """Load items from YAML file"""
        try:
            with open('items.yaml', 'r') as f:
                data = yaml.safe_load(f)
                for item_id, item_data in data['items'].items():
                    self.items[item_id] = Item(
                        id=item_id,
                        name=item_data['name'],
                        description=item_data['description'],
                        tags=item_data.get('tags', []),
                        is_container=item_data.get('is_container', False),
                        contents=item_data.get('contents', []),
                        script=item_data.get('script')
                    )
            logger.info(f"Loaded {len(self.items)} items from items.yaml")
        except Exception as e:
            logger.error(f"Error loading items: {e}")
    
    def load_scripts(self):
        """Load scripts from YAML file"""
        try:
            with open('scripts.yaml', 'r') as f:
                data = yaml.safe_load(f)
                for script_name, script_data in data['scripts'].items():
                    self.scripts[script_name] = script_data
                    
                    # Register event handlers
                    if 'trigger' in script_data:
                        trigger = script_data['trigger']
                        event_type = trigger.get('event')
                        if event_type:
                            if event_type not in self.event_handlers:
                                self.event_handlers[event_type] = []
                            self.event_handlers[event_type].append(script_name)
            
            logger.info(f"Loaded {len(self.scripts)} scripts from scripts.yaml")
        except Exception as e:
            logger.error(f"Error loading scripts: {e}")
    
    def load_user_data(self):
        """Load persistent user data from JSON file"""
        if not self.use_database:
            try:
                with open(self.user_data_file, 'r') as f:
                    self.persistent_users = json.load(f)
                logger.info(f"Loaded {len(self.persistent_users)} persistent users")
            except FileNotFoundError:
                self.persistent_users = {}
                logger.info("No existing user data file found")
            except Exception as e:
                logger.error(f"Error loading user data: {e}")
                self.persistent_users = {}
    
    def save_user_data(self):
        """Save persistent user data to JSON file"""
        if not self.use_database:
            try:
                with open(self.user_data_file, 'w') as f:
                    json.dump(self.persistent_users, f, indent=2)
                logger.debug("Saved user data to file")
            except Exception as e:
                logger.error(f"Error saving user data: {e}")
    
    async def save_user_to_backend(self, user):
        """Save user data to appropriate backend"""
        if self.use_database:
            try:
                db_user = DBUser(
                    name=user.name,
                    room_id=user.room_id,
                    inventory=user.inventory,
                    admin=user.admin,
                    last_seen=datetime.utcnow()
                )
                self.db.save_user(db_user)
            except Exception as e:
                logger.error(f"Error saving user to database: {e}")
        else:
            # Save to flat file
            self.persistent_users[user.name] = {
                'room_id': user.room_id,
                'inventory': user.inventory,
                'admin': user.admin
            }
            self.save_user_data()
    
    async def load_user_from_backend(self, username):
        """Load user data from appropriate backend"""
        if self.use_database:
            try:
                db_user = self.db.get_user(username)
                if db_user:
                    return {
                        'room_id': db_user.room_id,
                        'inventory': db_user.inventory,
                        'admin': db_user.admin
                    }
            except Exception as e:
                logger.error(f"Error loading user from database: {e}")
                return None
        else:
            return self.persistent_users.get(username)
    
    def setup_web_routes(self):
        """Setup Flask routes and SocketIO handlers"""
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/init-db')
        def init_database():
            """Initialize database with YAML data"""
            try:
                import yaml
                
                # Load and save rooms
                with open('rooms.yaml', 'r') as f:
                    rooms_data = yaml.safe_load(f)
                    for room_id, room_data in rooms_data['rooms'].items():
                        if not self.db.get_room(room_id):  # Only if not exists
                            from db.models import Room
                            room = Room(
                                id=room_id,
                                name=room_data['name'],
                                description=room_data['description'],
                                exits=room_data.get('exits', {}),
                                items=room_data.get('items', [])
                            )
                            self.db.save_room(room)
                
                # Load and save items
                with open('items.yaml', 'r') as f:
                    items_data = yaml.safe_load(f)
                    for item_id, item_data in items_data['items'].items():
                        if not self.db.get_item(item_id):  # Only if not exists
                            from db.models import Item
                            item = Item(
                                id=item_id,
                                name=item_data['name'],
                                description=item_data['description'],
                                tags=item_data.get('tags', []),
                                is_container=item_data.get('is_container', False),
                                contents=item_data.get('contents', []),
                                script=item_data.get('script')
                            )
                            self.db.save_item(item)
                
                # Load and save bots
                with open('bots.yaml', 'r') as f:
                    bots_data = yaml.safe_load(f)
                    for bot_id, bot_data in bots_data['bots'].items():
                        if not self.db.get_bot(bot_id):  # Only if not exists
                            from db.models import Bot
                            bot = Bot(
                                id=bot_id,
                                name=bot_data['name'],
                                room_id=bot_data['room'],
                                description=bot_data['description'],
                                responses=bot_data.get('responses', []),
                                visible=bot_data.get('visible', True),
                                inventory=bot_data.get('inventory', [])
                            )
                            self.db.save_bot(bot)
                
                # Reload data into memory
                self.load_from_database()
                
                return {"status": "success", "message": "Database initialized successfully"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Web client connected: {request.sid}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Web client disconnected: {request.sid}")
            if request.sid in self.web_sessions:
                username = self.web_sessions[request.sid]
                if username in self.web_users:
                    asyncio.create_task(self.handle_web_user_disconnect(username, request.sid))
        
        @self.socketio.on('login')
        def handle_web_login(data):
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username:
                emit('login_response', {'success': False, 'message': 'Username required'})
                return
            
            # Simple username-based authentication (no password required for now)
            admin = username == "admin"
            
            # Create web user
            web_user = WebUser(
                name=username,
                session_id=request.sid,
                authenticated=True,
                admin=admin
            )
            
            # Load user data
            user_data = asyncio.run(self.load_user_from_backend(username))
            if user_data:
                web_user.room_id = user_data.get('room_id', 'lobby')
                web_user.inventory = user_data.get('inventory', [])
            
            self.web_users[username] = web_user
            self.web_sessions[request.sid] = username
            
            # Add to room
            if web_user.room_id in self.rooms:
                self.rooms[web_user.room_id].users.add(username)
            
            join_room(web_user.room_id)
            
            logger.info(f"Web user '{username}' logged in (admin: {admin})")
            
            emit('login_response', {'success': True, 'admin': admin})
            emit('message', {'text': f'Welcome, {username}! Type "help" for commands.'})
            
            # Send initial room info
            asyncio.create_task(self.send_web_room_info(username))
            
            # Trigger enter room event
            asyncio.create_task(self.trigger_event(Event("enter_room", web_user.room_id, username)))
        
        @self.socketio.on('command')
        def handle_web_command(data):
            if request.sid not in self.web_sessions:
                emit('message', {'text': 'Not logged in'})
                return
            
            username = self.web_sessions[request.sid]
            command = data.get('command', '').strip()
            
            if command:
                try:
                    # Process command synchronously for web users
                    response = self.process_web_command_sync(username, command)
                    if response:
                        emit('message', {'text': response})
                except Exception as e:
                    logger.error(f"Error processing web command: {e}")
                    emit('message', {'text': f'Error: {str(e)}'})
            else:
                emit('message', {'text': 'Empty command'})
    
    async def handle_web_user_disconnect(self, username, session_id):
        """Handle web user disconnection"""
        if username in self.web_users:
            web_user = self.web_users[username]
            
            # Remove from room
            if web_user.room_id in self.rooms:
                self.rooms[web_user.room_id].users.discard(username)
            
            # Save user data
            await self.save_web_user_data(web_user)
            
            # Clean up
            del self.web_users[username]
            if session_id in self.web_sessions:
                del self.web_sessions[session_id]
            
            logger.info(f"Web user '{username}' disconnected")
    
    async def save_web_user_data(self, web_user):
        """Save web user data to backend"""
        if self.use_database:
            try:
                user_data = {
                    'name': web_user.name,
                    'room_id': web_user.room_id,
                    'inventory': web_user.inventory,
                    'admin': web_user.admin,
                    'last_seen': datetime.utcnow()
                }
                await self.user_repo.save_user(user_data)
            except Exception as e:
                logger.error(f"Error saving web user to database: {e}")
        else:
            self.persistent_users[web_user.name] = {
                'room_id': web_user.room_id,
                'inventory': web_user.inventory,
                'admin': web_user.admin
            }
            self.save_user_data()
    
    async def send_web_room_info(self, username):
        """Send room information to web user"""
        if username not in self.web_users:
            return
        
        web_user = self.web_users[username]
        room = self.rooms.get(web_user.room_id)
        
        if not room:
            return
        
        # Build room info
        room_info = {
            'name': room.name,
            'description': room.description,
            'exits': list(room.exits.keys()),
            'users': [u for u in room.users if u != username],
            'bots': [bot.name for bot in self.bots.values() 
                    if bot.room_id == room.id and bot.visible],
            'items': [self.items[item_id].name for item_id in room.items 
                     if item_id in self.items]
        }
        
        self.socketio.emit('room_info', room_info, room=web_user.session_id)
    
    def process_web_command_sync(self, username, command):
        """Process command from web user synchronously"""
        if username not in self.web_users:
            return "User not found"
        
        web_user = self.web_users[username]
        
        # Basic commands that don't need async
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == "help":
            return self.get_help_text(web_user.admin)
        elif cmd == "look":
            return self.get_room_description(web_user.room_id, username)
        elif cmd == "who":
            return self.get_who_list()
        elif cmd == "inventory" or cmd == "inv":
            return self.get_inventory_web(web_user)
        elif cmd == "say" and args:
            message = " ".join(args)
            return self.handle_say_web(web_user, message)
        elif cmd in ["north", "south", "east", "west"] or (cmd == "go" and args):
            direction = args[0] if cmd == "go" else cmd
            return self.move_user_web(web_user, direction)
        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."
    
    def get_room_description(self, room_id, username):
        """Get room description for web users"""
        room = self.rooms.get(room_id)
        if not room:
            return "You are in an unknown location."
        
        message = f"{room.name}\n{room.description}\n"
        
        if room.exits:
            exits = ", ".join(room.exits.keys())
            message += f"Exits: {exits}\n"
        
        other_users = [u for u in room.users if u != username]
        if other_users:
            message += f"Users here: {', '.join(other_users)}\n"
        
        bots_here = [bot.name for bot in self.bots.values() 
                    if bot.room_id == room.id and bot.visible]
        if bots_here:
            message += f"Bots here: {', '.join(bots_here)}\n"
        
        if room.items:
            item_names = [self.items[item_id].name for item_id in room.items 
                         if item_id in self.items]
            if item_names:
                message += f"Items here: {', '.join(item_names)}\n"
        
        # Update room info panel
        self.send_web_room_info_sync(username)
        
        return message.strip()
    
    def get_inventory_web(self, web_user):
        """Get inventory for web user"""
        if not web_user.inventory:
            return "You are not carrying anything."
        
        items = []
        for item_id in web_user.inventory:
            if item_id in self.items:
                items.append(self.items[item_id].name)
        
        return f"You are carrying: {', '.join(items)}"
    
    def handle_say_web(self, web_user, message):
        """Handle say command for web user"""
        room_message = f"{web_user.name} says: {message}"
        self.send_to_room(web_user.room_id, room_message, exclude_user=web_user.name)
        return f"You say: {message}"
    
    def move_user_web(self, web_user, direction):
        """Move web user to another room"""
        current_room = self.rooms.get(web_user.room_id)
        if not current_room:
            return "You are in an unknown location."
        
        if direction not in current_room.exits:
            return f"You can't go {direction} from here."
        
        target_room_id = current_room.exits[direction]
        if target_room_id not in self.rooms:
            return f"The {direction} exit leads nowhere."
        
        # Move user
        current_room.users.discard(web_user.name)
        web_user.room_id = target_room_id
        self.rooms[target_room_id].users.add(web_user.name)
        
        # Update room info
        self.send_web_room_info_sync(web_user.name)
        
        return self.get_room_description(target_room_id, web_user.name)
    
    def send_web_room_info_sync(self, username):
        """Send room info to web user synchronously"""
        if username not in self.web_users:
            return
        
        web_user = self.web_users[username]
        room = self.rooms.get(web_user.room_id)
        
        if not room:
            return
        
        room_info = {
            'name': room.name,
            'description': room.description,
            'exits': list(room.exits.keys()),
            'users': [u for u in room.users if u != username],
            'bots': [bot.name for bot in self.bots.values() 
                    if bot.room_id == room.id and bot.visible],
            'items': [self.items[item_id].name for item_id in room.items 
                     if item_id in self.items]
        }
        
        self.socketio.emit('room_info', room_info, room=web_user.session_id)
    
    def send_to_web_user(self, username, message):
        """Send message to specific web user"""
        if username in self.web_users:
            web_user = self.web_users[username]
            self.socketio.emit('message', {'text': message}, room=web_user.session_id)
    
    def send_to_web_room(self, room_id, message, exclude_user=None):
        """Send message to all web users in a room"""
        for username, web_user in self.web_users.items():
            if web_user.room_id == room_id and username != exclude_user:
                self.socketio.emit('message', {'text': message}, room=web_user.session_id)
    
    def send_to_all_web_users(self, message):
        """Send message to all web users"""
        self.socketio.emit('message', {'text': message})
    
    async def handle_client(self, reader, writer):
        """Handle TCP client connection"""
        addr = writer.get_extra_info('peername')
        logger.info(f"Client connected from {addr}")
        
        self.connections[writer] = None  # No username yet
        
        try:
            # Send welcome message
            await self.send_message(writer, "Welcome to the Multi-User Text Space!")
            await self.send_message(writer, "Enter your username:")
            
            while True:
                data = await reader.readline()
                if not data:
                    break
                
                message = data.decode().strip()
                if not message:
                    continue
                
                # Handle login
                if writer not in self.connections or self.connections[writer] is None:
                    username = message
                    if not username:
                        await self.send_message(writer, "Username cannot be empty. Try again:")
                        continue
                    
                    # Check if username is already taken
                    if username in self.users:
                        await self.send_message(writer, "Username already taken. Try another:")
                        continue
                    
                    # Handle authentication
                    if self.use_database:
                        # For database mode, we might want password authentication
                        # For now, keep it simple like flat file mode
                        pass
                    
                    # Create user
                    admin = username == "admin"
                    user = User(
                        name=username,
                        writer=writer,
                        authenticated=True,
                        admin=admin
                    )
                    
                    # Load user data
                    user_data = await self.load_user_from_backend(username)
                    if user_data:
                        user.room_id = user_data.get('room_id', 'lobby')
                        user.inventory = user_data.get('inventory', [])
                        user.admin = user_data.get('admin', admin)
                    
                    self.users[username] = user
                    self.connections[writer] = username
                    
                    # Add to room
                    if user.room_id in self.rooms:
                        self.rooms[user.room_id].users.add(username)
                    
                    logger.info(f"User '{username}' logged in (admin: {user.admin})")
                    
                    await self.send_message(writer, f"Welcome, {username}!")
                    if user.admin:
                        await self.send_message(writer, "You have admin privileges.")
                    await self.send_message(writer, "Type 'help' for commands.")
                    
                    # Show room
                    await self.show_room(user)
                    
                    # Trigger enter room event
                    await self.trigger_event(Event("enter_room", user.room_id, username))
                else:
                    # Process command
                    username = self.connections[writer]
                    user = self.users[username]
                    
                    logger.debug(f"User '{username}' command: {message}")
                    
                    response = await self.process_command(user, message)
                    if response:
                        await self.send_message(writer, response)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            await self.cleanup_connection(writer)
    
    async def cleanup_connection(self, writer):
        """Clean up client connection"""
        try:
            username = self.connections.get(writer)
            if username and username in self.users:
                user = self.users[username]
                
                # Remove from room
                if user.room_id in self.rooms:
                    self.rooms[user.room_id].users.discard(username)
                
                # Save user data
                await self.save_user_to_backend(user)
                
                # Clean up
                del self.users[username]
                logger.info(f"User '{username}' disconnected")
            
            if writer in self.connections:
                del self.connections[writer]
            
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.error(f"Error cleaning up connection: {e}")
    
    async def send_message(self, writer, message):
        """Send message to TCP client"""
        try:
            writer.write(f"{message}\n".encode())
            await writer.drain()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def send_to_user(self, username, message):
        """Send message to specific user (TCP or web)"""
        # TCP user
        if username in self.users:
            user = self.users[username]
            if user.writer:
                asyncio.create_task(self.send_message(user.writer, message))
        
        # Web user
        self.send_to_web_user(username, message)
    
    def send_to_room(self, room_id, message, exclude_user=None):
        """Send message to all users in a room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        
        # Send to TCP users
        for username in room.users:
            if username != exclude_user and username in self.users:
                user = self.users[username]
                if user.writer:
                    asyncio.create_task(self.send_message(user.writer, message))
        
        # Send to web users
        self.send_to_web_room(room_id, message, exclude_user)
    
    def send_to_all_users(self, message):
        """Send message to all connected users"""
        # Send to TCP users
        for user in self.users.values():
            if user.writer:
                asyncio.create_task(self.send_message(user.writer, message))
        
        # Send to web users
        self.send_to_all_web_users(message)
    
    async def process_command(self, user, command, is_web=False):
        """Process user command"""
        if not command:
            return None
        
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Basic commands
        if cmd == "help":
            return self.get_help_text(user.admin)
        elif cmd == "look":
            await self.show_room(user)
            return None
        elif cmd == "who":
            return self.get_who_list()
        elif cmd == "inventory" or cmd == "inv":
            return self.get_inventory(user)
        elif cmd == "quit":
            if is_web:
                return "Goodbye!"
            else:
                return "quit"  # Special signal for TCP client
        
        # Movement commands
        elif cmd in ["go", "move"] and args:
            return await self.move_user(user, args[0])
        elif cmd in self.rooms.get(user.room_id, Room("", "", "", {})).exits:
            return await self.move_user(user, cmd)
        
        # Communication commands
        elif cmd == "say" and args:
            message = " ".join(args)
            return await self.handle_say(user, message)
        elif cmd == "whisper" and len(args) >= 2:
            target = args[0]
            message = " ".join(args[1:])
            return await self.handle_whisper(user, target, message)
        
        # Item commands
        elif cmd in ["get", "take"] and args:
            item_name = " ".join(args)
            return await self.handle_get_item(user, item_name)
        elif cmd == "drop" and args:
            item_name = " ".join(args)
            return await self.handle_drop_item(user, item_name)
        elif cmd in ["examine", "exam", "look"] and args:
            item_name = " ".join(args)
            return await self.handle_examine_item(user, item_name)
        elif cmd == "use" and args:
            item_name = " ".join(args)
            return await self.handle_use_item(user, item_name)
        
        # Admin commands
        elif cmd == "teleport" and user.admin:
            if args:
                return await self.handle_teleport(user, args[0])
            else:
                return "Available rooms: " + ", ".join(self.rooms.keys())
        elif cmd == "broadcast" and user.admin and args:
            message = " ".join(args)
            return await self.handle_broadcast(user, message)
        elif cmd == "script" and user.admin and args:
            script_name = args[0]
            return await self.handle_execute_script(user, script_name)
        
        # Check for bot responses
        await self.check_bot_responses(user.room_id, command)
        
        return f"Unknown command: {cmd}. Type 'help' for available commands."
    
    def get_help_text(self, is_admin):
        """Get help text for user"""
        help_text = """
Available commands:
  look - See room description and contents
  go <exit> - Move to another room (or just type the exit name)
  say <message> - Speak to everyone in the room
  whisper <user> <message> - Send private message
  who - List all online users
  inventory - Show your items
  get <item> - Pick up an item
  drop <item> - Drop an item
  examine <item> - Look at an item closely
  use <item> - Use an item
  help - Show this help
  quit - Disconnect
"""
        
        if is_admin:
            help_text += """
Admin commands:
  teleport [room] - Jump to room (no args lists rooms)
  broadcast <message> - Send message to all users
  script <name> - Execute a bot script
"""
        
        return help_text.strip()
    
    def get_who_list(self):
        """Get list of online users"""
        tcp_users = list(self.users.keys())
        web_users = list(self.web_users.keys())
        all_users = sorted(set(tcp_users + web_users))
        
        if not all_users:
            return "No users online."
        
        return f"Online users ({len(all_users)}): " + ", ".join(all_users)
    
    def get_inventory(self, user):
        """Get user's inventory"""
        if not user.inventory:
            return "You are not carrying anything."
        
        items = []
        for item_id in user.inventory:
            if item_id in self.items:
                items.append(self.items[item_id].name)
        
        return f"You are carrying: {', '.join(items)}"
    
    async def show_room(self, user):
        """Show room information to user"""
        room = self.rooms.get(user.room_id)
        if not room:
            if user.writer:
                await self.send_message(user.writer, "You are in an unknown location.")
            else:
                # Web user - send message via SocketIO
                self.send_to_web_user(user.name, "You are in an unknown location.")
            return
        
        # Room description
        message = f"\n{room.name}\n{room.description}\n"
        
        # Exits
        if room.exits:
            exits = ", ".join(room.exits.keys())
            message += f"Exits: {exits}\n"
        
        # Users
        other_users = [u for u in room.users if u != user.name]
        if other_users:
            message += f"Users here: {', '.join(other_users)}\n"
        
        # Visible bots
        bots_here = [bot.name for bot in self.bots.values() 
                    if bot.room_id == room.id and bot.visible]
        if bots_here:
            message += f"Bots here: {', '.join(bots_here)}\n"
        
        # Items
        if room.items:
            item_names = [self.items[item_id].name for item_id in room.items 
                         if item_id in self.items]
            if item_names:
                message += f"Items here: {', '.join(item_names)}\n"
        
        if user.writer:
            await self.send_message(user.writer, message.strip())
        else:
            # Web user - send message and room info
            self.send_to_web_user(user.name, message.strip())
            await self.send_web_room_info(user.name)
    
    async def move_user(self, user, direction):
        """Move user to another room"""
        current_room = self.rooms.get(user.room_id)
        if not current_room:
            return "You are in an unknown location."
        
        # Check if direction is valid
        if direction not in current_room.exits:
            return f"You can't go {direction} from here."
        
        target_room_id = current_room.exits[direction]
        if target_room_id not in self.rooms:
            return f"The {direction} exit leads nowhere."
        
        # Trigger leave room event
        await self.trigger_event(Event("leave_room", user.room_id, user.name))
        
        # Move user
        current_room.users.discard(user.name)
        user.room_id = target_room_id
        self.rooms[target_room_id].users.add(user.name)
        
        # Show new room
        await self.show_room(user)
        
        # Trigger enter room event
        await self.trigger_event(Event("enter_room", user.room_id, user.name))
        
        return None
    
    async def handle_say(self, user, message):
        """Handle say command"""
        room_message = f"{user.name} says: {message}"
        self.send_to_room(user.room_id, room_message, exclude_user=user.name)
        
        logger.info(f"User '{user.name}' says in '{user.room_id}': {message}")
        
        return f"You say: {message}"
    
    async def handle_whisper(self, user, target, message):
        """Handle whisper command"""
        # Check if target user exists
        if target not in self.users and target not in self.web_users:
            return f"User '{target}' is not online."
        
        whisper_message = f"{user.name} whispers to you: {message}"
        self.send_to_user(target, whisper_message)
        
        logger.info(f"User '{user.name}' whispers to '{target}': {message}")
        
        return f"You whisper to {target}: {message}"
    
    async def handle_get_item(self, user, item_name):
        """Handle get/take item command"""
        room = self.rooms.get(user.room_id)
        if not room:
            return "You are in an unknown location."
        
        # Find item in room
        item_id = self.find_item_by_name(item_name, room.items)
        if not item_id:
            # Check bot inventories
            for bot in self.bots.values():
                if bot.room_id == user.room_id:
                    bot_item_id = self.find_item_by_name(item_name, bot.inventory)
                    if bot_item_id:
                        # Try to get item from bot
                        bot.inventory.remove(bot_item_id)
                        user.inventory.append(bot_item_id)
                        await self.save_user_to_backend(user)
                        return f"You get the {self.items[bot_item_id].name} from {bot.name}."
            
            return f"There is no '{item_name}' here."
        
        # Move item from room to user
        room.items.remove(item_id)
        user.inventory.append(item_id)
        
        # Save user data
        await self.save_user_to_backend(user)
        
        item = self.items[item_id]
        return f"You pick up the {item.name}."
    
    async def handle_drop_item(self, user, item_name):
        """Handle drop item command"""
        item_id = self.find_item_by_name(item_name, user.inventory)
        if not item_id:
            return f"You don't have a '{item_name}'."
        
        room = self.rooms.get(user.room_id)
        if not room:
            return "You are in an unknown location."
        
        # Move item from user to room
        user.inventory.remove(item_id)
        room.items.append(item_id)
        
        # Save user data
        await self.save_user_to_backend(user)
        
        item = self.items[item_id]
        return f"You drop the {item.name}."
    
    async def handle_examine_item(self, user, item_name):
        """Handle examine item command"""
        # Check user inventory first
        item_id = self.find_item_by_name(item_name, user.inventory)
        
        # Check room items
        if not item_id:
            room = self.rooms.get(user.room_id)
            if room:
                item_id = self.find_item_by_name(item_name, room.items)
        
        # Check bot inventories
        if not item_id:
            for bot in self.bots.values():
                if bot.room_id == user.room_id:
                    item_id = self.find_item_by_name(item_name, bot.inventory)
                    if item_id:
                        break
        
        if not item_id:
            return f"There is no '{item_name}' here."
        
        item = self.items[item_id]
        description = f"{item.name}: {item.description}"
        
        if item.tags:
            description += f"\nTags: {', '.join(item.tags)}"
        
        if item.is_container and item.contents:
            content_names = [self.items[cid].name for cid in item.contents 
                           if cid in self.items]
            if content_names:
                description += f"\nContains: {', '.join(content_names)}"
        
        return description
    
    async def handle_use_item(self, user, item_name):
        """Handle use item command"""
        item_id = self.find_item_by_name(item_name, user.inventory)
        if not item_id:
            return f"You don't have a '{item_name}' to use."
        
        item = self.items[item_id]
        if not item.script:
            return f"The {item.name} cannot be used."
        
        # Execute item script
        try:
            await self.script_engine.execute_script(item.script, user.name, user.room_id)
            return f"You use the {item.name}."
        except Exception as e:
            logger.error(f"Error executing item script: {e}")
            return f"The {item.name} doesn't work properly."
    
    def find_item_by_name(self, name, item_list):
        """Find item ID by name in a list of item IDs"""
        name_lower = name.lower()
        for item_id in item_list:
            if item_id in self.items:
                item = self.items[item_id]
                if name_lower in item.name.lower():
                    return item_id
        return None
    
    async def handle_teleport(self, user, room_id):
        """Handle admin teleport command"""
        if room_id not in self.rooms:
            return f"Room '{room_id}' does not exist."
        
        # Trigger leave room event
        await self.trigger_event(Event("leave_room", user.room_id, user.name))
        
        # Move user
        old_room = self.rooms.get(user.room_id)
        if old_room:
            old_room.users.discard(user.name)
        
        user.room_id = room_id
        self.rooms[room_id].users.add(user.name)
        
        # Show new room
        await self.show_room(user)
        
        # Trigger enter room event
        await self.trigger_event(Event("enter_room", user.room_id, user.name))
        
        logger.info(f"Admin '{user.name}' teleported to '{room_id}'")
        
        return None
    
    async def handle_broadcast(self, user, message):
        """Handle admin broadcast command"""
        broadcast_message = f"[BROADCAST] {user.name}: {message}"
        self.send_to_all_users(broadcast_message)
        
        logger.info(f"Admin '{user.name}' broadcast: {message}")
        
        return f"Broadcast sent: {message}"
    
    async def handle_execute_script(self, user, script_name):
        """Handle admin script execution command"""
        if script_name not in self.scripts:
            return f"Script '{script_name}' not found."
        
        script_data = self.scripts[script_name]
        bot_name = script_data.get('bot')
        script_code = script_data.get('script', '')
        
        if not bot_name or bot_name not in self.bots:
            return f"Bot '{bot_name}' not found for script '{script_name}'."
        
        bot = self.bots[bot_name]
        
        try:
            await self.script_engine.execute_script(script_code, bot_name, bot.room_id)
            logger.info(f"Admin '{user.name}' executed script '{script_name}'")
            return f"Script '{script_name}' executed."
        except Exception as e:
            logger.error(f"Error executing script '{script_name}': {e}")
            return f"Error executing script '{script_name}': {e}"
    
    async def check_bot_responses(self, room_id, message):
        """Check if any bots should respond to the message"""
        message_lower = message.lower()
        
        for bot in self.bots.values():
            if bot.room_id != room_id:
                continue
            
            for response_data in bot.responses:
                triggers = response_data.get('trigger', [])
                response = response_data.get('response', '')
                
                if any(trigger.lower() in message_lower for trigger in triggers):
                    self.send_to_room(room_id, f"{bot.name} says: {response}")
                    break
    
    async def trigger_event(self, event):
        """Trigger an event and execute associated scripts"""
        event_type = event.type
        
        if event_type not in self.event_handlers:
            return
        
        for script_name in self.event_handlers[event_type]:
            script_data = self.scripts.get(script_name)
            if not script_data:
                continue
            
            # Check if event matches script trigger
            trigger = script_data.get('trigger', {})
            if 'room' in trigger and trigger['room'] != event.room_id:
                continue
            
            bot_name = script_data.get('bot')
            script_code = script_data.get('script', '')
            
            if bot_name and bot_name in self.bots:
                bot = self.bots[bot_name]
                try:
                    await self.script_engine.execute_script(
                        script_code, bot_name, bot.room_id, 
                        event_data={'user': event.user_name}
                    )
                except Exception as e:
                    logger.error(f"Error executing event script '{script_name}': {e}")
    
    async def start_server(self, host='0.0.0.0', tcp_port=8888, web_port=5000):
        """Start the unified server"""
        # Get host and ports from environment for Railway
        host = os.getenv('HOST', host)
        tcp_port = int(os.getenv('TCP_PORT', tcp_port))
        
        # Railway uses PORT for web traffic
        web_port = int(os.getenv('PORT', os.getenv('WEB_PORT', web_port)))
        
        # Start TCP server
        tcp_server = await asyncio.start_server(
            self.handle_client, host, tcp_port
        )
        
        logger.info(f"TCP server started on {host}:{tcp_port}")
        
        # Start web server in a separate thread
        def run_web_server():
            self.socketio.run(self.app, host=host, port=web_port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
        
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        
        logger.info(f"Web server started on {host}:{web_port}")
        logger.info("Multi-User Text Space Server is running!")
        logger.info(f"Connect via: nc {host} {tcp_port} or http://{host}:{web_port}")
        
        # Keep TCP server running
        async with tcp_server:
            await tcp_server.serve_forever()

async def main():
    """Main function"""
    # Check if database should be used
    use_database = os.getenv('USE_DATABASE', 'false').lower() == 'true'
    
    server = TextSpaceServer(use_database=use_database)
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
