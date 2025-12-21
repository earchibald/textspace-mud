# The Text Spot - Web-Only Multi-User Text Space

A simplified, web-focused multi-user text space system designed for educational use and creative play. Built for families, educators, and communities with child-friendly features and real-time web interaction.

## Version 2.0.0 - Web-Only Architecture

**Major Changes:**
- Removed all TCP/CLI functionality
- Simplified to web-only interface
- Streamlined codebase focused on browser experience
- Enhanced testing with comprehensive test protocols

## Features

### Core Web Features
- **Web-Only Interface**: Clean browser-based interaction via SocketIO
- **Real-Time Communication**: Instant messaging and room updates
- **Room-Based Navigation**: Directional and named exits with partial matching
- **Interactive Bots**: Educational bots with keyword responses
- **Item System**: Interactive items with descriptions and scripts
- **User Persistence**: Location and inventory saved between sessions
- **Admin Features**: Moderation tools for privileged users

### Educational Focus
- Child-friendly design (5+ years)
- Educational bots teaching math, reading, science
- Safe, moderated environment
- Age-appropriate content and interactions

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Starting the Server
```bash
python server_web_only.py
```

**Server runs on:** http://localhost:8080

### Connecting
Open your web browser and navigate to http://localhost:8080

### First Steps
1. Enter your username (use "admin" for admin privileges)
2. You'll automatically see your surroundings
3. Type `help` or `h` to see available commands
4. Move with `north`/`n`, `south`/`s`, `east`/`e`, `west`/`w`
5. Chat with `say <message>` or `"<message>`

## Commands

### Basic Commands
| Command | Alias | Description | Example |
|---------|-------|-------------|---------|
| `help` | `h` | Show available commands | `help` |
| `version` | `v` | Show server version | `version` |
| `look` | `l` | See room description | `look` |
| `go <exit>` | `g` | Move to another room | `go north` |
| `north/south/east/west` | `n/s/e/w` | Move in cardinal directions | `north` |
| `say <message>` | `"` | Speak to everyone in room | `say Hello!` |
| `who` | | List all online users | `who` |
| `inventory` | `i` | Show your items | `inventory` |
| `get <item>` | | Pick up an item | `get magic book` |
| `drop <item>` | | Drop an item | `drop treasure` |
| `examine <item>` | | Look at item closely | `examine book` |
| `use <item>` | | Use an item | `use scroll` |

### Admin Commands (admin user only)
| Command | Description | Example |
|---------|-------------|---------|
| `teleport [room]` | Jump to room | `teleport library` |
| `broadcast <message>` | Message all users | `broadcast Welcome!` |
| `kick <user>` | Disconnect a user | `kick baduser` |
| `switchuser <name>` | Switch to different user | `switchuser testuser` |

## Navigation Features

### Partial Matching
- `go green` works for `go greenhouse`
- `go lib` works for `go library`
- Ambiguous matches show options: `go ga` → "Options: gap, garden"

### Auto-Login
- Username stored in browser localStorage
- Automatic login on return visits
- Use `switchuser` (admin only) to change users

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  The Text Spot v2.0.0                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Users      │  │    Rooms     │  │    Bots      │     │
│  │  - Inventory │  │  - Items     │  │  - Responses │     │
│  │  - Location  │  │  - Exits     │  │  - Inventory │     │
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
│                   Web Interface Only                         │
│  ┌──────────────────────────────────────────────────────────┤
│  │              Flask + SocketIO                            │
│  │              Real-time WebSocket                         │
│  └──────────────────────────────────────────────────────────┤
├─────────────────────────────────────────────────────────────┤
│                    File-Based Storage                        │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │   Configuration      │  │   User Data          │        │
│  │   - YAML Files       │  │   - JSON File        │        │
│  │   - Static Content   │  │   - Persistent       │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables
```bash
# Server name (appears in web interface)
SERVER_NAME="The Text Spot"

# Server host and port
HOST=0.0.0.0
PORT=8080

# Security
SECRET_KEY=your-secret-key-here
```

### File Structure
```
006-mats/
├── server_web_only.py     # Main web-only server
├── script_engine.py       # Scripting language engine
├── rooms.yaml             # Room definitions
├── bots.yaml              # Bot configurations
├── items.yaml             # Item definitions
├── scripts.yaml           # Bot scripts
├── users.json             # Persistent user data
├── templates/
│   └── index.html         # Web interface template
├── test_web_only.py       # Comprehensive test suite
├── textspace.log          # Server activity log
├── requirements.txt       # Python dependencies
└── README_WEB_ONLY.md     # This file
```

## Testing

### Automated Tests
```bash
# Run comprehensive test suite
python test_web_only.py
```

**Test Coverage:**
- 16 functional requirements tested
- Unit tests for all core functionality
- Manual test protocols for integration testing

### Manual Testing Protocols

Each functional requirement has a specific test protocol:

**FR-01 Server Initialization**
1. Start server with `python server_web_only.py`
2. Verify web interface loads at http://localhost:8080
3. Check logs show 'Web server starting'
4. Verify no TCP server messages in logs

**FR-02 Version Tracking**
1. Connect to web interface
2. Login as any user
3. Type 'version' or 'v'
4. Verify response shows 'The Text Spot v2.0.0'

**FR-03 Command Aliases**
1. Login to web interface
2. Test each alias: v, h, l, i, n, s, e, w
3. Verify each produces same result as full command
4. Test 'g garden' for go command

*[Continue with all 16 test protocols...]*

## Development

### Adding New Rooms
1. Edit `rooms.yaml`
2. Add room definition with unique ID
3. Define exits to/from existing rooms
4. Restart server

### Adding New Items
1. Edit `items.yaml`
2. Define item with name, description, tags
3. Optionally add script for interactive behavior
4. Place in room via `rooms.yaml`

### Adding New Bots
1. Edit `bots.yaml`
2. Define bot with name, room, responses
3. Optionally create scripts in `scripts.yaml`
4. Restart server

## Deployment

### Local Development
```bash
python server_web_only.py
```

### Production (Railway)
```bash
# Set environment variables
export SERVER_NAME="Your Server Name"
export SECRET_KEY="your-production-secret"

# Deploy
railway up
```

## Child-Friendly Design

### Safety Features
- Simple, clear commands and responses
- Educational bots encouraging learning
- Admin moderation tools (kick, broadcast)
- Age-appropriate content
- Web-only interface (no external tools needed)

### Educational Content
- Math concepts (counting, arithmetic)
- Reading and storytelling
- Science facts and exploration
- Creative play and imagination
- Social interaction skills

## Version History

### v2.0.0 - Web-Only Architecture
- Removed all TCP/CLI functionality
- Simplified to web-only interface
- Enhanced testing with 16 functional requirements
- Comprehensive test protocols
- Streamlined codebase

### v1.x.x - Legacy Versions
- Dual TCP/Web interface
- Complex architecture
- Mixed functionality

## License

Educational use focused on social learning and creative play. Perfect for families, educators, and communities.

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-21  
**Status:** Production Ready - Web Only
