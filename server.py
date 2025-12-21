#!/usr/bin/env python3
import asyncio
import json
import yaml
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional
from script_engine import ScriptEngine
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading

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
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

class TextSpaceServer:
    def __init__(self):
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
        self.user_data_file = "users.json"
        self.load_rooms()
        self.load_bots()
        self.load_items()
        self.load_scripts()
        self.load_user_data()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'textspace-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.setup_web_routes()
    
    def load_rooms(self):
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
        except FileNotFoundError:
            # Create default lobby if no rooms file
            self.rooms['lobby'] = Room(
                id='lobby',
                name='The Lobby',
                description='A simple starting room.',
                exits={}
            )
    
    def load_bots(self):
        try:
            with open('bots.yaml', 'r') as f:
                data = yaml.safe_load(f)
                for bot_id, bot_data in data['bots'].items():
                    bot = Bot(
                        name=bot_data['name'],
                        room_id=bot_data['room'],
                        description=bot_data['description'],
                        responses=bot_data.get('responses', []),
                        visible=bot_data.get('visible', True),
                        inventory=bot_data.get('inventory', [])
                    )
                    self.bots[bot_id] = bot
        except FileNotFoundError:
            pass
    
    def load_items(self):
        try:
            with open('items.yaml', 'r') as f:
                data = yaml.safe_load(f)
                for item_id, item_data in data.get('items', {}).items():
                    self.items[item_id] = Item(
                        id=item_id,
                        name=item_data['name'],
                        description=item_data['description'],
                        tags=item_data.get('tags', []),
                        is_container=item_data.get('is_container', False),
                        script=item_data.get('script')
                    )
        except FileNotFoundError:
            pass
    
    def load_user_data(self):
        """Load persistent user data"""
        try:
            with open(self.user_data_file, 'r') as f:
                self.persistent_users = json.load(f)
        except FileNotFoundError:
            self.persistent_users = {}
    
    def save_user_data(self):
        """Save persistent user data"""
        try:
            with open(self.user_data_file, 'w') as f:
                json.dump(self.persistent_users, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user data: {e}")
    
    def save_user(self, user: User):
        """Save individual user's persistent data"""
        self.persistent_users[user.name] = {
            'room_id': user.room_id,
            'inventory': user.inventory,
            'admin': user.admin
        }
        self.save_user_data()
    
    def load_user(self, username: str) -> dict:
        """Load individual user's persistent data"""
        return self.persistent_users.get(username, {
            'room_id': 'lobby',
            'inventory': [],
            'admin': username == 'admin'
        })
    
    def load_scripts(self):
        try:
            with open('scripts.yaml', 'r') as f:
                data = yaml.safe_load(f)
                self.scripts = data.get('scripts', {})
                
                # Load event handlers
                for script_name, script_data in self.scripts.items():
                    event_trigger = script_data.get('trigger')
                    if event_trigger:
                        event_type = event_trigger.get('event')
                        if event_type:
                            if event_type not in self.event_handlers:
                                self.event_handlers[event_type] = []
                            self.event_handlers[event_type].append(script_name)
        except FileNotFoundError:
            pass
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {client_addr}")
        self.connections[writer] = None
        try:
            await self.send_message(writer, "Welcome to the Text Space! Enter your name: ")
            
            while True:
                data = await reader.readline()
                if not data:
                    break
                
                message = data.decode().strip()
                await self.process_command(writer, message)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            logger.info(f"Connection closed from {client_addr}")
            await self.disconnect_user(writer)
    
    async def process_command(self, writer: asyncio.StreamWriter, message: str):
        user_name = self.connections.get(writer)
        
        if not user_name:  # Not authenticated
            if message and message not in self.users:
                # Load persistent user data
                user_data = self.load_user(message)
                
                user = User(
                    name=message, 
                    writer=writer, 
                    authenticated=True, 
                    admin=user_data['admin'],
                    room_id=user_data['room_id'],
                    inventory=user_data['inventory'].copy()
                )
                self.users[message] = user
                self.connections[writer] = message
                self.rooms[user.room_id].users.add(message)
                logger.info(f"User '{message}' logged in{' (admin)' if user.admin else ''} at {user.room_id}")
                await self.send_room_info(writer, user.room_id)
                # Trigger enter event for initial room
                await self.trigger_event("enter_room", user.room_id, message)
            else:
                await self.send_message(writer, "Name taken or invalid. Try another: ")
            return
        
        # Authenticated user commands
        user = self.users[user_name]
        logger.debug(f"User '{user_name}' in '{user.room_id}': {message}")
        
        if message.startswith("quit"):
            logger.info(f"User '{user_name}' quit")
            await self.send_message(writer, "Goodbye!\n")
            writer.close()
        elif message.startswith("who"):
            users = ", ".join(self.users.keys())
            await self.send_message(writer, f"Online users: {users}\n> ")
        elif message.startswith("look"):
            await self.send_room_info(writer, user.room_id)
        elif message.startswith("help"):
            help_text = "Commands:\n"
            help_text += "  look - See room description\n"
            help_text += "  go <exit> or <exit> - Move to another room\n"
            help_text += "  say <message> - Speak to everyone here\n"
            help_text += "  whisper <user> <message> - Private message\n"
            help_text += "  who - List online users\n"
            help_text += "  inventory - Show your items\n"
            help_text += "  get <item> - Pick up an item\n"
            help_text += "  drop <item> - Drop an item\n"
            help_text += "  examine <item> - Look at an item closely\n"
            help_text += "  use <item> - Use an item\n"
            help_text += "  quit - Disconnect\n"
            if user.admin:
                help_text += "\nAdmin commands:\n"
                help_text += "  teleport [room] - Jump to room (no args lists rooms)\n"
                help_text += "  broadcast <message> - Message all users\n"
                help_text += "  script <name> - Execute bot script\n"
            help_text += "> "
            await self.send_message(writer, help_text)
        elif message.startswith("say "):
            text = message[4:].strip()
            logger.info(f"User '{user_name}' says in '{user.room_id}': {text}")
            await self.broadcast_to_room(user.room_id, f"{user_name} says: {text}", exclude=user_name)
            await self.send_message(writer, f"You say: {text}\n> ")
            # Check for bot responses
            await self.check_bot_responses(user.room_id, text, user_name)
        elif message.startswith("whisper "):
            parts = message[8:].split(' ', 1)
            if len(parts) < 2:
                await self.send_message(writer, "Usage: whisper <user> <message>\n> ")
            else:
                target, text = parts
                result = await self.send_whisper(user_name, target, text)
                if not result:
                    await self.send_message(writer, f"Could not whisper to '{target}'.\n> ")
        elif message.startswith("broadcast ") and user.admin:
            text = message[10:].strip()
            await self.broadcast_global(f"[ANNOUNCEMENT] {text}")
        elif message.startswith("script ") and user.admin:
            script_name = message[7:].strip()
            await self.run_script(script_name)
        elif message.startswith("teleport") and user.admin:
            args = message[8:].strip()
            if not args:
                # List available rooms
                rooms = ", ".join(self.rooms.keys())
                await self.send_message(writer, f"Available rooms: {rooms}\n> ")
            else:
                logger.info(f"Admin '{user_name}' teleporting to '{args}'")
                await self.teleport_user(user, args)
        elif message.startswith("inventory"):
            await self.show_inventory(user)
        elif message.startswith("get "):
            item_name = message[4:].strip()
            await self.get_item(user, item_name)
        elif message.startswith("drop "):
            item_name = message[5:].strip()
            await self.drop_item(user, item_name)
        elif message.startswith("examine "):
            item_name = message[8:].strip()
            await self.examine_item(user, item_name)
        elif message.startswith("use "):
            item_name = message[4:].strip()
            await self.use_item(user, item_name)
        elif message.startswith("go "):
            exit_name = message[3:].strip()
            await self.move_user(user, exit_name)
        else:
            # Try as direct exit name
            room = self.rooms[user.room_id]
            if message in room.exits:
                await self.move_user(user, message)
            else:
                await self.send_message(writer, f"Unknown command: {message}\n> ")
    
    async def send_room_info(self, writer: asyncio.StreamWriter, room_id: str):
        room = self.rooms[room_id]
        users_here = [name for name in room.users if name in self.users]
        others = [name for name in users_here if name != self.connections.get(writer)]
        
        # Get bots in this room
        bots_here = [bot.name for bot in self.bots.values() if bot.room_id == room_id and bot.visible]
        
        # Get items in this room
        items_here = [self.items[item_id].name for item_id in room.items if item_id in self.items]
        
        info = f"\n{room.name}\n{room.description}\n"
        
        if room.exits:
            exits = ", ".join(room.exits.keys())
            info += f"Exits: {exits}\n"
        
        if others:
            info += f"Others here: {', '.join(others)}\n"
        
        if bots_here:
            info += f"Bots here: {', '.join(bots_here)}\n"
        
        if items_here:
            info += f"Items here: {', '.join(items_here)}\n"
        
        info += "> "
        await self.send_message(writer, info)
    
    async def move_user(self, user: User, exit_name: str):
        current_room = self.rooms[user.room_id]
        
        if exit_name not in current_room.exits:
            await self.send_message(user.writer, f"No exit '{exit_name}' here.\n> ")
            return
        
        new_room_id = current_room.exits[exit_name]
        if new_room_id not in self.rooms:
            await self.send_message(user.writer, f"Exit leads nowhere.\n> ")
            return
        
        # Move user
        current_room.users.discard(user.name)
        
        # Trigger leave event
        await self.trigger_event("leave_room", user.room_id, user.name)
        
        user.room_id = new_room_id
        self.rooms[new_room_id].users.add(user.name)
        
        await self.send_room_info(user.writer, new_room_id)
        
        # Trigger enter event after room info is displayed
        await self.trigger_event("enter_room", new_room_id, user.name)
        
        # Save user location
        self.save_user(user)
    
    async def teleport_user(self, user: User, room_id: str):
        """Teleport user to any room (admin only)"""
        if room_id not in self.rooms:
            await self.send_message(user.writer, f"Room '{room_id}' not found.\n> ")
            return
        
        # Remove from current room
        current_room = self.rooms[user.room_id]
        current_room.users.discard(user.name)
        
        # Trigger leave event
        await self.trigger_event("leave_room", user.room_id, user.name)
        
        # Add to new room
        user.room_id = room_id
        self.rooms[room_id].users.add(user.name)
        
        await self.send_message(user.writer, f"*Teleported to {room_id}*\n")
        await self.send_room_info(user.writer, room_id)
        
        # Trigger enter event after room info is displayed
        await self.trigger_event("enter_room", room_id, user.name)
        
        # Save user location
        self.save_user(user)
    
    async def broadcast_to_room(self, room_id: str, message: str, exclude: str = None):
        room = self.rooms[room_id]
        for user_name in room.users:
            if user_name != exclude and user_name in self.users:
                user = self.users[user_name]
                await self.send_message(user.writer, f"{message}\n> ")
    
    async def send_whisper(self, sender: str, target: str, message: str):
        sender_user = self.users.get(sender)
        target_user = self.users.get(target)
        
        if not target_user:
            await self.send_message(sender_user.writer, f"User '{target}' not found.\n> ")
            return False
        
        # Check if target is in same room
        if target_user.room_id != sender_user.room_id:
            await self.send_message(sender_user.writer, f"{target} is not here.\n> ")
            return False
        
        await self.send_message(target_user.writer, f"{sender} whispers: {message}\n> ")
        await self.send_message(sender_user.writer, f"You whisper to {target}: {message}\n> ")
        return True
    
    async def broadcast_global(self, message: str):
        for user in self.users.values():
            await self.send_message(user.writer, f"{message}\n> ")
    
    async def check_bot_responses(self, room_id: str, message: str, speaker: str):
        message_lower = message.lower()
        
        # Check if message is directed at a specific bot
        directed_bot = None
        for bot in self.bots.values():
            if bot.room_id == room_id and bot.name.lower() in message_lower:
                directed_bot = bot
                break
        
        for bot in self.bots.values():
            if bot.room_id != room_id:
                continue
            
            # If message is directed at a specific bot, only that bot responds
            if directed_bot and directed_bot != bot:
                continue
            
            for response_data in bot.responses:
                triggers = response_data.get('trigger', [])
                if any(trigger in message_lower for trigger in triggers):
                    response = response_data.get('response', '')
                    await asyncio.sleep(1)  # Small delay for realism
                    await self.broadcast_to_room(room_id, f"{bot.name} says: {response}")
                    break  # Only one response per bot per message
    
    async def run_script(self, script_name: str):
        """Execute a named script"""
        if script_name in self.scripts:
            script_data = self.scripts[script_name]
            bot_name = script_data.get('bot')
            script_text = script_data.get('script', '')
            if bot_name and script_text:
                await self.script_engine.execute_script(script_text, bot_name)
    
    async def trigger_event(self, event_type: str, room_id: str, user_name: str):
        """Trigger event handlers for a specific event"""
        if event_type in self.event_handlers:
            for script_name in self.event_handlers[event_type]:
                script_data = self.scripts.get(script_name)
                if script_data:
                    # Check if event matches room condition
                    trigger = script_data.get('trigger', {})
                    target_room = trigger.get('room')
                    if not target_room or target_room == room_id:
                        bot_name = script_data.get('bot')
                        script_text = script_data.get('script', '')
                        if bot_name and script_text:
                            logger.info(f"Event '{event_type}' in '{room_id}' triggered script '{script_name}'")
                            await self.script_engine.execute_script(script_text, bot_name)
    
    async def show_inventory(self, user: User):
        """Show user's inventory"""
        if not user.inventory:
            await self.send_message(user.writer, "You are not carrying anything.\n> ")
            return
        
        items = [self.items[item_id].name for item_id in user.inventory if item_id in self.items]
        await self.send_message(user.writer, f"You are carrying: {', '.join(items)}\n> ")
    
    async def get_item(self, user: User, item_name: str):
        """Pick up an item from the room"""
        room = self.rooms[user.room_id]
        
        # Find item by name in room
        item_id = None
        for iid in room.items:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            await self.send_message(user.writer, f"There is no '{item_name}' here.\n> ")
            return
        
        # Move item from room to user
        room.items.remove(item_id)
        user.inventory.append(item_id)
        
        await self.send_message(user.writer, f"You pick up the {self.items[item_id].name}.\n> ")
        await self.broadcast_to_room(user.room_id, f"{user.name} picks up the {self.items[item_id].name}.", exclude=user.name)
        
        # Save user data
        self.save_user(user)
    
    async def drop_item(self, user: User, item_name: str):
        """Drop an item in the room"""
        # Find item by name in inventory
        item_id = None
        for iid in user.inventory:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            await self.send_message(user.writer, f"You don't have a '{item_name}'.\n> ")
            return
        
        # Move item from user to room
        user.inventory.remove(item_id)
        self.rooms[user.room_id].items.append(item_id)
        
        await self.send_message(user.writer, f"You drop the {self.items[item_id].name}.\n> ")
        await self.broadcast_to_room(user.room_id, f"{user.name} drops the {self.items[item_id].name}.", exclude=user.name)
        
        # Save user data
        self.save_user(user)
    
    async def examine_item(self, user: User, item_name: str):
        """Examine an item closely"""
        # Check inventory first, then room
        item_id = None
        location = "inventory"
        
        for iid in user.inventory:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            room = self.rooms[user.room_id]
            for iid in room.items:
                if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                    item_id = iid
                    location = "room"
                    break
        
        if not item_id:
            await self.send_message(user.writer, f"There is no '{item_name}' here or in your inventory.\n> ")
            return
        
        item = self.items[item_id]
        info = f"{item.name}: {item.description}"
        
        if item.tags:
            info += f"\nTags: {', '.join(item.tags)}"
        
        if item.is_container and item.contents:
            contents = [self.items[cid].name for cid in item.contents if cid in self.items]
            info += f"\nContains: {', '.join(contents)}"
        
        info += "\n> "
        await self.send_message(user.writer, info)
    
    async def use_item(self, user: User, item_name: str):
        """Use an item (execute its script if it has one)"""
        # Find item in inventory
        item_id = None
        for iid in user.inventory:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            await self.send_message(user.writer, f"You don't have a '{item_name}' to use.\n> ")
            return
        
        item = self.items[item_id]
        
        if item.script:
            await self.send_message(user.writer, f"You use the {item.name}.\n> ")
            # Execute item script (simplified - could be enhanced)
            await self.script_engine.execute_script(item.script, f"item_{item_id}")
        else:
            await self.send_message(user.writer, f"The {item.name} doesn't seem to do anything special.\n> ")
    
    def setup_web_routes(self):
        """Setup Flask routes and SocketIO handlers"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.socketio.on('connect')
        def on_connect():
            emit('message', {'text': 'Welcome to the Text Space! Enter your name:'})
        
        @self.socketio.on('login')
        def on_login(data):
            username = data['username'].strip()
            if not username or username in self.users or username in [u.name for u in self.web_users.values()]:
                emit('message', {'text': 'Name taken or invalid. Try another:'})
                return
            
            # Load persistent user data
            user_data = self.load_user(username)
            
            web_user = WebUser(
                name=username,
                session_id=request.sid,
                room_id=user_data['room_id'],
                authenticated=True,
                admin=user_data['admin'],
                inventory=user_data['inventory'].copy()
            )
            
            self.web_users[request.sid] = web_user
            self.web_sessions[request.sid] = username
            self.rooms[web_user.room_id].users.add(username)
            
            join_room(web_user.room_id)
            logger.info(f"Web user '{username}' logged in{' (admin)' if web_user.admin else ''} at {web_user.room_id}")
            self.send_web_room_info(web_user)
            
            # Trigger enter event
            asyncio.create_task(self.trigger_event("enter_room", web_user.room_id, username))
        
        @self.socketio.on('command')
        def on_command(data):
            if request.sid not in self.web_users:
                emit('message', {'text': 'Please login first.'})
                return
            
            web_user = self.web_users[request.sid]
            command = data['command'].strip()
            
            # Process web command
            asyncio.create_task(self.process_web_command(web_user, command))
        
        @self.socketio.on('disconnect')
        def on_disconnect():
            if request.sid in self.web_users:
                web_user = self.web_users[request.sid]
                self.rooms[web_user.room_id].users.discard(web_user.name)
                self.save_web_user(web_user)
                del self.web_users[request.sid]
                if request.sid in self.web_sessions:
                    del self.web_sessions[request.sid]
                logger.info(f"Web user '{web_user.name}' disconnected")
    
    async def process_web_command(self, web_user: WebUser, command: str):
        """Process commands from web users"""
        if command.startswith('look'):
            self.send_web_room_info(web_user)
        elif command.startswith('say '):
            text = command[4:].strip()
            logger.info(f"Web user '{web_user.name}' says in '{web_user.room_id}': {text}")
            self.socketio.emit('message', {'text': f'You say: {text}'}, room=request.sid)
            self.socketio.emit('message', {'text': f'{web_user.name} says: {text}'}, 
                             room=web_user.room_id, include_self=False)
            # Broadcast to TCP users too
            await self.broadcast_to_room(web_user.room_id, f"{web_user.name} says: {text}", exclude=web_user.name)
            await self.check_bot_responses(web_user.room_id, text, web_user.name)
        elif command.startswith('go ') or command in self.rooms[web_user.room_id].exits:
            exit_name = command[3:].strip() if command.startswith('go ') else command
            await self.move_web_user(web_user, exit_name)
        elif command == 'who':
            all_users = list(self.users.keys()) + [u.name for u in self.web_users.values()]
            self.socketio.emit('message', {'text': f'Online users: {", ".join(all_users)}'}, room=request.sid)
        elif command == 'inventory':
            await self.show_web_inventory(web_user)
        elif command.startswith('get '):
            item_name = command[4:].strip()
            await self.get_web_item(web_user, item_name)
        elif command.startswith('drop '):
            item_name = command[5:].strip()
            await self.drop_web_item(web_user, item_name)
        elif command.startswith('examine '):
            item_name = command[8:].strip()
            await self.examine_web_item(web_user, item_name)
        elif command.startswith('use '):
            item_name = command[4:].strip()
            await self.use_web_item(web_user, item_name)
        else:
            self.socketio.emit('message', {'text': f'Unknown command: {command}'}, room=request.sid)
    
    def send_web_room_info(self, web_user: WebUser):
        """Send room info to web user"""
        room = self.rooms[web_user.room_id]
        users_here = [name for name in room.users if name in self.users or name in [u.name for u in self.web_users.values()]]
        others = [name for name in users_here if name != web_user.name]
        bots_here = [bot.name for bot in self.bots.values() if bot.room_id == web_user.room_id and bot.visible]
        items_here = [self.items[item_id].name for item_id in room.items if item_id in self.items]
        
        self.socketio.emit('room_info', {
            'name': room.name,
            'description': room.description,
            'exits': list(room.exits.keys()),
            'users': others,
            'bots': bots_here,
            'items': items_here
        }, room=request.sid)
    
    async def move_web_user(self, web_user: WebUser, exit_name: str):
        """Move web user between rooms"""
        current_room = self.rooms[web_user.room_id]
        
        if exit_name not in current_room.exits:
            self.socketio.emit('message', {'text': f"No exit '{exit_name}' here."}, room=request.sid)
            return
        
        new_room_id = current_room.exits[exit_name]
        if new_room_id not in self.rooms:
            self.socketio.emit('message', {'text': "Exit leads nowhere."}, room=request.sid)
            return
        
        # Move user
        current_room.users.discard(web_user.name)
        leave_room(web_user.room_id)
        
        await self.trigger_event("leave_room", web_user.room_id, web_user.name)
        
        web_user.room_id = new_room_id
        self.rooms[new_room_id].users.add(web_user.name)
        join_room(new_room_id)
        
        self.send_web_room_info(web_user)
        await self.trigger_event("enter_room", new_room_id, web_user.name)
        self.save_web_user(web_user)
    
    async def show_web_inventory(self, web_user: WebUser):
        """Show web user's inventory"""
        if not web_user.inventory:
            self.socketio.emit('message', {'text': 'You are not carrying anything.'}, room=request.sid)
            return
        
        items = [self.items[item_id].name for item_id in web_user.inventory if item_id in self.items]
        self.socketio.emit('message', {'text': f'You are carrying: {", ".join(items)}'}, room=request.sid)
    
    async def get_web_item(self, web_user: WebUser, item_name: str):
        """Web user picks up item"""
        room = self.rooms[web_user.room_id]
        
        item_id = None
        for iid in room.items:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            self.socketio.emit('message', {'text': f"There is no '{item_name}' here."}, room=request.sid)
            return
        
        room.items.remove(item_id)
        web_user.inventory.append(item_id)
        
        self.socketio.emit('message', {'text': f'You pick up the {self.items[item_id].name}.'}, room=request.sid)
        self.socketio.emit('message', {'text': f'{web_user.name} picks up the {self.items[item_id].name}.'}, 
                          room=web_user.room_id, include_self=False)
        await self.broadcast_to_room(web_user.room_id, f"{web_user.name} picks up the {self.items[item_id].name}.", exclude=web_user.name)
        self.save_web_user(web_user)
    
    async def drop_web_item(self, web_user: WebUser, item_name: str):
        """Web user drops item"""
        item_id = None
        for iid in web_user.inventory:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            self.socketio.emit('message', {'text': f"You don't have a '{item_name}'."}, room=request.sid)
            return
        
        web_user.inventory.remove(item_id)
        self.rooms[web_user.room_id].items.append(item_id)
        
        self.socketio.emit('message', {'text': f'You drop the {self.items[item_id].name}.'}, room=request.sid)
        self.socketio.emit('message', {'text': f'{web_user.name} drops the {self.items[item_id].name}.'}, 
                          room=web_user.room_id, include_self=False)
        await self.broadcast_to_room(web_user.room_id, f"{web_user.name} drops the {self.items[item_id].name}.", exclude=web_user.name)
        self.save_web_user(web_user)
    
    async def examine_web_item(self, web_user: WebUser, item_name: str):
        """Web user examines item"""
        item_id = None
        location = "inventory"
        
        for iid in web_user.inventory:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            room = self.rooms[web_user.room_id]
            for iid in room.items:
                if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                    item_id = iid
                    location = "room"
                    break
        
        if not item_id:
            self.socketio.emit('message', {'text': f"There is no '{item_name}' here or in your inventory."}, room=request.sid)
            return
        
        item = self.items[item_id]
        info = f"{item.name}: {item.description}"
        
        if item.tags:
            info += f"\nTags: {', '.join(item.tags)}"
        
        if item.is_container and item.contents:
            contents = [self.items[cid].name for cid in item.contents if cid in self.items]
            info += f"\nContains: {', '.join(contents)}"
        
        self.socketio.emit('message', {'text': info}, room=request.sid)
    
    async def use_web_item(self, web_user: WebUser, item_name: str):
        """Web user uses item"""
        item_id = None
        for iid in web_user.inventory:
            if iid in self.items and self.items[iid].name.lower() == item_name.lower():
                item_id = iid
                break
        
        if not item_id:
            self.socketio.emit('message', {'text': f"You don't have a '{item_name}' to use."}, room=request.sid)
            return
        
        item = self.items[item_id]
        
        if item.script:
            self.socketio.emit('message', {'text': f'You use the {item.name}.'}, room=request.sid)
            await self.script_engine.execute_script(item.script, f"web_item_{item_id}")
        else:
            self.socketio.emit('message', {'text': f"The {item.name} doesn't seem to do anything special."}, room=request.sid)
    
    def save_web_user(self, web_user: WebUser):
        """Save web user's persistent data"""
        self.persistent_users[web_user.name] = {
            'room_id': web_user.room_id,
            'inventory': web_user.inventory,
            'admin': web_user.admin
        }
        self.save_user_data()
    
    async def send_message(self, writer: asyncio.StreamWriter, message: str):
        writer.write(message.encode())
        await writer.drain()
    
    async def disconnect_user(self, writer: asyncio.StreamWriter):
        user_name = self.connections.get(writer)
        if user_name and user_name in self.users:
            user = self.users[user_name]
            if user.room_id in self.rooms:
                self.rooms[user.room_id].users.discard(user_name)
            del self.users[user_name]
        if writer in self.connections:
            del self.connections[writer]
        writer.close()

async def main():
    server = TextSpaceServer()
    
    # Start TCP server
    tcp_server = await asyncio.start_server(
        server.handle_client, 'localhost', 8888
    )
    
    print("Text Space Server running on:")
    print("  TCP: localhost:8888 (terminal/nc)")
    print("  Web: localhost:5000 (browser)")
    print("Connect with: nc localhost 8888 or http://localhost:5000")
    logger.info("Text Space Server started - TCP:8888, Web:5000")
    
    # Start web server in a separate thread
    def run_web_server():
        server.socketio.run(server.app, host='localhost', port=5000, debug=False)
    
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Run TCP server
    async with tcp_server:
        await tcp_server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
