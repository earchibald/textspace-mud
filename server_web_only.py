#!/usr/bin/env python3
"""
The Text Spot - Web-Only Multi-User Text Space Server
Simplified version focused on web interface only
"""
import os
import json
import yaml
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional, List
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from script_engine import ScriptEngine

# Version tracking
VERSION = "2.0.11"

# Server configuration
SERVER_NAME = os.getenv("SERVER_NAME", "The Text Spot")

# Set up logging
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
    contents: list = None
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
    inventory: list = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

@dataclass
class Room:
    id: str
    name: str
    description: str
    exits: Dict[str, str]
    users: set = None
    items: list = None
    
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

class TextSpaceServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'textspace-secret-key')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Data storage
        self.rooms = {}
        self.items = {}
        self.bots = {}
        self.scripts = {}
        self.web_users = {}
        self.web_sessions = {}
        
        # Script engine
        self.script_engine = ScriptEngine(self)
        
        # Load data
        self.load_data()
        
        # Setup routes and handlers
        self.setup_web_routes()
        
        logger.info("Web-only Text Space Server initialized")
    
    def load_data(self):
        """Load all data from YAML files"""
        try:
            # Load rooms
            with open('rooms.yaml', 'r') as f:
                rooms_data = yaml.safe_load(f)
                for room_id, room_data in rooms_data['rooms'].items():
                    self.rooms[room_id] = Room(
                        id=room_id,
                        name=room_data['name'],
                        description=room_data['description'],
                        exits=room_data.get('exits', {}),
                        items=room_data.get('items', [])
                    )
            logger.info(f"Loaded {len(self.rooms)} rooms")
            
            # Load items
            with open('items.yaml', 'r') as f:
                items_data = yaml.safe_load(f)
                for item_id, item_data in items_data['items'].items():
                    self.items[item_id] = Item(
                        id=item_id,
                        name=item_data['name'],
                        description=item_data['description'],
                        tags=item_data.get('tags', []),
                        is_container=item_data.get('is_container', False),
                        contents=item_data.get('contents', []),
                        script=item_data.get('script')
                    )
            logger.info(f"Loaded {len(self.items)} items")
            
            # Load bots
            with open('bots.yaml', 'r') as f:
                bots_data = yaml.safe_load(f)
                for bot_name, bot_data in bots_data['bots'].items():
                    self.bots[bot_name] = Bot(
                        name=bot_name,
                        room_id=bot_data['room'],
                        description=bot_data['description'],
                        responses=bot_data.get('responses', []),
                        visible=bot_data.get('visible', True),
                        inventory=bot_data.get('inventory', [])
                    )
            logger.info(f"Loaded {len(self.bots)} bots")
            
            # Load scripts
            with open('scripts.yaml', 'r') as f:
                scripts_data = yaml.safe_load(f)
                self.scripts = scripts_data.get('scripts', {})
            logger.info(f"Loaded {len(self.scripts)} scripts")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def setup_web_routes(self):
        """Setup Flask routes and SocketIO handlers"""
        @self.app.route('/')
        def index():
            return render_template('index.html', server_name=SERVER_NAME)
        
        # REST API routes
        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            return jsonify({
                'running': True,
                'version': VERSION,
                'users_online': len(self.web_users),
                'rooms_count': len(self.rooms),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/config/<config_type>', methods=['GET'])
        def api_get_config(config_type):
            try:
                if config_type == 'rooms':
                    return jsonify({'rooms': {k: v.__dict__ for k, v in self.rooms.items()}})
                elif config_type == 'bots':
                    return jsonify({'bots': {k: v.__dict__ for k, v in self.bots.items()}})
                elif config_type == 'items':
                    return jsonify({'items': {k: v.__dict__ for k, v in self.items.items()}})
                elif config_type == 'scripts':
                    return jsonify({'scripts': self.scripts})
                else:
                    return jsonify({'error': 'Invalid config type'}), 400
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config/<config_type>', methods=['POST'])
        def api_update_config(config_type):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Create backup and update
                import shutil
                backup_file = f'{config_type}.yaml.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                shutil.copy(f'{config_type}.yaml', backup_file)
                
                # Write new config
                with open(f'{config_type}.yaml', 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
                
                # Reload configuration
                if config_type == 'rooms':
                    self.load_rooms()
                elif config_type == 'bots':
                    self.load_bots()
                elif config_type == 'items':
                    self.load_items()
                elif config_type == 'scripts':
                    self.load_scripts()
                
                return jsonify({'success': True, 'message': f'{config_type} configuration updated', 'backup': backup_file})
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/version', methods=['POST'])
        def api_increment_version():
            try:
                # Read current version
                with open('server_web_only.py', 'r') as f:
                    content = f.read()
                
                # Increment version
                import re
                version_match = re.search(r'VERSION = "(\d+)\.(\d+)\.(\d+)"', content)
                if version_match:
                    major, minor, patch = map(int, version_match.groups())
                    new_version = f"{major}.{minor}.{patch + 1}"
                    
                    new_content = re.sub(
                        r'VERSION = "\d+\.\d+\.\d+"',
                        f'VERSION = "{new_version}"',
                        content
                    )
                    
                    with open('server_web_only.py', 'w') as f:
                        f.write(new_content)
                    
                    return jsonify({'success': True, 'version': new_version})
                else:
                    return jsonify({'error': 'Version not found'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs', methods=['GET'])
        def api_get_logs():
            try:
                lines = request.args.get('lines', 50, type=int)
                with open('textspace.log', 'r') as f:
                    log_lines = f.readlines()
                recent_logs = ''.join(log_lines[-lines:])
                return jsonify({'logs': recent_logs})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Web client connected: {request.sid}")
            emit('message', {'text': f'✅ Connected to {SERVER_NAME} v{VERSION}. Enter your username to begin.'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Web client disconnected: {request.sid}")
            if request.sid in self.web_sessions:
                username = self.web_sessions[request.sid]
                if username in self.web_users:
                    self.handle_user_disconnect(username, request.sid)
        
        @self.socketio.on('login')
        def handle_login(data):
            username = data.get('username', '').strip()
            if not username:
                emit('login_response', {'success': False, 'message': 'Username required'})
                return
            
            admin = username == "admin" or username == "tester-admin"
            web_user = WebUser(
                name=username,
                session_id=request.sid,
                authenticated=True,
                admin=admin
            )
            
            # Load user data
            user_data = self.load_user_data(username)
            if user_data:
                web_user.room_id = user_data.get('room_id', 'lobby')
                web_user.inventory = user_data.get('inventory', [])
            
            self.web_users[username] = web_user
            self.web_sessions[request.sid] = username
            
            # Add to room
            if web_user.room_id in self.rooms:
                self.rooms[web_user.room_id].users.add(username)
            
            join_room(web_user.room_id)
            
            # Notify room of player entering
            self.send_to_room(web_user.room_id, f"📥 {username} enters the room.", exclude_user=username)
            
            logger.info(f"Web user '{username}' logged in (admin: {admin})")
            
            emit('login_response', {'success': True, 'admin': admin})
            emit('message', {'text': f'Welcome, {username}! Type "help" for commands.'})
            
            # Send room description (implicit look)
            room_desc = self.get_room_description(web_user.room_id, username)
            emit('message', {'text': room_desc})
        
        @self.socketio.on('command')
        def handle_command(data):
            if request.sid not in self.web_sessions:
                # Check if this might be a login attempt
                command = data.get('command', '').strip()
                if command and not any(c in command for c in [' ', '\t']):
                    handle_login({'username': command})
                    return
                else:
                    emit('message', {'text': 'Not logged in'})
                    return
            
            username = self.web_sessions[request.sid]
            command = data.get('command', '').strip()
            
            if command:
                try:
                    response = self.process_command(username, command)
                    if response:
                        emit('message', {'text': response})
                except Exception as e:
                    logger.error(f"Error processing command: {e}")
                    emit('message', {'text': f'Error: {str(e)}'})
        
        @self.socketio.on('user_switched')
        def handle_user_switched(data):
            # Update stored username when user switches
            pass  # Handled by client-side JavaScript
    
    def process_command(self, username, command):
        """Process user command"""
        if username not in self.web_users:
            return "User not found"
        
        web_user = self.web_users[username]
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle quote alias for say
        if cmd.startswith('"') and len(cmd) > 1:
            # Extract message after quote
            message = cmd[1:] + (" " + " ".join(args) if args else "")
            return self.handle_say(web_user, message.strip())
        
        # Most-significant match command parsing
        cmd = self.resolve_command(cmd, web_user.admin)
        
        # Handle ambiguous commands
        if cmd.startswith("AMBIGUOUS:"):
            matches = cmd.split(":")[1].split(",")
            return f"Ambiguous command. Did you mean: {', '.join(matches)}?"
        
        # Basic commands
        if cmd == "help":
            return self.get_help_text(web_user.admin)
        elif cmd == "version":
            return f"The Text Spot v{VERSION}"
        elif cmd == "whoami":
            admin_status = " (admin)" if web_user.admin else ""
            return f"You are: {web_user.name}{admin_status}"
        elif cmd == "look":
            return self.get_room_description(web_user.room_id, username)
        elif cmd == "who":
            return self.get_who_list()
        elif cmd == "inventory":
            return self.get_inventory(web_user)
        elif cmd == "say" and args:
            message = " ".join(args)
            return self.handle_say(web_user, message)
        elif cmd == "whisper" and len(args) >= 2:
            target = args[0]
            message = " ".join(args[1:])
            return self.handle_whisper(web_user, target, message)
        elif cmd in ["get", "take"] and args:
            item_name = " ".join(args)
            return self.handle_get_item(web_user, item_name)
        elif cmd == "drop" and args:
            item_name = " ".join(args)
            return self.handle_drop_item(web_user, item_name)
        elif cmd in ["examine", "exam"] and args:
            item_name = " ".join(args)
            return self.handle_examine_item(web_user, item_name)
        elif cmd == "use" and args:
            item_name = " ".join(args)
            return self.handle_use_item(web_user, item_name)
        elif cmd == "open" and args:
            item_name = " ".join(args)
            return self.handle_open_item(web_user, item_name)
        elif cmd == "close" and args:
            item_name = " ".join(args)
            return self.handle_close_item(web_user, item_name)
        elif cmd in ["go", "move"] and args:
            direction = args[0]
            return self.move_user(web_user, direction)
        elif cmd in ["north", "south", "east", "west"]:
            return self.move_user(web_user, cmd)
        
        # Admin commands
        elif cmd == "teleport" and web_user.admin:
            if args:
                return self.handle_teleport(web_user, args[0])
            else:
                return "Available rooms: " + ", ".join(self.rooms.keys())
        elif cmd == "broadcast" and web_user.admin and args:
            message = " ".join(args)
            return self.handle_broadcast(web_user, message)
        elif cmd == "kick" and web_user.admin and args:
            target_user = args[0]
            return self.handle_kick_user(web_user, target_user)
        elif cmd == "switchuser" and web_user.admin and args:
            if not web_user.admin:
                return "Access denied. Admin privileges required."
            new_username = args[0]
            result = self.handle_switch_user(web_user, new_username)
            emit('user_switched', {'username': new_username})
            return result
        
        return f"Unknown command: {cmd}. Type 'help' for available commands."
    
    def resolve_command(self, cmd, is_admin):
        """Resolve command using most-significant match"""
        # Define all available commands
        basic_commands = [
            'help', 'version', 'whoami', 'look', 'who', 'inventory', 'say', 'whisper',
            'get', 'take', 'drop', 'examine', 'exam', 'use', 'go', 'move',
            'north', 'south', 'east', 'west'
        ]
        
        admin_commands = ['teleport', 'broadcast', 'kick', 'switchuser']
        
        # Single-letter aliases (exact matches only)
        aliases = {
            'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
            'l': 'look', 'g': 'go', 'i': 'inventory', 'h': 'help', 'v': 'version'
        }
        
        # Check exact alias match first (only for single letters)
        if len(cmd) == 1 and cmd in aliases:
            return aliases[cmd]
        
        # Build command list based on user privileges
        all_commands = basic_commands[:]
        if is_admin:
            all_commands.extend(admin_commands)
        
        # Find exact match
        if cmd in all_commands:
            return cmd
        
        # Find partial matches
        matches = [c for c in all_commands if c.startswith(cmd)]
        
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            return f"AMBIGUOUS:{','.join(matches)}"
        else:
            return cmd  # Return original if no matches
    
    def get_help_text(self, is_admin):
        """Get help text for user"""
        help_text = """
Available commands:
  look (l) - See room description and contents
  go <exit> (g) - Move to another room (or just type the exit name)
  north/south/east/west (n/s/e/w) - Move in cardinal directions
  say <message> (") - Speak to everyone in the room
  whisper <user> <message> - Send private message to user
  who - List all online users
  whoami - Show your username and admin status
  inventory (i) - Show your items
  get <item> - Pick up an item
  drop <item> - Drop an item
  examine <item> - Look at an item closely
  use <item> - Use an item
  open <item> - Open a container
  close <item> - Close a container
  help (h) - Show this help
  version (v) - Show server version
"""
        
        if is_admin:
            help_text += """
Admin commands:
  teleport [room] - Jump to room (no args lists rooms)
  broadcast <message> - Send message to all users
  kick <user> - Disconnect a user
  switchuser <name> - Switch to different user
"""
        
        return help_text.strip()
    
    def get_room_description(self, room_id, username):
        """Get room description"""
        room = self.rooms.get(room_id)
        if not room:
            return "You are in an unknown location."
        
        lines = []
        lines.append(room.name)
        lines.append(room.description)
        
        if room.exits:
            exits = ", ".join(room.exits.keys())
            lines.append(f"Exits: {exits}")
        
        other_users = [u for u in room.users if u != username]
        if other_users:
            lines.append(f"Users here: {', '.join(other_users)}")
        
        bots_here = [bot.name for bot in self.bots.values() 
                    if bot.room_id == room_id and bot.visible]
        if bots_here:
            lines.append(f"Bots here: {', '.join(bots_here)}")
        
        items_here = [self.items[item_id].name for item_id in room.items 
                     if item_id in self.items]
        if items_here:
            lines.append(f"Items here: {', '.join(items_here)}")
        
        return "\n".join(lines)
    
    def get_who_list(self):
        """Get list of online users"""
        users = list(self.web_users.keys())
        if users:
            return f"Online users ({len(users)}): {', '.join(users)}"
        else:
            return "No users online."
    
    def get_inventory(self, web_user):
        """Get user inventory"""
        if not web_user.inventory:
            return "You are not carrying anything."
        
        item_names = [self.items[item_id].name for item_id in web_user.inventory 
                     if item_id in self.items]
        return f"You are carrying: {', '.join(item_names)}"
    
    def handle_say(self, web_user, message):
        """Handle say command"""
        room_message = f"{web_user.name} says: {message}"
        self.send_to_room(web_user.room_id, room_message, exclude_user=web_user.name)
        return f"You say: {message}"
    
    def handle_whisper(self, web_user, target_username, message):
        """Handle whisper command"""
        if target_username not in self.web_users:
            return f"User '{target_username}' not found."
        
        target_user = self.web_users[target_username]
        
        # Send whisper to target
        whisper_message = f"{web_user.name} whispers: {message}"
        emit('message', {'text': whisper_message}, room=target_user.session_id)
        
        return f"You whisper to {target_username}: {message}"
    
    def move_user(self, web_user, direction):
        """Move user to another room with partial matching"""
        current_room = self.rooms.get(web_user.room_id)
        if not current_room:
            return "You are in an unknown location."
        
        # Find matching exits (exact match first, then partial)
        matching_exits = []
        exact_match = None
        
        for exit_name in current_room.exits:
            if exit_name == direction:
                exact_match = exit_name
                break
            elif exit_name.startswith(direction):
                matching_exits.append(exit_name)
        
        # Use exact match if found
        if exact_match:
            target_exit = exact_match
        elif len(matching_exits) == 1:
            target_exit = matching_exits[0]
        elif len(matching_exits) > 1:
            return f"Ambiguous direction '{direction}'. Options: {', '.join(matching_exits)}"
        else:
            return f"You can't go {direction} from here."
        
        target_room_id = current_room.exits[target_exit]
        if target_room_id not in self.rooms:
            return f"The {target_exit} exit leads nowhere."
        
        # Move user
        current_room.users.discard(web_user.name)
        web_user.room_id = target_room_id
        self.rooms[target_room_id].users.add(web_user.name)
        
        # Notify rooms of player movement
        self.send_to_room(current_room.id, f"📤 {web_user.name} leaves the room.", exclude_user=web_user.name)
        self.send_to_room(target_room_id, f"📥 {web_user.name} enters the room.", exclude_user=web_user.name)
        
        # Save user data
        self.save_user_data(web_user)
        
        return self.get_room_description(target_room_id, web_user.name)
    
    def handle_kick_user(self, admin_user, target_username):
        """Handle kicking a user"""
        if target_username == admin_user.name:
            return "You cannot kick yourself."
        
        if target_username in self.web_users:
            web_user = self.web_users[target_username]
            
            # Remove from room
            if web_user.room_id in self.rooms:
                self.rooms[web_user.room_id].users.discard(target_username)
            
            # Remove from users dict
            del self.web_users[target_username]
            if web_user.session_id in self.web_sessions:
                del self.web_sessions[web_user.session_id]
            
            # Send message and disconnect
            emit('message', {'text': 'You have been disconnected by an administrator.'}, 
                 room=web_user.session_id)
            disconnect(web_user.session_id)
            
            return f"Kicked user: {target_username}"
        
        return f"User '{target_username}' not found."
    
    def handle_switch_user(self, web_user, new_username):
        """Handle user switching"""
        if not new_username:
            return "Usage: switchuser <username>"
        
        # Remove from current room
        if web_user.room_id in self.rooms:
            self.rooms[web_user.room_id].users.discard(web_user.name)
        
        # Remove from users dict
        if web_user.name in self.web_users:
            del self.web_users[web_user.name]
        
        # Create new user
        admin = new_username == "admin"
        new_web_user = WebUser(
            name=new_username,
            session_id=web_user.session_id,
            authenticated=True,
            admin=admin
        )
        
        # Load user data
        user_data = self.load_user_data(new_username)
        if user_data:
            new_web_user.room_id = user_data.get('room_id', 'lobby')
            new_web_user.inventory = user_data.get('inventory', [])
        
        # Update session
        self.web_users[new_username] = new_web_user
        self.web_sessions[web_user.session_id] = new_username
        
        # Add to room
        if new_web_user.room_id in self.rooms:
            self.rooms[new_web_user.room_id].users.add(new_username)
        
        # Notify room of player entering
        self.send_to_room(new_web_user.room_id, f"📥 {new_username} enters the room.", exclude_user=new_username)
        
        return f"Switched to user: {new_username}. " + self.get_room_description(new_web_user.room_id, new_username)
    
    def handle_teleport(self, web_user, room_id):
        """Handle teleport command"""
        if room_id not in self.rooms:
            return f"Room '{room_id}' not found."
        
        # Remove from current room
        if web_user.room_id in self.rooms:
            self.rooms[web_user.room_id].users.discard(web_user.name)
        
        # Move to new room
        web_user.room_id = room_id
        self.rooms[room_id].users.add(web_user.name)
        
        # Save user data
        self.save_user_data(web_user)
        
        return self.get_room_description(room_id, web_user.name)
    
    def handle_broadcast(self, web_user, message):
        """Handle broadcast command"""
        broadcast_message = f"📢 {web_user.name} broadcasts: {message}"
        self.send_to_all(broadcast_message, exclude_user=web_user.name)
        return f"Broadcast sent: {message}"
    
    def handle_get_item(self, web_user, item_name):
        """Handle getting an item"""
        room = self.rooms.get(web_user.room_id)
        if not room:
            return "You are in an unknown location."
        
        # Check for items in open containers first
        for room_item_id in room.items:
            if room_item_id in self.items:
                container = self.items[room_item_id]
                if container.is_container and hasattr(container, 'is_open') and container.is_open:
                    for content_id in container.contents:
                        if content_id in self.items:
                            item = self.items[content_id]
                            if item.name.lower() == item_name.lower():
                                # Move item from container to inventory
                                container.contents.remove(content_id)
                                web_user.inventory.append(content_id)
                                self.save_user_data(web_user)
                                self.send_to_room(web_user.room_id, f"{web_user.name} takes {item.name} from {container.name}.", exclude_user=web_user.name)
                                return f"You take {item.name} from {container.name}."
        
        # Find item in room
        item_id = None
        for room_item_id in room.items:
            if room_item_id in self.items:
                item = self.items[room_item_id]
                if item.name.lower() == item_name.lower():
                    # Check if item is immovable
                    if "immovable" in item.tags:
                        return f"The {item.name} is too heavy to move."
                    item_id = room_item_id
                    break
        
        if not item_id:
            return f"There is no '{item_name}' here."
        
        # Move item from room to inventory
        room.items.remove(item_id)
        web_user.inventory.append(item_id)
        
        # Save user data
        self.save_user_data(web_user)
        
        # Notify room
        item = self.items[item_id]
        self.send_to_room(web_user.room_id, f"{web_user.name} picks up {item.name}.", exclude_user=web_user.name)
        
        return f"You pick up {item.name}."
    
    def handle_drop_item(self, web_user, item_name):
        """Handle dropping an item"""
        # Find item in inventory
        item_id = None
        for inv_item_id in web_user.inventory:
            if inv_item_id in self.items:
                item = self.items[inv_item_id]
                if item.name.lower() == item_name.lower():
                    item_id = inv_item_id
                    break
        
        if not item_id:
            return f"You don't have '{item_name}'."
        
        # Move item from inventory to room
        web_user.inventory.remove(item_id)
        room = self.rooms.get(web_user.room_id)
        if room:
            room.items.append(item_id)
        
        # Save user data
        self.save_user_data(web_user)
        
        # Notify room
        item = self.items[item_id]
        self.send_to_room(web_user.room_id, f"{web_user.name} drops {item.name}.", exclude_user=web_user.name)
        
        return f"You drop {item.name}."
    
    def handle_examine_item(self, web_user, item_name):
        """Handle examining an item"""
        # Check inventory first
        for item_id in web_user.inventory:
            if item_id in self.items:
                item = self.items[item_id]
                if item.name.lower() == item_name.lower():
                    return f"{item.name}: {item.description}"
        
        # Check room items
        room = self.rooms.get(web_user.room_id)
        if room:
            for item_id in room.items:
                if item_id in self.items:
                    item = self.items[item_id]
                    if item.name.lower() == item_name.lower():
                        return f"{item.name}: {item.description}"
        
        return f"You don't see '{item_name}' here."
    
    def handle_use_item(self, web_user, item_name):
        """Handle using an item"""
        # Find item in inventory
        for item_id in web_user.inventory:
            if item_id in self.items:
                item = self.items[item_id]
                if item.name.lower() == item_name.lower():
                    if item.script:
                        # Execute item script
                        try:
                            result = self.script_engine.execute_script(item.script, {
                                'user': web_user.name,
                                'room': web_user.room_id,
                                'item': item_id
                            })
                            return result if result else f"You use {item.name}."
                        except Exception as e:
                            logger.error(f"Script error: {e}")
                            return f"You use {item.name}."
                    else:
                        return f"You use {item.name}."
        
        return f"You don't have '{item_name}'."

    def handle_open_item(self, web_user, item_name):
        """Handle opening a container"""
        room = self.rooms.get(web_user.room_id)
        if not room:
            return "You are in an unknown location."
        
        # Find container in room
        for item_id in room.items:
            if item_id in self.items:
                item = self.items[item_id]
                if item.name.lower() == item_name.lower():
                    if not item.is_container:
                        return f"You can't open {item.name}."
                    
                    if hasattr(item, 'is_open') and item.is_open:
                        return f"The {item.name} is already open."
                    
                    # Open the container
                    item.is_open = True
                    self.send_to_room(web_user.room_id, f"{web_user.name} opens {item.name}.", exclude_user=web_user.name)
                    
                    # Show contents
                    if item.contents:
                        contents = [self.items[content_id].name for content_id in item.contents if content_id in self.items]
                        return f"You open {item.name}. Inside you see: {', '.join(contents)}."
                    else:
                        return f"You open {item.name}. It is empty."
        
        return f"You don't see '{item_name}' here."
    
    def handle_close_item(self, web_user, item_name):
        """Handle closing a container"""
        room = self.rooms.get(web_user.room_id)
        if not room:
            return "You are in an unknown location."
        
        # Find container in room
        for item_id in room.items:
            if item_id in self.items:
                item = self.items[item_id]
                if item.name.lower() == item_name.lower():
                    if not item.is_container:
                        return f"You can't close {item.name}."
                    
                    if not hasattr(item, 'is_open') or not item.is_open:
                        return f"The {item.name} is already closed."
                    
                    # Close the container
                    item.is_open = False
                    self.send_to_room(web_user.room_id, f"{web_user.name} closes {item.name}.", exclude_user=web_user.name)
                    return f"You close {item.name}."
        
        return f"You don't see '{item_name}' here."

    def send_to_room(self, room_id, message, exclude_user=None):
        """Send message to all users in a room"""
        if room_id not in self.rooms:
            return
        
        for username in self.rooms[room_id].users:
            if username != exclude_user and username in self.web_users:
                web_user = self.web_users[username]
                emit('message', {'text': message}, room=web_user.session_id)
    
    def send_to_all(self, message, exclude_user=None):
        """Send message to all users"""
        for username, web_user in self.web_users.items():
            if username != exclude_user:
                emit('message', {'text': message}, room=web_user.session_id)
    
    def handle_user_disconnect(self, username, session_id):
        """Handle user disconnect"""
        if username in self.web_users:
            web_user = self.web_users[username]
            
            # Notify room of player leaving
            if web_user.room_id in self.rooms:
                self.send_to_room(web_user.room_id, f"📤 {username} leaves the room.", exclude_user=username)
                self.rooms[web_user.room_id].users.discard(username)
            
            # Save user data
            self.save_user_data(web_user)
            
            # Remove from active users
            del self.web_users[username]
        
        if session_id in self.web_sessions:
            del self.web_sessions[session_id]
        
        logger.info(f"User '{username}' disconnected")
    
    def load_user_data(self, username):
        """Load user data from file"""
        try:
            with open('users.json', 'r') as f:
                users_data = json.load(f)
                return users_data.get(username)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            return None
    
    def save_user_data(self, web_user):
        """Save user data to file"""
        try:
            # Load existing data
            try:
                with open('users.json', 'r') as f:
                    users_data = json.load(f)
            except FileNotFoundError:
                users_data = {}
            
            # Update user data
            users_data[web_user.name] = {
                'room_id': web_user.room_id,
                'inventory': web_user.inventory,
                'admin': web_user.admin,
                'last_seen': datetime.now().isoformat()
            }
            
            # Save data
            with open('users.json', 'w') as f:
                json.dump(users_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
    
    def run(self):
        """Start the web server"""
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 8080))
        
        logger.info(f"Starting {SERVER_NAME} v{VERSION}")
        logger.info(f"Web server starting on {host}:{port}")
        
        self.socketio.run(self.app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    server = TextSpaceServer()
    server.run()
