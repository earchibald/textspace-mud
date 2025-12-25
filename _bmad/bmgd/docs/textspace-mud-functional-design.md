# TextSpace MUD - Functional Design Document

**Project**: TextSpace MUD (The Text Spot)  
**Version**: 2.9.4  
**Last Updated**: 2025-12-25  
**Repository**: https://github.com/earchibald/textspace-mud

## 1. System Overview

TextSpace MUD is a web-based multi-user dungeon (MUD) game engine built with Flask and SocketIO. It provides a terminal-style interface for text-based adventure gaming with real-time multiplayer interaction.

### 1.1 Key Characteristics
- Web-based terminal UI with persistent room display
- Real-time WebSocket communication
- YAML-based configuration for rooms, items, bots, and scripts
- Admin command system with user management
- Tab completion for improved UX
- MCP (Model Context Protocol) API for remote management
- Dual-environment deployment (development/production)

## 2. Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser Client                        │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │   Terminal UI      │  │    WebSocket Client          │  │
│  │  - Input/Output    │  │  - Real-time messaging       │  │
│  │  - Tab Completion  │  │  - Login/Command handling    │  │
│  │  - Room Display    │  │  - Auto-reconnect            │  │
│  └────────────────────┘  └──────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ WebSocket (socket.io)
                     │ HTTP/HTTPS
┌────────────────────┴────────────────────────────────────────┐
│                     Flask Application                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              TextSpaceServer Core                     │  │
│  │  - Session Management (WebUser)                       │  │
│  │  - Command Registry & Processing                      │  │
│  │  - Room Management                                    │  │
│  │  - Inventory System                                   │  │
│  │  - Bot & Script Engine                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MCP API Endpoints                        │  │
│  │  - /api/mcp/login, /api/mcp/logout                    │  │
│  │  - /api/mcp/send_command                              │  │
│  │  - /api/mcp/status                                    │  │
│  │  - /api/completions (tab completion)                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  Persistent Storage                          │
│  - YAML Config Files (rooms, bots, items, scripts)          │
│  - User Data (JSON per user)                                │
│  - MOTD (Message of the Day)                                │
│  - Database (optional, via volume mount)                    │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

**Backend**:
- Python 3.10
- Flask (web framework)
- Flask-SocketIO (WebSocket support)
- PyYAML (configuration parsing)

**Frontend**:
- Vanilla JavaScript
- Socket.IO client
- CSS Grid layout

**Infrastructure**:
- Docker (containerization)
- Railway (cloud hosting - dev & prod)
- GitHub Actions (CI/CD)
- DevContainer (development environment)

## 3. Development Workflow

### 3.1 Branch Strategy

```
main (production)
  └─ PR merge ──┐
                │
develop (staging)
  └─ PR merge ──┘
                │
feature/* (feature branches)
```

**Branches**:
- `main`: Production-ready code, deployed to Railway production
- `develop`: Integration branch, deployed to Railway development
- `feature/*`: Individual feature development

### 3.2 Development Environment

**DevContainer Configuration**:
- Base: Python 3.10 on Debian Bullseye
- Node.js 20 (for npx and tooling)
- Homebrew (for Railway CLI)
- Railway CLI (deployment management)
- VS Code with Python, Jupyter, Docker, Copilot extensions

**Local Development**:
```bash
# Start local server
python3 server_web_only.py

# Access at http://localhost:8080
```

### 3.3 CI/CD Pipeline

**GitHub Actions** (`.github/workflows/test-features.yml`):
- Triggers: Push to `main` or `develop`, PRs to either branch
- Jobs:
  1. Unit tests (Python validation, config file checks)
  2. Integration tests (server startup verification)
  3. Daily scheduled runs (9 AM UTC)

**Railway Deployment**:
- **Development**: `develop` branch → `textspace-mud-dev-development.up.railway.app`
- **Production**: `main` branch → `exciting-liberation-production.up.railway.app`
- Auto-deploy on push (when GitHub integration configured)
- Manual deploy: `railway up --detach`

### 3.4 Deployment Timeline
- GitHub push → CI runs (~60s)
- Railway build & deploy (~60s)
- **Total**: ~120 seconds from push to live

## 4. Core Components

### 4.1 Command System

**Command Registry** (`command_registry.py`):
- Centralized command registration
- Argument validation and type checking
- Admin-only command filtering
- Alias support
- Usage help generation

**Command Types**:
- Basic: `help`, `version`, `whoami`, `who`, `motd`, `quit`
- Navigation: `look`, `go`, `north`, `south`, `east`, `west`
- Items: `get`, `drop`, `put`, `give`, `inventory`, `use`
- Interaction: `open`, `close`, `examine`
- Communication: `say`, `whisper`
- Admin: `teleport`, `broadcast`, `kick`, `switchuser`, `script`

### 4.2 Tab Completion

**Features**:
- Command name completion
- Argument completion (users, items, exits, bots)
- Context-aware suggestions based on:
  - Room contents
  - Inventory
  - Open containers
  - User permissions (admin vs regular)
- Empty input shows formatted help display

**API**: `/api/completions?partial={text}&user={username}&text={fullText}`

### 4.3 Room System

**Room Structure** (YAML):
```yaml
- name: Room Name
  description: Room description text
  exits:
    direction: destination_room_id
  items:
    - item_id
  bots:
    - bot_id
```

**Features**:
- Dynamic room descriptions
- Exit management
- Item and bot placement
- User presence tracking
- Persistent room state

### 4.4 Item System

**Item Structure** (YAML):
```yaml
- id: item_id
  name: Item Display Name
  description: Item description
  type: object|container
  portable: true|false
  open: true|false  # for containers
  contents: []      # for containers
```

**Features**:
- Portable/non-portable items
- Container items (can hold other items)
- Open/close state management
- Item examination
- Use actions (extensible)

### 4.5 Bot System

**Bot Structure** (YAML):
```yaml
- id: bot_id
  name: Bot Name
  description: Bot description
  script: script_id  # optional
```

**Features**:
- NPCs in rooms
- Script-driven behavior
- Interaction hooks (examine, talk, give)

### 4.6 Script Engine

**Script Structure** (YAML):
```yaml
- id: script_id
  name: Script Name
  description: Script purpose
  trigger: event_type
  actions:
    - type: action_type
      params: {}
```

**Trigger Types**:
- `on_examine`: Player examines object
- `on_use`: Player uses item
- `on_enter`: Player enters room
- Custom triggers

## 5. Configuration Management

### 5.1 Configuration Files

**Location**: `/app/data/` (persistent volume)

**Files**:
- `rooms.yaml`: Room definitions
- `items.yaml`: Item definitions
- `bots.yaml`: Bot definitions
- `scripts.yaml`: Script definitions
- `motd.txt`: Message of the day
- `users/*.json`: User save data

### 5.2 MCP Remote Configuration

**Endpoints**:
- Read configuration files
- Write/update configuration (with validation)
- Reset to examples
- Validate YAML before applying

**Authentication**: IP whitelist (localhost + Railway internal IPs)

## 6. User Management

### 6.1 User Sessions

**WebUser Object**:
- `name`: Username
- `session_id`: Unique session identifier
- `admin`: Admin privileges flag
- `room_id`: Current room location
- `inventory`: List of item IDs
- `authenticated`: Login status

**Session Storage**:
- In-memory: `self.web_users[username]`
- Persistent: `data/users/{username}.json`

### 6.2 Authentication

**Login**:
- Username-only (no password)
- Admin users: `admin`, `tester-admin`
- Auto-login from localStorage cache
- Session persistence across reconnects

**Logout**:
- `quit` or `logout` command
- Clears localStorage cache
- Disconnects WebSocket
- Saves user state

### 6.3 Admin Features

**Admin Commands**:
- `teleport [room]`: Jump to any room
- `broadcast <msg>`: Message all users
- `kick <user>`: Disconnect user
- `switchuser <user>`: Impersonate user
- `script <name>`: Run bot script
- `motd [message]`: View/set MOTD

**Admin Display**:
- Environment name on login (`🔧 Environment: {name}`)
- Admin indicator in whoami/who commands
- Extended command help

## 7. UI Architecture

### 7.1 Layout Structure

```
┌─────────────────────────────────────────────┐
│          Status Bar (connection)            │
├─────────────────────────────────────────────┤
│       Room Info Box (110px fixed)           │
│  - Room Name                                │
│  - Description                              │
│  - Exits                                    │
│  - Users, Bots, Items                       │
├─────────────────────────────────────────────┤
│     Main Output (400px, scrollable)         │
│  - Chat messages                            │
│  - Command responses                        │
│  - System messages                          │
├─────────────────────────────────────────────┤
│       Input + Send Button                   │
└─────────────────────────────────────────────┘
```

### 7.2 Room Info Display Logic

**Update Conditions**:
- Message must be multi-line
- Must not be help text, MOTD, or system messages
- Must not start with `>` (user command echo)
- Must not contain chat indicators (`says:`, `whispers:`)
- Must have room name + description format

**Skip Conditions**:
- `Available commands:` (help text)
- `Type "help"` (prompts)
- `📢 Message of the Day:`
- `🔧 Environment:`

## 8. Environment Configuration

### 8.1 Environment Variables

**Development**:
- `RAILWAY_ENVIRONMENT_NAME=development`
- `DATABASE_PATH=/app/data/textspace-dev.db`
- `USE_DATABASE=true`
- `SECRET_KEY=textspace-dev-secret-key-*`
- `PORT=8080`

**Production**:
- `RAILWAY_ENVIRONMENT_NAME=production`
- `DATABASE_PATH=/app/data/textspace.db`
- `USE_DATABASE=true`
- `SECRET_KEY=textspace-super-secret-key-*`
- `PORT=8080`

**Local**:
- Defaults to `RAILWAY_ENVIRONMENT_NAME=local`
- File-based storage in `data/`

### 8.2 Persistent Storage

**Railway Volumes**:
- Development: `/app/data` (textspace-mud-dev-volume)
- Production: `/app/data` (exciting-liberation-volume)

**Contents**:
- Configuration YAML files (symlinked)
- User save data
- Database file (if enabled)
- MOTD file

## 9. VS Code Tasks

**Available Tasks** (`.vscode/tasks.json`):
1. Run Server Locally
2. Deploy to Dev Railway
3. Deploy to Production Railway
4. View Dev Railway Logs
5. View Production Railway Logs
6. Check Dev Server Status
7. Install Dependencies
8. Test Python Imports

**Usage**: Run via Command Palette → `Tasks: Run Task`

## 10. Known Issues & Limitations

### 10.1 Resolved Issues
- ✅ Issue #1: Commands without args show usage help (not "unknown command")
- ✅ Issue #2: Web UI tab completion implemented
- ✅ Issue #3: MOTD functionality added
- ✅ Issue #4: Quit/logout command with cache clearing
- ✅ Issue #5: Tab completion includes items in open containers
- ✅ Issue #6: Complex grammar verbs (put, give) implemented
- ✅ Issue #7: MCP server login functionality added
- ✅ Issue #8: BMAD issue workflow updated
- ✅ Issue #10: Railway development environment configured
- ✅ Issue #11: DevContainer configured (MCP auto-start pending)
- ✅ Issue #13: Help command no longer overwrites room info

### 10.2 Current Limitations
- Playwright tests unavailable on ARM64 architecture
- MCP servers don't auto-start in DevContainer
- Railway GitHub auto-deploy requires manual Dashboard configuration
- No password authentication (username-only)

## 11. API Reference

### 11.1 WebSocket Events

**Client → Server**:
- `login`: `{username: string}`
- `command`: `{command: string}`

**Server → Client**:
- `login_response`: `{success: bool, admin: bool, username: string, message?: string}`
- `message`: `{text: string}`
- `user_switched`: `{username: string}`
- `logout`: `{message: string}`

### 11.2 HTTP API Endpoints

**MCP Endpoints** (require IP whitelist):
- `POST /api/mcp/login`: Login MCP user
- `POST /api/mcp/logout`: Logout MCP user
- `POST /api/mcp/send_command`: Send command as MCP user
- `GET /api/mcp/status`: Get MCP session status

**Completion Endpoint**:
- `GET /api/completions?partial={text}&user={username}&text={fullText}`

### 11.3 Configuration API

See `textspace_remote_mcp_server.py` for MCP server configuration tools.

## 12. Future Enhancements

### 12.1 Planned Features
- Password authentication system
- Persistent database for game state
- Quest/achievement system
- Combat system
- Economy/trading system
- Enhanced bot AI with conversation trees
- Web-based admin panel
- Mobile-responsive UI

### 12.2 Infrastructure Improvements
- GitHub auto-deploy configuration documentation
- Automated Playwright tests (non-ARM64 runner)
- Prometheus metrics endpoint
- Structured logging (JSON)
- Health check endpoint improvements
- Redis for session management (multi-instance)

## 13. Quick Reference

### 13.1 Common Commands

```bash
# Development
python3 server_web_only.py              # Run locally
git checkout develop                     # Switch to dev branch
git push origin develop                  # Deploy to dev
railway environment development          # Switch to dev env
railway logs                            # View dev logs

# Deployment
railway up --detach                     # Manual deploy
railway status                          # Check deployment

# Testing
curl https://textspace-mud-dev-development.up.railway.app/
```

### 13.2 File Locations

```
/workspaces/006-mats/
├── server_web_only.py          # Main server
├── command_registry.py         # Command system
├── config_manager.py           # Config loader
├── script_engine.py            # Script executor
├── templates/index.html        # Web UI
├── requirements.txt            # Python deps
├── Dockerfile                  # Container image
├── railway.json                # Railway config
├── .github/workflows/          # CI/CD
├── .devcontainer/              # DevContainer
├── data/                       # Persistent data
│   ├── rooms.yaml
│   ├── items.yaml
│   ├── bots.yaml
│   ├── scripts.yaml
│   └── users/
└── _bmad/                      # BMAD framework
    └── bmgd/                   # Game development
```

---

**Document Version**: 1.0  
**Maintained By**: BMAD Game Development Team  
**Next Review**: When significant features are added
