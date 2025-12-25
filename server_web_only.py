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
from config_manager import ConfigManager
from command_registry import Command, CommandRegistry
from functools import wraps

# Version tracking
VERSION = "2.9.1"

# Server configuration
SERVER_NAME = os.getenv("SERVER_NAME", "The Text Spot")

# IP Whitelist for API endpoints
API_WHITELIST = ["98.33.93.100"]

def require_whitelisted_ip(f):
    """Decorator to restrict API access to whitelisted IPs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        if client_ip not in API_WHITELIST:
            return jsonify({"error": "Access denied"}), 403
        return f(*args, **kwargs)
    return decorated_function

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
        
        # Get port from Railway environment
        self.port = int(os.getenv('PORT', 8080))
        
        # Data storage
        self.rooms = {}
        self.items = {}
        self.bots = {}
        self.scripts = {}
        self.web_users = {}
        self.web_sessions = {}
        self.motd = ""  # Message of the Day
        
        # MCP session management
        self.mcp_sessions = {}  # Track MCP user sessions
        self.mcp_current_user = None  # Current active MCP user
        
        # Command registry
        self.command_registry = CommandRegistry()
        self.setup_commands()
        
        # Configuration manager
        try:
            self.config_manager = ConfigManager()
            
            # Initialize persistent config on Railway
            if os.getenv('RAILWAY_ENVIRONMENT_NAME'):
                self.config_manager.initialize_persistent_config()
                self.config_manager.create_symlinks()
        except Exception as e:
            logger.warning(f"Config manager initialization failed: {e}")
            self.config_manager = None
        
        # Script engine
        self.script_engine = ScriptEngine(self)
        
        # Load data
        self.load_data()
        
        # Setup routes and handlers
        self.setup_web_routes()
        
        logger.info("Web-only Text Space Server initialized")
    
    def setup_commands(self):
        """Setup command registry with all available commands"""
        # Basic commands
        self.command_registry.register(Command("help", self.handle_help, usage="help"))
        self.command_registry.register(Command("version", self.handle_version, usage="version"))
        self.command_registry.register(Command("whoami", self.handle_whoami, usage="whoami"))
        self.command_registry.register(Command("look", self.handle_look_cmd, usage="look [target]", aliases=["l", "examine", "exam"], arg_types=["examinable"]))
        self.command_registry.register(Command("who", self.handle_who, usage="who"))
        self.command_registry.register(Command("inventory", self.handle_inventory, usage="inventory", aliases=["i"]))
        
        # Communication commands
        self.command_registry.register(Command("say", self.handle_say_cmd, args_required=1, usage="say <message>"))
        self.command_registry.register(Command("whisper", self.handle_whisper_cmd, args_required=2, usage="whisper <target> <message>", arg_types=["user", "message"]))
        
        # Item commands with contextual completion
        self.command_registry.register(Command("get", self.handle_get_cmd, args_required=1, usage="get <item>", aliases=["take"], arg_types=["room_item"]))
        self.command_registry.register(Command("drop", self.handle_drop_cmd, args_required=1, usage="drop <item>", arg_types=["inventory_item"]))
        self.command_registry.register(Command("put", self.handle_put_cmd, args_required=1, usage="put <item> [in <container>]", arg_types=["inventory_item", "preposition", "open_container"]))
        self.command_registry.register(Command("give", self.handle_give_cmd, args_required=1, usage="give <item> to <target>", arg_types=["inventory_item", "preposition", "give_target"]))
        self.command_registry.register(Command("look", self.handle_look_cmd, usage="look [target]", aliases=["l", "examine", "exam"], arg_types=["examinable"]))
        self.command_registry.register(Command("use", self.handle_use_cmd, args_required=1, usage="use <item>", arg_types=["inventory_item"]))
        self.command_registry.register(Command("open", self.handle_open_cmd, args_required=1, usage="open <item>", arg_types=["openable"]))
        self.command_registry.register(Command("close", self.handle_close_cmd, args_required=1, usage="close <item>", arg_types=["closeable"]))
        
        # Movement commands
        self.command_registry.register(Command("go", self.handle_go_cmd, args_required=1, usage="go <direction>", aliases=["move", "g"], arg_types=["direction"]))
        self.command_registry.register(Command("north", self.handle_north, usage="north", aliases=["n"]))
        self.command_registry.register(Command("south", self.handle_south, usage="south", aliases=["s"]))
        self.command_registry.register(Command("east", self.handle_east, usage="east", aliases=["e"]))
        self.command_registry.register(Command("west", self.handle_west, usage="west", aliases=["w"]))
        
        # Admin commands
        self.command_registry.register(Command("teleport", self.handle_teleport_cmd, admin_only=True, usage="teleport [room]", arg_types=["room"]))
        self.command_registry.register(Command("broadcast", self.handle_broadcast_cmd, admin_only=True, args_required=1, usage="broadcast <message>"))
        self.command_registry.register(Command("kick", self.handle_kick_cmd, admin_only=True, args_required=1, usage="kick <username>", arg_types=["user"]))
        self.command_registry.register(Command("switchuser", self.handle_switchuser_cmd, admin_only=True, args_required=1, usage="switchuser <username>", arg_types=["user"]))
        self.command_registry.register(Command("script", self.handle_script_cmd, admin_only=True, args_required=1, usage="script <name>", arg_types=["script"]))
        
        # MOTD command (different usage for admin vs user)
        self.command_registry.register(Command("motd", self.handle_motd_cmd, usage="motd"))
        
        # Quit/logout command
        self.command_registry.register(Command("quit", self.handle_quit_cmd, usage="quit", aliases=["logout"]))
        self.command_registry.register(Command("script", self.handle_script_cmd, admin_only=True, args_required=1, usage="script <name>", arg_types=["script"]))
    
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
            
            # Load MOTD
            self.load_motd()
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def load_motd(self):
        """Load MOTD from file"""
        try:
            with open('motd.txt', 'r') as f:
                self.motd = f.read().strip()
            logger.info(f"Loaded MOTD: {self.motd[:50]}..." if len(self.motd) > 50 else f"Loaded MOTD: {self.motd}")
        except FileNotFoundError:
            self.motd = ""
            logger.info("No MOTD file found, using empty MOTD")
        except Exception as e:
            logger.error(f"Error loading MOTD: {e}")
            self.motd = ""
    
    def save_motd(self):
        """Save MOTD to file"""
        try:
            with open('motd.txt', 'w') as f:
                f.write(self.motd)
            logger.info(f"Saved MOTD: {self.motd[:50]}..." if len(self.motd) > 50 else f"Saved MOTD: {self.motd}")
        except Exception as e:
            logger.error(f"Error saving MOTD: {e}")
    
    def setup_web_routes(self):
        """Setup Flask routes and SocketIO handlers"""
        @self.app.route('/')
        def index():
            return render_template('index.html', server_name=SERVER_NAME)
        
        # REST API routes (IP restricted)
        @self.app.route('/api/status', methods=['GET'])
        @require_whitelisted_ip
        def api_status():
            return jsonify({
                'running': True,
                'version': VERSION,
                'users_online': len(self.web_users),
                'rooms_count': len(self.rooms),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/restart', methods=['POST'])
        @require_whitelisted_ip
        def api_restart():
            logger.info("Server restart requested via API")
            # In a production environment, this would trigger a graceful restart
            # For now, we'll just return success
            return jsonify({"message": "Server restart initiated", "status": "success"})
        
        @self.app.route('/api/shutdown', methods=['POST'])
        @require_whitelisted_ip
        def api_shutdown():
            logger.info("Server shutdown requested via API")
            # In a production environment, this would trigger a graceful shutdown
            # For now, we'll just return success
            return jsonify({"message": "Server shutdown initiated", "status": "success"})
        
        @self.app.route('/api/config/<config_type>', methods=['GET'])
        @require_whitelisted_ip
        def api_get_config(config_type):
            try:
                if config_type == 'rooms':
                    # Read from file instead of objects
                    with open('rooms.yaml', 'r') as f:
                        data = yaml.safe_load(f.read())
                    return jsonify(data)
                elif config_type == 'bots':
                    with open('bots.yaml', 'r') as f:
                        data = yaml.safe_load(f.read())
                    return jsonify(data)
                elif config_type == 'items':
                    with open('items.yaml', 'r') as f:
                        data = yaml.safe_load(f.read())
                    return jsonify(data)
                elif config_type == 'scripts':
                    with open('scripts.yaml', 'r') as f:
                        data = yaml.safe_load(f.read())
                    return jsonify(data)
                else:
                    return jsonify({'error': 'Invalid config type'}), 400
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config/<config_type>', methods=['POST'])
        @require_whitelisted_ip
        def api_update_config(config_type):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Validate config type
                if config_type not in ['rooms', 'bots', 'items', 'scripts']:
                    return jsonify({'error': 'Invalid config type'}), 400
                
                # Create backup and update
                import shutil
                backup_file = f'{config_type}.yaml.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                shutil.copy(f'{config_type}.yaml', backup_file)
                
                # Write new config
                with open(f'{config_type}.yaml', 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
                
                # Reload configuration
                self.load_data()  # Reload all data
                
                return jsonify({
                    'success': True, 
                    'message': f'{config_type} configuration updated', 
                    'backup': backup_file
                })
                    
            except Exception as e:
                logger.error(f"Config update error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/version', methods=['POST'])
        @require_whitelisted_ip
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
        @require_whitelisted_ip
        def api_get_logs():
            try:
                lines = request.args.get('lines', 50, type=int)
                with open('textspace.log', 'r') as f:
                    log_lines = f.readlines()
                recent_logs = ''.join(log_lines[-lines:])
                return jsonify({'logs': recent_logs})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config/reset/<config_type>', methods=['POST'])
        @require_whitelisted_ip
        def api_reset_config(config_type):
            try:
                data = request.get_json()
                confirmation_code = data.get('confirmation_code', '')
                
                if not confirmation_code:
                    # Return required confirmation code
                    from datetime import datetime
                    required_code = f"RESET_{config_type.upper()}_{datetime.now().strftime('%Y%m%d')}"
                    return jsonify({
                        'error': 'Confirmation code required',
                        'required_code': required_code,
                        'warning': 'This will PERMANENTLY reset the configuration to default examples'
                    }), 400
                
                if self.config_manager:
                    result = self.config_manager.reset_config_with_confirmation(config_type, confirmation_code)
                    
                    if result['success']:
                        # Reload server data after reset
                        self.load_data()
                        return jsonify(result)
                    else:
                        return jsonify(result), 400
                else:
                    return jsonify({'error': 'Config manager not available'}), 500
                    
            except Exception as e:
                logger.error(f"Config reset error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config/info', methods=['GET'])
        def api_config_info():
            try:
                if self.config_manager:
                    info = self.config_manager.get_config_info()
                    return jsonify(info)
                else:
                    return jsonify({'error': 'Config manager not available', 'fallback_mode': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/completions', methods=['GET'])
        def api_completions():
            """Get command completions for tab completion"""
            try:
                partial = request.args.get('partial', '').lower()
                username = request.args.get('user', '')
                full_text = request.args.get('text', partial)  # Full command text for context
                
                logger.info(f"Completions request: partial='{partial}', user='{username}', text='{full_text}'")
                
                completions = []
                if username in self.web_users:
                    web_user = self.web_users[username]
                    logger.info(f"Found user {username}, admin={web_user.admin}")
                else:
                    # Create temporary user context for completion
                    admin = username == "admin" or username == "tester-admin"
                    web_user = WebUser(name=username, session_id="", admin=admin, room_id="lobby")
                    logger.info(f"Created temporary user context for {username}, admin={admin}")
                
                # Parse the full text to determine if we're completing a command or argument
                words = full_text.strip().split()
                logger.info(f"Parsed words: {words}, length: {len(words)}")
                
                # If we have a space at the end or multiple words, we're completing arguments
                is_argument_completion = len(words) > 1 or (full_text.endswith(' ') and len(words) >= 1)
                logger.info(f"Is argument completion: {is_argument_completion}")
                
                if not is_argument_completion:
                    # Completing command name
                    logger.info("Completing command name")
                    
                    # For empty partial, show formatted help-style output
                    if not partial:
                        # Create organized command help
                        help_text = "Available Commands:\n\n"
                        help_text += "  Basic:        help, version, whoami, who, motd, quit (logout)\n"
                        help_text += "  Look:         look (l, examine, exam) [target]\n"
                        help_text += "  Items:        get (take) <item>, drop <item>, use <item>\n"
                        help_text += "  Complex:      put <item> [in <container>], give <item> to <target>\n"
                        help_text += "  Interact:     open <item>, close <item>\n"
                        help_text += "  Chat:         say <message>, whisper <target> <message>\n"
                        help_text += "  Movement:     go (move, g) <direction>, north (n), south (s), east (e), west (w)\n"
                        help_text += "  Inventory:    inventory (i)\n"
                        
                        if web_user.admin:
                            help_text += "\n  Admin:        teleport [room], motd [message]"
                        
                        completions = [{
                            'name': 'help_display',
                            'usage': help_text,
                            'aliases': [],
                            'admin_only': False,
                            'type': 'help'
                        }]
                    else:
                        # Normal partial matching
                        for cmd_name, cmd in self.command_registry.commands.items():
                            # Check admin permissions
                            if cmd.admin_only and not web_user.admin:
                                continue
                            
                            # Check if command matches partial
                            if cmd_name.startswith(partial):
                                completions.append({
                                    'name': cmd_name,
                                    'usage': cmd.usage,
                                    'aliases': cmd.aliases,
                                    'admin_only': cmd.admin_only
                                })
                            
                            # Check aliases too (separate from main command check)
                            for alias in cmd.aliases:
                                if alias.startswith(partial) and alias not in [c['name'] for c in completions]:
                                    completions.append({
                                        'name': alias,
                                        'usage': cmd.usage,
                                        'aliases': [],
                                        'admin_only': cmd.admin_only
                                    })
                
                else:
                    # Completing command argument
                    logger.info("Completing command argument")
                    cmd_name = words[0].lower()
                    resolved_cmd = self.resolve_command(cmd_name, web_user.admin)
                    logger.info(f"Command: {cmd_name}, resolved: {resolved_cmd}")
                    
                    # Handle ambiguous commands
                    if resolved_cmd.startswith("AMBIGUOUS:"):
                        matches = resolved_cmd.split(":")[1].split(",")
                        if len(matches) == 2:
                            resolved_cmd = matches[0]
                    
                    command_def = self.command_registry.get_command(resolved_cmd)
                    logger.info(f"Command def: {command_def}, arg_types: {command_def.arg_types if command_def else None}")
                    
                    if command_def and command_def.arg_types:
                        # Special handling for complex grammar commands
                        if command_def.name in ['put', 'give']:
                            completions.extend(self.get_complex_completions(username, command_def.name, words, partial, full_text))
                        else:
                            # Standard argument completion
                            # Determine which argument we're completing
                            if full_text.endswith(' '):
                                # Starting a new argument
                                arg_index = len(words) - 1
                            else:
                                # Completing current argument
                                arg_index = len(words) - 2
                            
                            logger.info(f"Argument index: {arg_index}")
                            
                            if arg_index < len(command_def.arg_types):
                                arg_type = command_def.arg_types[arg_index]
                                logger.info(f"Argument type: {arg_type}")
                                context_items = self.get_completion_context(username, arg_type)
                                logger.info(f"Context items: {context_items}")
                                
                                # Filter context items by partial match
                                for item in context_items:
                                    if item.lower().startswith(partial):
                                        completions.append({
                                            'name': item,
                                            'usage': f"{command_def.name} {item}",
                                            'aliases': [],
                                            'admin_only': False,
                                            'type': 'argument'
                                        })
                
                logger.info(f"Returning {len(completions)} completions")
                return jsonify({'completions': completions})
            except Exception as e:
                logger.error(f"Completions API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/motd', methods=['GET'])
        @require_whitelisted_ip
        def api_get_motd():
            """Get current MOTD"""
            try:
                return jsonify({'motd': self.motd})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/motd', methods=['POST'])
        @require_whitelisted_ip
        def api_set_motd():
            """Set MOTD via API"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                new_motd = data.get('motd', '')
                self.motd = new_motd
                self.save_motd()
                
                return jsonify({
                    'success': True,
                    'motd': self.motd,
                    'message': 'MOTD updated successfully'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/mcp/login', methods=['POST'])
        @require_whitelisted_ip
        def api_mcp_login():
            """MCP login - establish user session"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                username = data.get('username', '').strip()
                if not username:
                    return jsonify({'error': 'Username required'}), 400
                
                admin = data.get('admin', False) or username == "admin" or username == "tester-admin"
                
                # Create WebUser instance
                web_user = WebUser(
                    name=username,
                    session_id=f"mcp_{username}",
                    authenticated=True,
                    admin=admin,
                    room_id='lobby'
                )
                
                # Load user data if exists
                user_data = self.load_user_data(username)
                if user_data:
                    web_user.room_id = user_data.get('room_id', 'lobby')
                    web_user.inventory = user_data.get('inventory', [])
                
                # Add to web_users and sessions
                self.web_users[username] = web_user
                self.web_sessions[web_user.session_id] = username
                
                # Add to room
                if web_user.room_id in self.rooms:
                    self.rooms[web_user.room_id].users.add(username)
                
                # Track MCP session
                self.mcp_sessions[username] = {
                    'session_id': web_user.session_id,
                    'admin': admin,
                    'room_id': web_user.room_id,
                    'login_time': datetime.now().isoformat()
                }
                self.mcp_current_user = username
                
                logger.info(f"MCP user '{username}' logged in (admin: {admin})")
                
                return jsonify({
                    'success': True,
                    'username': username,
                    'admin': admin,
                    'room_id': web_user.room_id,
                    'message': f'MCP user {username} logged in successfully'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/mcp/logout', methods=['POST'])
        @require_whitelisted_ip
        def api_mcp_logout():
            """MCP logout - close current session"""
            try:
                if not self.mcp_current_user:
                    return jsonify({'error': 'No active MCP session'}), 400
                
                username = self.mcp_current_user
                
                # Clean up user state
                if username in self.web_users:
                    web_user = self.web_users[username]
                    
                    # Remove from room
                    if web_user.room_id in self.rooms:
                        self.rooms[web_user.room_id].users.discard(username)
                    
                    # Save user data
                    self.save_user_data(web_user)
                    
                    # Remove from web_users and sessions
                    del self.web_users[username]
                    if web_user.session_id in self.web_sessions:
                        del self.web_sessions[web_user.session_id]
                
                # Clean up MCP session
                if username in self.mcp_sessions:
                    del self.mcp_sessions[username]
                self.mcp_current_user = None
                
                logger.info(f"MCP user '{username}' logged out")
                
                return jsonify({
                    'success': True,
                    'message': f'MCP user {username} logged out successfully'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/mcp/status', methods=['GET'])
        @require_whitelisted_ip
        def api_mcp_status():
            """MCP status - show current session info"""
            try:
                if not self.mcp_current_user:
                    return jsonify({
                        'logged_in': False,
                        'message': 'No active MCP session'
                    })
                
                username = self.mcp_current_user
                session_info = self.mcp_sessions.get(username, {})
                
                user_info = {
                    'logged_in': True,
                    'username': username,
                    'admin': session_info.get('admin', False),
                    'room_id': session_info.get('room_id', 'unknown'),
                    'login_time': session_info.get('login_time', 'unknown'),
                    'session_id': session_info.get('session_id', 'unknown')
                }
                
                # Add inventory info if user exists
                if username in self.web_users:
                    web_user = self.web_users[username]
                    user_info['inventory'] = [self.items[item_id].name for item_id in web_user.inventory if item_id in self.items]
                    user_info['room_name'] = self.rooms[web_user.room_id].name if web_user.room_id in self.rooms else 'Unknown'
                
                return jsonify(user_info)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/command', methods=['POST'])
        @require_whitelisted_ip
        def api_send_command():
            """Send command via MCP with session awareness"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                command = data.get('command', '').strip()
                username = data.get('username', '').strip()
                
                if not command:
                    return jsonify({'error': 'Command required'}), 400
                
                # Check for active MCP session first
                if self.mcp_current_user and username == self.mcp_current_user:
                    # Use existing MCP session
                    if username in self.web_users:
                        result = self.process_command(username, command)
                        return jsonify({
                            'success': True,
                            'result': result,
                            'username': username,
                            'session_type': 'mcp_logged_in'
                        })
                
                # Fall back to temporary user context
                result = self.process_command(username, command)
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'username': username,
                    'session_type': 'temporary'
                })
                
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
            
            emit('login_response', {'success': True, 'admin': admin, 'username': username})
            emit('message', {'text': f'Welcome, {username}! Type "help" for commands.'})
            
            # Show MOTD if set
            if self.motd:
                emit('message', {'text': f'📢 Message of the Day:\n{self.motd}'})
            
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
        """Process user command using generalized command registry"""
        if username not in self.web_users:
            return "User not found"
        
        web_user = self.web_users[username]
        parts = command.split()
        if not parts:
            return "Please enter a command. Type 'help' for available commands."
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle quote alias for say
        if cmd.startswith('"') and len(cmd) > 1:
            message = cmd[1:] + (" " + " ".join(args) if args else "")
            return self.handle_say(web_user, message.strip())
        
        # Resolve command using existing logic
        resolved_cmd = self.resolve_command(cmd, web_user.admin)
        
        # Handle ambiguous commands
        if resolved_cmd.startswith("AMBIGUOUS:"):
            matches = resolved_cmd.split(":")[1].split(",")
            if len(matches) == 2:
                resolved_cmd = matches[0]
            else:
                return f"Ambiguous command. Did you mean: {', '.join(matches)}?"
        
        # Get command from registry
        command_def = self.command_registry.get_command(resolved_cmd)
        if command_def:
            # Check admin permissions
            if command_def.admin_only and not web_user.admin:
                return "Access denied. Admin privileges required."
            
            # Check argument requirements
            if len(args) < command_def.args_required:
                return f"Usage: {command_def.usage}"
            
            # Execute command
            try:
                return command_def.handler(web_user, args)
            except Exception as e:
                logger.error(f"Error executing command {resolved_cmd}: {e}")
                return f"Error executing command: {str(e)}"
        
        return f"Unknown command: {cmd}. Type 'help' for available commands."
    
    def get_completion_context(self, username, arg_type):
        """Get contextual completion options based on argument type"""
        if username not in self.web_users:
            return []
        
        web_user = self.web_users[username]
        room = self.rooms.get(web_user.room_id)
        
        if arg_type == "room_item":
            # Items available in the current room (including items in open containers)
            if room:
                available_items = []
                # Direct room items
                for item_id in room.items:
                    if item_id in self.items:
                        available_items.append(self.items[item_id].name)
                        # Check if this item is an open container
                        item = self.items[item_id]
                        if item.is_container and hasattr(item, 'is_open') and item.is_open:
                            # Add items from open container
                            for content_id in item.contents:
                                if content_id in self.items:
                                    available_items.append(self.items[content_id].name)
                return available_items
        
        elif arg_type == "inventory_item":
            # Items in user's inventory
            return [self.items[item_id].name for item_id in web_user.inventory if item_id in self.items]
        
        elif arg_type == "examinable":
            # Items that can be examined (room items + inventory + users + bots + items in open containers)
            examinable = []
            if room:
                # Room items (including items in open containers)
                for item_id in room.items:
                    if item_id in self.items:
                        examinable.append(self.items[item_id].name)
                        # Check if this item is an open container
                        item = self.items[item_id]
                        if item.is_container and hasattr(item, 'is_open') and item.is_open:
                            # Add items from open container
                            for content_id in item.contents:
                                if content_id in self.items:
                                    examinable.append(self.items[content_id].name)
                # Other users in room
                examinable.extend([user for user in room.users if user != username])
                # Bots in room (visibility depends on user permissions)
                for bot in self.bots.values():
                    if bot.room_id == web_user.room_id:
                        if bot.visible or web_user.admin:
                            examinable.append(bot.name)
            # User's inventory
            examinable.extend([self.items[item_id].name for item_id in web_user.inventory if item_id in self.items])
            return examinable
        
        elif arg_type == "openable" or arg_type == "closeable":
            # Items that can be opened/closed (room items + inventory)
            openable = []
            if room:
                openable.extend([self.items[item_id].name for item_id in room.items if item_id in self.items])
            openable.extend([self.items[item_id].name for item_id in web_user.inventory if item_id in self.items])
            return openable
        
        elif arg_type == "open_container":
            # Containers that are currently open
            open_containers = []
            if room:
                for item_id in room.items:
                    if item_id in self.items:
                        item = self.items[item_id]
                        if item.is_container and hasattr(item, 'is_open') and item.is_open:
                            open_containers.append(item.name)
            return open_containers
        
        elif arg_type == "give_target":
            # Users and bots that can receive items
            targets = []
            if room:
                # Other users in room
                targets.extend([user for user in room.users if user != username])
                # Visible bots in room
                for bot in self.bots.values():
                    if bot.room_id == web_user.room_id:
                        if bot.visible or web_user.admin:
                            targets.append(bot.name)
            return targets
        
        elif arg_type == "preposition":
            # Context-aware preposition suggestions
            return ["in", "to"]
        
        elif arg_type == "direction":
            # Available exits from current room
            if room and room.exits:
                return list(room.exits.keys())
        
        elif arg_type == "room":
            # All available rooms (admin only)
            if web_user.admin:
                return list(self.rooms.keys())
        
        elif arg_type == "user":
            # All online users
            return list(self.web_users.keys())
        
        elif arg_type == "script":
            # Available scripts (admin only)
            if web_user.admin:
                return list(self.scripts.keys())
        
        return []
    
    def get_complex_completions(self, username, command_name, words, partial, full_text):
        """Get completions for complex grammar commands (put, give)"""
        completions = []
        
        if command_name == "put":
            # put ITEM [in CONTAINER]
            if len(words) == 1:  # "put "
                # Completing the item name
                items = self.get_completion_context(username, "inventory_item")
                for item in items:
                    if item.lower().startswith(partial):
                        completions.append({
                            'name': item,
                            'usage': f"put {item}",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'argument'
                        })
            elif len(words) == 2:  # "put ITEM"
                if full_text.endswith(' '):
                    # Suggest "in" and available containers
                    if "in".startswith(partial):
                        completions.append({
                            'name': 'in',
                            'usage': f"put {words[1]} in <container>",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'preposition'
                        })
                    # Also suggest open containers directly
                    containers = self.get_completion_context(username, "open_container")
                    for container in containers:
                        if container.lower().startswith(partial):
                            completions.append({
                                'name': container,
                                'usage': f"put {words[1]} in {container}",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'container'
                            })
                else:
                    # Completing the item name
                    items = self.get_completion_context(username, "inventory_item")
                    for item in items:
                        if item.lower().startswith(partial):
                            completions.append({
                                'name': item,
                                'usage': f"put {item}",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'argument'
                            })
            elif len(words) >= 3 and words[2] == "in":
                # "put ITEM in CONTAINER"
                containers = self.get_completion_context(username, "open_container")
                for container in containers:
                    if container.lower().startswith(partial):
                        completions.append({
                            'name': container,
                            'usage': f"put {words[1]} in {container}",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'argument'
                        })
        
        elif command_name == "give":
            # give ITEM to TARGET
            if len(words) == 1:  # "give "
                # Completing the item name
                items = self.get_completion_context(username, "inventory_item")
                for item in items:
                    if item.lower().startswith(partial):
                        completions.append({
                            'name': item,
                            'usage': f"give {item}",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'argument'
                        })
            elif len(words) == 2:  # "give ITEM"
                if full_text.endswith(' '):
                    # Suggest "to" and available targets
                    if "to".startswith(partial):
                        completions.append({
                            'name': 'to',
                            'usage': f"give {words[1]} to <target>",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'preposition'
                        })
                    # Also suggest targets directly
                    targets = self.get_completion_context(username, "give_target")
                    for target in targets:
                        if target.lower().startswith(partial):
                            completions.append({
                                'name': target,
                                'usage': f"give {words[1]} to {target}",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'target'
                            })
                else:
                    # Completing the item name
                    items = self.get_completion_context(username, "inventory_item")
                    for item in items:
                        if item.lower().startswith(partial):
                            completions.append({
                                'name': item,
                                'usage': f"give {item}",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'argument'
                            })
            elif len(words) >= 3 and words[2] == "to":
                # "give ITEM to TARGET"
                targets = self.get_completion_context(username, "give_target")
                for target in targets:
                    if target.lower().startswith(partial):
                        completions.append({
                            'name': target,
                            'usage': f"give {words[1]} to {target}",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'argument'
                        })
        
        return completions
    
    # Command handler methods for registry
    def handle_help(self, web_user, args):
        return self.get_help_text(web_user.admin)
    
    def handle_version(self, web_user, args):
        return f"The Text Spot v{VERSION}"
    
    def handle_whoami(self, web_user, args):
        admin_status = " (admin)" if web_user.admin else ""
        return f"You are: {web_user.name}{admin_status}"
    
    def handle_look(self, web_user, args):
        return self.get_room_description(web_user.room_id, web_user.name)
    
    def handle_look_cmd(self, web_user, args):
        """Handle look command - room description or examine target"""
        if not args:
            # Bare 'look' - show room description
            return self.get_room_description(web_user.room_id, web_user.name)
        else:
            # 'look <target>' - examine the target
            target_name = " ".join(args)
            return self.handle_examine_target(web_user, target_name)
    
    def handle_examine_target(self, web_user, target_name):
        """Handle examining a specific target (items, users, bots)"""
        # Check inventory first
        for item_id in web_user.inventory:
            if item_id in self.items:
                item = self.items[item_id]
                if item.name.lower() == target_name.lower():
                    return f"{item.name}: {item.description}"
        
        # Check room items (including items in open containers)
        room = self.rooms.get(web_user.room_id)
        if room:
            # Check direct room items
            for item_id in room.items:
                if item_id in self.items:
                    item = self.items[item_id]
                    if item.name.lower() == target_name.lower():
                        return f"{item.name}: {item.description}"
            
            # Check items in open containers
            for item_id in room.items:
                if item_id in self.items:
                    container = self.items[item_id]
                    if container.is_container and hasattr(container, 'is_open') and container.is_open:
                        for content_id in container.contents:
                            if content_id in self.items:
                                item = self.items[content_id]
                                if item.name.lower() == target_name.lower():
                                    return f"{item.name}: {item.description}"
            
            # Check other users in room
            for user_name in room.users:
                if user_name != web_user.name and user_name.lower() == target_name.lower():
                    if user_name in self.web_users:
                        target_user = self.web_users[user_name]
                        admin_status = " (admin)" if target_user.admin else ""
                        return f"{user_name}{admin_status}: Another player exploring the space."
                    return f"{user_name}: Another visitor to this place."
            
            # Check bots in room (visibility depends on user permissions)
            for bot in self.bots.values():
                if bot.room_id == web_user.room_id:
                    if bot.name.lower() == target_name.lower():
                        # Regular users can only examine visible bots, admins can examine all
                        if bot.visible or web_user.admin:
                            visibility_note = " (invisible)" if not bot.visible else ""
                            return f"{bot.name}{visibility_note}: {bot.description}"
        
        return f"You don't see '{target_name}' here."
    
    def handle_who(self, web_user, args):
        return self.get_who_list()
    
    def handle_inventory(self, web_user, args):
        return self.get_inventory(web_user)
    
    def handle_say_cmd(self, web_user, args):
        message = " ".join(args)
        return self.handle_say(web_user, message)
    
    def handle_whisper_cmd(self, web_user, args):
        target = args[0]
        message = " ".join(args[1:])
        return self.handle_whisper(web_user, target, message)
    
    def handle_get_cmd(self, web_user, args):
        item_name = " ".join(args)
        return self.handle_get_item(web_user, item_name)
    
    def handle_drop_cmd(self, web_user, args):
        item_name = " ".join(args)
        return self.handle_drop_item(web_user, item_name)
    
    def handle_examine_cmd(self, web_user, args):
        """Legacy examine command - redirect to look"""
        target_name = " ".join(args)
        return self.handle_examine_target(web_user, target_name)
    
    def handle_use_cmd(self, web_user, args):
        item_name = " ".join(args)
        return self.handle_use_item(web_user, item_name)
    
    def handle_open_cmd(self, web_user, args):
        item_name = " ".join(args)
        return self.handle_open_item(web_user, item_name)
    
    def handle_close_cmd(self, web_user, args):
        item_name = " ".join(args)
        return self.handle_close_item(web_user, item_name)
    
    def handle_go_cmd(self, web_user, args):
        direction = args[0]
        return self.move_user(web_user, direction)
    
    def handle_north(self, web_user, args):
        return self.move_user(web_user, "north")
    
    def handle_south(self, web_user, args):
        return self.move_user(web_user, "south")
    
    def handle_east(self, web_user, args):
        return self.move_user(web_user, "east")
    
    def handle_west(self, web_user, args):
        return self.move_user(web_user, "west")
    
    def handle_teleport_cmd(self, web_user, args):
        if args:
            return self.handle_teleport(web_user, args[0])
        else:
            return "Available rooms: " + ", ".join(self.rooms.keys())
    
    def handle_broadcast_cmd(self, web_user, args):
        message = " ".join(args)
        return self.handle_broadcast(web_user, message)
    
    def handle_kick_cmd(self, web_user, args):
        target_user = args[0]
        return self.handle_kick_user(web_user, target_user)
    
    def handle_switchuser_cmd(self, web_user, args):
        new_username = args[0]
        result = self.handle_switch_user(web_user, new_username)
        emit('user_switched', {'username': new_username})
        return result
    
    def handle_script_cmd(self, web_user, args):
        script_name = args[0]
        return self.handle_execute_script(web_user, script_name)
    
    def handle_motd_cmd(self, web_user, args):
        """Handle MOTD command - view or set message of the day"""
        if not args:
            # View current MOTD
            if self.motd:
                return f"📢 Message of the Day:\n{self.motd}"
            else:
                return "📢 No message of the day is currently set."
        else:
            # Set MOTD (admin only)
            if not web_user.admin:
                return "❌ Only administrators can set the message of the day."
            
            new_motd = " ".join(args)
            self.motd = new_motd
            self.save_motd()
            
            if new_motd:
                return f"📢 Message of the day updated:\n{new_motd}"
            else:
                return "📢 Message of the day cleared."
    
    def parse_complex_command(self, args):
        """Parse complex commands with prepositions using pattern matching"""
        # Convert to string for easier parsing
        args_str = " ".join(args)
        
        # Handle put ITEM in CONTAINER
        if " in " in args_str:
            parts = args_str.split(" in ", 1)
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                return "put_in", [parts[0].strip(), parts[1].strip()]
        
        # Handle give ITEM to TARGET
        if " to " in args_str:
            parts = args_str.split(" to ", 1)
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                return "give_to", [parts[0].strip(), parts[1].strip()]
        
        # Handle put ITEM (simple drop)
        if args:
            return "put_simple", [args_str.strip()]
        
        # No match
        return "unknown", args
    
    def handle_put_cmd(self, web_user, args):
        """Handle put command with complex grammar"""
        command_type, parsed_args = self.parse_complex_command(args)
        
        match command_type:
            case "put_simple":
                # put ITEM (same as drop)
                return self.handle_drop_item(web_user, parsed_args[0])
            case "put_in":
                # put ITEM in CONTAINER
                return self.handle_put_in_container(web_user, parsed_args[0], parsed_args[1])
            case _:
                return f"Usage: put <item> [in <container>]"
    
    def handle_give_cmd(self, web_user, args):
        """Handle give command with complex grammar"""
        command_type, parsed_args = self.parse_complex_command(args)
        
        match command_type:
            case "give_to":
                # give ITEM to TARGET
                return self.handle_give_to_target(web_user, parsed_args[0], parsed_args[1])
            case _:
                return f"Usage: give <item> to <target>"
    
    def handle_put_in_container(self, web_user, item_name, container_name):
        """Handle putting an item into a container"""
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
        
        # Find container in room
        room = self.rooms.get(web_user.room_id)
        if not room:
            return "You are in an unknown location."
        
        container_id = None
        for room_item_id in room.items:
            if room_item_id in self.items:
                container = self.items[room_item_id]
                if container.name.lower() == container_name.lower():
                    if not container.is_container:
                        return f"You can't put things in {container.name}."
                    if not (hasattr(container, 'is_open') and container.is_open):
                        return f"The {container.name} is closed."
                    container_id = room_item_id
                    break
        
        if not container_id:
            return f"You don't see '{container_name}' here."
        
        # Move item from inventory to container
        web_user.inventory.remove(item_id)
        self.items[container_id].contents.append(item_id)
        self.save_user_data(web_user)
        
        item = self.items[item_id]
        container = self.items[container_id]
        self.send_to_room(web_user.room_id, f"{web_user.name} puts {item.name} in {container.name}.", exclude_user=web_user.name)
        return f"You put {item.name} in {container.name}."
    
    def handle_give_to_target(self, web_user, item_name, target_name):
        """Handle giving an item to a target"""
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
        
        room = self.rooms.get(web_user.room_id)
        if not room:
            return "You are in an unknown location."
        
        # Check for user target
        for user_name in room.users:
            if user_name != web_user.name and user_name.lower() == target_name.lower():
                if user_name in self.web_users:
                    target_user = self.web_users[user_name]
                    # Move item from giver to receiver
                    web_user.inventory.remove(item_id)
                    target_user.inventory.append(item_id)
                    self.save_user_data(web_user)
                    self.save_user_data(target_user)
                    
                    item = self.items[item_id]
                    self.send_to_room(web_user.room_id, f"{web_user.name} gives {item.name} to {user_name}.")
                    return f"You give {item.name} to {user_name}."
                else:
                    return f"{user_name} is not available to receive items."
        
        # Check for bot target
        for bot in self.bots.values():
            if bot.room_id == web_user.room_id and bot.name.lower() == target_name.lower():
                if bot.visible or web_user.admin:
                    # For now, bots just acknowledge the gift but don't keep it
                    item = self.items[item_id]
                    self.send_to_room(web_user.room_id, f"{web_user.name} offers {item.name} to {bot.name}.")
                    self.send_to_room(web_user.room_id, f"{bot.name} says: 'Thank you, but I cannot accept gifts right now.'")
                    return f"You offer {item.name} to {bot.name}, but they politely decline."
        
        return f"You don't see '{target_name}' here."

    def handle_quit_cmd(self, web_user, args):
        """Handle quit/logout command - clean logout with session cleanup"""
        username = web_user.name
        
        # Notify room of departure
        self.send_to_room(web_user.room_id, f"📤 {username} has left the game.", exclude_user=username)
        
        # Clean up server state
        self.handle_user_disconnect(username, web_user.session_id)
        
        # Send logout event to client to trigger cleanup
        from flask_socketio import emit
        emit('logout', {'message': f'👋 Goodbye, {username}! You have been logged out.'})
        
        # Return message (though client will disconnect)
        return f"👋 Goodbye, {username}!"
    
    def resolve_command(self, cmd, is_admin):
        """Resolve command using most-significant match"""
        # Define all available commands
        basic_commands = [
            'help', 'version', 'whoami', 'look', 'who', 'inventory', 'say', 'whisper',
            'get', 'take', 'drop', 'examine', 'exam', 'use', 'go', 'move',
            'north', 'south', 'east', 'west'
        ]
        
        admin_commands = ['teleport', 'broadcast', 'kick', 'switchuser', 'script']
        
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
  put <item> [in <container>] - Put item down or in container
  give <item> to <target> - Give item to user or bot
  examine <item> - Look at an item closely
  use <item> - Use an item
  open <item> - Open a container
  close <item> - Close a container
  motd - View message of the day
  quit (logout) - Log out and return to login screen
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
  script <name> - Execute a bot script
  motd [message] - View or set message of the day
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
        
        # Check if user is admin
        is_admin = username in self.web_users and self.web_users[username].admin
        
        other_users = [u for u in room.users if u != username]
        visible_bots = [bot for bot in self.bots.values() if bot.room_id == room_id and bot.visible]
        invisible_bots = [bot for bot in self.bots.values() if bot.room_id == room_id and not bot.visible]
        
        if is_admin:
            # Admin view: separate lists
            if other_users:
                lines.append(f"Users here: {', '.join(other_users)}")
            
            # Show all bots with invisible ones in parentheses
            all_bots = []
            for bot in visible_bots:
                all_bots.append(bot.name)
            for bot in invisible_bots:
                all_bots.append(f"({bot.name})")
            
            if all_bots:
                lines.append(f"Bots here: {', '.join(all_bots)}")
        else:
            # Non-admin view: combined list without differentiation
            all_entities = other_users + [bot.name for bot in visible_bots]
            if all_entities:
                lines.append(f"Others here: {', '.join(all_entities)}")
        
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
    
    def handle_execute_script(self, web_user, script_name):
        """Execute a bot script"""
        if script_name not in self.scripts:
            return f"Script '{script_name}' not found. Available scripts: {', '.join(self.scripts.keys())}"
        
        script_data = self.scripts[script_name]
        bot_name = script_data.get('bot')
        script_content = script_data.get('script')
        
        if not bot_name or not script_content:
            return f"Invalid script configuration for '{script_name}'"
        
        if bot_name not in self.bots:
            return f"Bot '{bot_name}' not found for script '{script_name}'"
        
        try:
            # Execute the script in the background using socketio's background task
            self.socketio.start_background_task(
                self._execute_script_background, 
                script_content, 
                bot_name
            )
            return f"Executing script '{script_name}' for bot '{bot_name}'"
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            return f"Error executing script '{script_name}': {str(e)}"
    
    def _execute_script_background(self, script_content, bot_name):
        """Background task for script execution"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.script_engine.execute_script(script_content, bot_name)
            )
            loop.close()
        except Exception as e:
            logger.error(f"Background script execution error: {e}")
    
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
        """Handle examining an item, user, or bot"""
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
            
            # Check other users in room
            for user_name in room.users:
                if user_name != web_user.name and user_name.lower() == item_name.lower():
                    if user_name in self.web_users:
                        target_user = self.web_users[user_name]
                        admin_status = " (admin)" if target_user.admin else ""
                        return f"{user_name}{admin_status}: Another player exploring the space."
                    return f"{user_name}: Another visitor to this place."
            
            # Check bots in room (visibility depends on user permissions)
            for bot in self.bots.values():
                if bot.room_id == web_user.room_id:
                    if bot.name.lower() == item_name.lower():
                        # Regular users can only examine visible bots, admins can examine all
                        if bot.visible or web_user.admin:
                            visibility_note = " (invisible)" if not bot.visible else ""
                            return f"{bot.name}{visibility_note}: {bot.description}"
        
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
