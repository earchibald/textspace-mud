# Multi-User Text Space System

A social/community-focused multi-user text space system with educational features, real-time communication, scriptable bots, and interactive items. Designed for families, educators, and communities with a focus on child-friendly learning and creative play.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Configuration](#configuration)
- [System Design](#system-design)
- [Development](#development)

## Features

### Core Features
- **Multi-User Environment**: Real-time text-based interaction via terminal or web interface
- **Room-Based Navigation**: Hybrid navigation system with directional (north/south/east/west) and named exits
- **Interactive Bots**: Educational bots with keyword responses and autonomous scripted behaviors
- **Event System**: Room enter/leave events trigger automated bot responses
- **Item System**: Interactive items with descriptions, tags, containers, and executable scripts
- **User Persistence**: User location, inventory, and admin status saved between sessions
- **Messaging System**: Room chat, private whispers, and global announcements
- **Admin Features**: Teleportation, broadcasting, and script execution for privileged users
- **Comprehensive Logging**: All activities logged to file for monitoring and moderation

### Educational Focus
- Child-friendly design (5+ years)
- Educational bots that teach math, reading, science
- Interactive story items (books, scrolls)
- Safe, moderated environment
- Age-appropriate content and interactions

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Text Space Server                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Users      │  │    Rooms     │  │    Bots      │     │
│  │  - Inventory │  │  - Items     │  │  - Inventory │     │
│  │  - Location  │  │  - Exits     │  │  - Responses │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Items     │  │   Scripts    │  │   Events     │     │
│  │  - Container │  │  - DSL       │  │  - Triggers  │     │
│  │  - Scripts   │  │  - Variables │  │  - Handlers  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│              Script Engine (DSL Interpreter)                 │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  Terminal Interface  │  │   Web Interface      │        │
│  │  (asyncio/TCP)       │  │  (Flask/SocketIO)    │        │
│  └──────────────────────┘  └──────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Backend Storage                           │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │   Flat Files         │  │   Database           │        │
│  │   - YAML/JSON        │  │   - MongoDB + Redis  │        │
│  │   - Development      │  │   - Production       │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Backend Options

The system supports two storage backends:

#### Flat File Backend (Default)
- **Files**: YAML configuration, JSON user data
- **Use Case**: Development, small deployments, simple setup
- **Pros**: No external dependencies, easy to edit, version control friendly
- **Cons**: Limited scalability, no concurrent access protection

#### Database Backend (Production)
- **Technologies**: MongoDB (document storage) + Redis (caching/sessions)
- **Use Case**: Production deployments, multiple server instances, high concurrency
- **Pros**: Scalable, concurrent access, advanced queries, backup/restore
- **Cons**: Requires database setup and maintenance

### Migration Path

The system provides seamless migration from flat files to database:
1. **Parallel Operation**: Run both backends simultaneously during transition
2. **Zero Downtime**: Migrate without service interruption
3. **Rollback Support**: Return to flat files if needed
4. **Data Verification**: Ensure migration completeness

### Data Models

#### User
- `name`: Username (unique)
- `room_id`: Current room location
- `inventory`: List of item IDs
- `admin`: Admin privilege flag
- `writer`: Network connection

#### Room
- `id`: Unique room identifier
- `name`: Display name
- `description`: Room description text
- `exits`: Dictionary of exit_name -> room_id
- `users`: Set of usernames in room
- `items`: List of item IDs in room

#### Bot
- `name`: Bot display name
- `room_id`: Current room location
- `description`: Bot description
- `responses`: List of trigger/response pairs
- `inventory`: List of item IDs
- `visible`: Whether bot appears in room listings (false for environmental effects)

#### Item
- `id`: Unique item identifier
- `name`: Display name
- `description`: Detailed description
- `tags`: List of descriptive tags
- `is_container`: Whether item can hold other items
- `contents`: List of item IDs (if container)
- `script`: Executable script (optional)

#### Event
- `type`: Event type (enter_room, leave_room)
- `room_id`: Room where event occurred
- `user_name`: User who triggered event
- `data`: Additional event data

## Quick Start

### Installation

```bash
# Install basic dependencies
pip install -r requirements.txt

# For database backend (optional)
pip install pymongo redis bcrypt python-dotenv
```

### Backend Selection

The system supports two backends:

**Flat File Backend (Default):**
- No additional setup required
- Uses YAML/JSON files for data storage
- Perfect for development and small deployments

**Database Backend (Production):**
- Requires MongoDB and Redis
- Scalable for production use
- See [DEPLOYMENT.md](DEPLOYMENT.md) for setup instructions

### Starting the Server

**Flat File Mode (Default):**
```bash
python server.py
# or
python server_v2.py  # Enhanced version with database support
```

**Database Mode:**
```bash
# Set up .env file first (see DEPLOYMENT.md)
USE_DATABASE=true python server_v2.py
```

**Server runs on:**
- TCP: localhost:8888 (terminal/nc)  
- Web: localhost:5000 (browser)

### Connecting

**Via netcat (nc):**
```bash
nc localhost 8888
```

**Via Python client:**
```bash
python client.py
```

**Via web browser:**
```bash
# Open http://localhost:5000 (server starts both interfaces automatically)
```

### First Steps

1. Enter your username (use "admin" for admin privileges)
2. Type `help` to see available commands
3. Type `look` to see your surroundings
4. Move with `north`, `south`, `east`, `west`, or named exits
5. Chat with `say <message>`
6. Pick up items with `get <item>`

## Commands

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `look` | See room description, exits, users, bots, and items | `look` |
| `go <exit>` | Move to another room | `go north` |
| `<exit>` | Direct exit name | `garden` |
| `say <message>` | Speak to everyone in the room | `say Hello everyone!` |
| `whisper <user> <message>` | Private message to another user | `whisper alice Secret message` |
| `who` | List all online users | `who` |
| `inventory` | Show your items | `inventory` |
| `get <item>` | Pick up an item | `get magic book` |
| `drop <item>` | Drop an item | `drop treasure chest` |
| `examine <item>` | Look at an item closely | `examine magic book` |
| `use <item>` | Use an item (execute its script) | `use story scroll` |
| `help` | Show available commands | `help` |
| `quit` | Disconnect | `quit` |

### Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `teleport [room]` | Jump to room (no args lists rooms) | `teleport garden` |
| `broadcast <message>` | Send message to all users | `broadcast Server restart in 5 min` |
| `script <name>` | Execute a bot script | `script teacher_schedule` |

## Configuration

### File Structure

```
006-mats/
├── server.py              # Original unified server (flat files only)
├── server_v2.py           # Enhanced server (flat files + database)
├── client.py              # Terminal client
├── script_engine.py       # Scripting language engine
├── database.py            # Database layer (MongoDB + Redis)
├── auth.py                # Authentication system
├── migrate.py             # Original migration tool
├── migrate_v2.py          # Enhanced migration tool
├── setup.py               # Setup and management script
├── admin_tool.py          # Admin management tool
├── monitor.py             # Health monitoring tool
├── backup_tool.py         # Backup and restore tool
├── test_suite.py          # Comprehensive test suite
├── rooms.yaml             # Room definitions
├── bots.yaml              # Bot configurations
├── items.yaml             # Item definitions
├── scripts.yaml           # Bot scripts
├── users.json             # Persistent user data (auto-generated)
├── .env                   # Environment configuration (create from .env.example)
├── .env.example           # Environment template
├── templates/
│   └── index.html         # Web interface template
├── textspace.log          # Server activity log
├── requirements.txt       # Core Python dependencies
├── requirements-db.txt    # Database dependencies
├── DEPLOYMENT.md          # Database deployment guide
└── README.md              # This file
```

### rooms.yaml

Define rooms with descriptions, exits, and items:

```yaml
rooms:
  lobby:
    name: "The Lobby"
    description: "A welcoming entrance hall with soft lighting."
    exits:
      north: garden
      east: library
    items: ["treasure_chest"]
```

**Room Properties:**
- `name`: Display name shown to users
- `description`: Descriptive text
- `exits`: Dictionary of exit_name -> target_room_id
- `items`: List of item IDs initially in the room

### bots.yaml

Configure bots with responses:

```yaml
bots:
  teacher:
    name: "Ms. Teacher"
    room: "library"
    description: "A friendly educational bot."
    responses:
      - trigger: ["hello", "hi", "help"]
        response: "Hello! I'm here to help you learn."
      - trigger: ["math", "numbers"]
        response: "Math is fun! Try counting to 10."
  
  wind_spirit:
    name: "Wind Spirit"
    room: "garden"
    description: "Creates atmospheric effects."
    visible: false
    responses:
      - trigger: ["wind", "breeze"]
        response: "*A gentle breeze rustles through the leaves*"
```

**Bot Properties:**
- `name`: Display name
- `room`: Initial room location
- `description`: Bot description
- `visible`: Whether bot appears in room listings (default: true, set false for environmental effects)
- `responses`: List of trigger/response pairs
  - `trigger`: List of keywords that activate response
  - `response`: Text to say when triggered

### items.yaml

Define items with properties and scripts:

```yaml
items:
  magic_book:
    name: "Magic Book"
    description: "A mysterious book with glowing letters."
    tags: ["educational", "magic", "readable"]
    script: |
      say *The book glows and whispers: 'Knowledge is the greatest magic!'*
      wait 1
      say *You feel smarter after reading it.*
  
  treasure_chest:
    name: "Treasure Chest"
    description: "A wooden chest with brass fittings."
    tags: ["container", "treasure"]
    is_container: true
    contents: ["golden_coin", "silver_key"]
```

**Item Properties:**
- `name`: Display name
- `description`: Detailed description
- `tags`: List of descriptive tags
- `is_container`: Boolean, whether item can hold other items
- `contents`: List of item IDs (if container)
- `script`: Executable script when item is used

### scripts.yaml

Create scripted bot behaviors with event triggers:

```yaml
scripts:
  garden_guide_welcome:
    bot: "guide"
    trigger:
      event: "enter_room"
      room: "garden"
    script: |
      say Welcome to our beautiful garden!
      wait 1
      say Take your time to explore and enjoy the flowers.
```

**Script Properties:**
- `bot`: Bot name that executes the script
- `trigger`: Optional event trigger
  - `event`: Event type (enter_room, leave_room)
  - `room`: Specific room (optional, omit for all rooms)
- `script`: Script commands (see Scripting Language below)

## System Design

### Scripting Language (DSL)

The system includes a simple Domain-Specific Language for bot behaviors:

**Commands:**

| Command | Description | Example |
|---------|-------------|---------|
| `say <message>` | Bot speaks in current room | `say Hello everyone!` |
| `wait <seconds>` | Pause execution | `wait 2` |
| `set <var> <value>` | Set a variable | `set topic math` |
| `if <var> equals <value> then <cmd>` | Conditional execution | `if topic equals math then say Let's learn!` |
| `broadcast <message>` | Message all users | `broadcast Important announcement` |
| `move <room_id>` | Move bot to room | `move library` |
| `random_say <msg1>\|<msg2>\|...` | Say random message | `random_say Hi!\|Hello!\|Greetings!` |
| `repeat <count> { commands }` | Loop commands | `repeat 3 { say Hello; wait 1 }` |
| `function <name> { commands }` | Define function | `function greet { say Welcome! }` |
| `call <function>` | Call user function | `call greet` |
| `give <item> <user>` | Give item to user | `give magic_book alice` |
| `take <item> <user>` | Take item from user | `take magic_book alice` |

**Example Script:**

```yaml
script: |
  # Advanced lesson with functions and loops
  function greeting { say Welcome to our lesson!; wait 1 }
  function countdown { repeat 3 { say Counting...; wait 1 } }
  
  call greeting
  set lesson_topic math
  if lesson_topic equals math then say Let's learn about numbers!
  call countdown
  repeat 2 { say Practice makes perfect!; wait 1 }
  say Great job everyone!
```

### Event System

Events trigger automated responses when users interact with the world:

**Event Types:**
- `enter_room`: Triggered when user enters a room
- `leave_room`: Triggered when user leaves a room

**Event Flow:**
1. User performs action (move, teleport, login)
2. Event is triggered with room_id and user_name
3. System checks for registered event handlers
4. Matching scripts are executed automatically

**Example Use Cases:**
- Welcome messages when entering specific rooms
- Farewell messages when leaving
- Room-specific bot behaviors
- Educational content delivery

### Item System

Items provide interactive objects with multiple capabilities:

**Item Features:**
- **Descriptions**: Detailed text shown on examination
- **Tags**: Categorization and filtering
- **Containers**: Items that hold other items
- **Scripts**: Executable behaviors when used
- **Portability**: Can be carried by users, bots, or placed in rooms

**Item Interactions:**
- `get <item>`: Pick up from room
- `drop <item>`: Place in room
- `examine <item>`: View details
- `use <item>`: Execute item script
- `inventory`: View carried items

**Container Items:**
- Can hold multiple items
- Contents shown on examination
- Items can be nested (containers in containers)

### Logging System

All server activities are logged to `textspace.log`:

**Logged Events:**
- Server startup/shutdown
- User connections/disconnections
- User logins (with admin status)
- Chat messages (user, room, content)
- Admin actions (teleport, broadcast, scripts)
- User commands (debug level)
- Errors and exceptions

**Log Format:**
```
2025-12-21 08:00:00,000 - INFO - User 'alice' logged in
2025-12-21 08:00:05,123 - INFO - User 'alice' says in 'lobby': Hello!
```

### Authentication & Permissions

**Simple Authentication:**
- Username-based (no passwords in current version)
- Unique usernames enforced
- Admin status granted to username "admin"

**Permission Levels:**
- **Regular Users**: Basic commands (move, chat, items)
- **Admin Users**: Additional commands (teleport, broadcast, script execution)

### Network Architecture

**Unified Server Architecture:**
- **Single Process**: One server handles both TCP and HTTP/WebSocket connections
- **TCP Interface** (port 8888): Raw TCP with line-based text for terminal clients
- **Web Interface** (port 5000): HTTP + WebSocket for browser-based access
- **Shared Backend**: All users (TCP and web) interact in the same world with shared state
- **Cross-Protocol Communication**: Terminal and web users can see and interact with each other

## Development

### Management Tools

The system includes comprehensive management tools for setup, administration, and maintenance:

#### Setup Tool (`setup.py`)
Automated setup and configuration:
```bash
# Set up flat file mode (simple)
python setup.py setup-flat

# Set up database mode (production)
python setup.py setup-db

# Check system status
python setup.py status

# Run test suite
python setup.py test

# Auto-start server
python setup.py start
```

#### Admin Tool (`admin_tool.py`)
User and system administration:
```bash
# List all users
python admin_tool.py list

# Promote user to admin
python admin_tool.py promote username

# Create new user
python admin_tool.py create username --admin

# Reset user location
python admin_tool.py reset-location username --room lobby

# Show system information
python admin_tool.py info
```

#### Migration Tool (`migrate_v2.py`)
Database migration and sync:
```bash
# Migrate from flat files to database
python migrate_v2.py migrate

# Run parallel sync (zero downtime)
python migrate_v2.py sync

# Verify migration integrity
python migrate_v2.py verify
```

#### Monitoring Tool (`monitor.py`)
Health checks and monitoring:
```bash
# Run health check
python monitor.py

# Continuous monitoring
python monitor.py --monitor --interval 60

# Database mode monitoring
python monitor.py --database
```

#### Backup Tool (`backup_tool.py`)
Data backup and restore:
```bash
# Create backup
python backup_tool.py create

# List available backups
python backup_tool.py list

# Restore from backup
python backup_tool.py restore backup_file.tar.gz
```

#### Test Suite (`test_suite.py`)
Comprehensive testing:
```bash
# Run all tests
python test_suite.py

# Tests include:
# - Unit tests for core components
# - Integration tests with real server
# - Performance benchmarks
# - Database connectivity tests
```

### Adding New Rooms

1. Edit `rooms.yaml`
2. Add room definition with unique ID
3. Define exits to/from existing rooms
4. Optionally add items
5. Restart server

### Adding New Bots

1. Edit `bots.yaml`
2. Define bot with name, room, responses
3. Optionally create welcome script in `scripts.yaml`
4. Restart server

### Adding New Items

1. Edit `items.yaml`
2. Define item with name, description, tags
3. Optionally add script for interactive behavior
4. Place in room via `rooms.yaml` or give to bot
5. Restart server

### Creating Bot Scripts

1. Edit `scripts.yaml`
2. Define script with bot name
3. Add event trigger if desired
4. Write script using DSL commands
5. Test with `script <name>` command (admin)

### Extending the System

**Adding New Commands:**
1. Add command handler in `server.py` `process_command()`
2. Implement command function
3. Update help text
4. Test thoroughly

**Adding New Script Commands:**
1. Add function to `script_engine.py`
2. Register in `self.functions` dictionary
3. Implement async function
4. Document in README

**Adding New Event Types:**
1. Define event trigger points in `server.py`
2. Call `trigger_event()` with event type
3. Update script loading to recognize new event
4. Document event type

### Testing

**Manual Testing:**
```bash
# Terminal 1: Start server
python server.py

# Terminal 2: Connect as user
nc localhost 8888

# Terminal 3: Connect as admin
nc localhost 8888
# Enter "admin" as username
```

**Test Scripts:**
- `test_messaging.sh`: Multi-user chat
- `test_bots.sh`: Bot interactions
- `test_scripts.sh`: Script execution
- `test_complete.sh`: Full system test

### Dependencies

```
PyYAML>=6.0          # Configuration file parsing
flask>=2.3.0         # Web interface framework
flask-socketio>=5.5.0 # Real-time web communication
```

## Child-Friendly Design

### Safety Features
- Simple, clear commands and responses
- Educational bots that encourage learning
- Moderated environment (via logging)
- Age-appropriate content
- No external network access required

### Educational Content
- Math concepts (counting, arithmetic)
- Reading and storytelling
- Science facts and exploration
- Creative play and imagination
- Social interaction skills

### Parental Controls
- Admin oversight capabilities
- Activity logging for review
- Broadcast messaging for announcements
- Script control for content management

## Future Enhancements

### Planned Features
- Enhanced moderation tools
- Plugin system for custom bots
- Scheduled bot behaviors
- Item crafting system
- Quest/achievement system
- Multi-room broadcasts (areas)
- User-to-user item trading
- Bot AI integration

### Technical Improvements
- ✅ Database backend for persistence (MongoDB + Redis)
- ✅ Enhanced authentication with password hashing
- ✅ Migration tools for seamless upgrades
- Enhanced web interface with graphics
- Mobile app support
- Voice interface option
- Multi-language support
- Performance optimization
- Automated testing suite

## License

Created for social learning and creative play. Perfect for families, educators, and communities.

## Support

For issues, questions, or contributions, please refer to the project repository or contact the maintainers.

---

**Version:** 1.0  
**Last Updated:** 2025-12-21  
**Status:** Production Ready
