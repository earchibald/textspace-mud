# TextSpace Remote MCP Server

Remote management system for Railway-deployed TextSpace server via REST API.

## Overview

The Remote MCP Server provides the same 10 tools as the local version, but operates against the live Railway deployment via REST API endpoints instead of local files.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Kiro CLI / Agent                        │
├─────────────────────────────────────────────────────────┤
│              Remote MCP Client                           │
├─────────────────────────────────────────────────────────┤
│           textspace_remote_mcp_server.py                 │
│                      ↓ HTTPS/WSS                        │
├─────────────────────────────────────────────────────────┤
│         Railway: textspace-mud-production                │
│              server_web_only.py                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  REST API    │  │  WebSocket   │  │   Web UI     │ │
│  │  /api/*      │  │  /socket.io  │  │      /       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Rooms     │  │    Bots      │  │    Items     │ │
│  │  rooms.yaml  │  │  bots.yaml   │  │ items.yaml   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## REST API Endpoints

The TextSpace server now exposes these API endpoints:

### Server Management
- `GET /api/status` - Server status, version, user count
- `GET /api/logs?lines=N` - Recent server logs

### Configuration Management  
- `GET /api/config/<type>` - Read configuration (rooms, bots, items, scripts)
- `POST /api/config/<type>` - Update configuration with automatic backup

### Version Management
- `POST /api/version` - Increment server version

## MCP Tools (Remote)

All 10 tools from the local MCP server, but operating remotely:

| Tool | Remote Operation |
|------|------------------|
| `server_status` | GET /api/status |
| `server_logs` | GET /api/logs |
| `read_config` | GET /api/config/<type> |
| `write_config` | POST /api/config/<type> + validation |
| `validate_config` | Local YAML validation |
| `increment_version` | POST /api/version |
| `connect_websocket` | WSS to Railway WebSocket |
| `send_command` | WebSocket command sending |
| `get_messages` | WebSocket message retrieval |
| `run_tests` | Remote API endpoint testing |

## Configuration

### MCP Server Configuration

Both local and remote MCP servers are configured in `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "textspace-local": {
      "command": "python3",
      "args": ["/Users/earchibald/scratch/006-mats/textspace_mcp_server.py"],
      "env": {
        "TEXTSPACE_PROJECT_PATH": "/Users/earchibald/scratch/006-mats"
      }
    },
    "textspace-remote": {
      "command": "python3", 
      "args": ["/Users/earchibald/scratch/006-mats/textspace_remote_mcp_server.py"],
      "env": {
        "TEXTSPACE_BASE_URL": "https://textspace-mud-production.up.railway.app"
      }
    }
  }
}
```

### Base URL Configuration

The remote MCP server defaults to:
```
https://textspace-mud-production.up.railway.app
```

This can be overridden via environment variable:
```bash
export TEXTSPACE_BASE_URL="https://your-custom-domain.com"
```

## Usage Examples

### Using Remote MCP Tools

```python
# In Kiro CLI with textspace-remote MCP server

# Check remote server status
result = await call_tool("server_status", {})
# Returns: {"running": true, "version": "2.0.11", "users_online": 3}

# Read remote configuration
result = await call_tool("read_config", {"config_type": "rooms"})

# Update remote configuration
new_config = """
rooms:
  lobby:
    name: "Updated Lobby"
    description: "A renovated entrance hall"
    exits:
      north: garden
    items: []
"""
result = await call_tool("write_config", {
    "config_type": "rooms", 
    "content": new_config
})
# Creates backup on Railway server, updates config, reloads

# Increment remote version
result = await call_tool("increment_version", {})
# Updates version on Railway server

# Connect to remote WebSocket
result = await call_tool("connect_websocket", {})

# Send command to remote server
result = await call_tool("send_command", {
    "command": "broadcast Hello from remote MCP!",
    "username": "admin"
})

# Run remote tests
result = await call_tool("run_tests", {"test_type": "full"})
```

### Remote vs Local Operations

| Operation | Local MCP | Remote MCP |
|-----------|-----------|------------|
| **Config Read** | File system | GET /api/config/<type> |
| **Config Write** | File + backup | POST /api/config/<type> + backup |
| **Server Status** | Process check | GET /api/status |
| **Logs** | tail textspace.log | GET /api/logs |
| **Version** | Edit file | POST /api/version |
| **WebSocket** | ws://localhost:8080 | wss://railway.app |
| **Testing** | Local endpoints | Remote API testing |

## Safety Features

### Automatic Backups
All configuration updates create timestamped backups on the Railway server:
```
rooms.yaml.backup.20251221_180307
bots.yaml.backup.20251221_180315
```

### Validation
All YAML configurations are validated before sending to the remote server:
- Syntax validation
- Schema validation (rooms must have names, etc.)
- Error reporting with specific issues

### Error Handling
- Network timeouts (10 seconds)
- HTTP error code handling
- Graceful degradation when Railway is unavailable
- Detailed error messages

## Testing

### Remote Test Suite

The remote MCP server includes specialized tests:

```python
# Basic tests
- Server Status: GET /api/status
- API Endpoints: Endpoint availability  
- Config Access: GET /api/config/rooms

# Web tests  
- Web Server: GET / (main page)
- WebSocket: WSS connection
- API Endpoints: Full API testing

# Full tests
- All basic + web tests
- Version Management: Version API
- Configuration CRUD: Full config lifecycle
```

### Running Tests

```bash
# Test remote MCP server
python3 test_remote_mcp.py

# Use MCP tools for testing
await call_tool("run_tests", {"test_type": "full"})
```

## Deployment Workflow

### 1. Local Development
```bash
# Use local MCP server for development
# Edit configs, test locally, commit changes
```

### 2. Remote Deployment
```bash
# Push to GitHub (triggers Railway deployment)
git push origin main

# Use remote MCP server to manage live instance
# Update configs, increment version, monitor
```

### 3. Configuration Management
```bash
# Read current remote config
remote_config = await call_tool("read_config", {"config_type": "rooms"})

# Modify and validate
validation = await call_tool("validate_config", {
    "config_type": "rooms",
    "content": modified_config
})

# Deploy if valid
if validation["valid"]:
    await call_tool("write_config", {
        "config_type": "rooms",
        "content": modified_config
    })
    
    # Increment version
    await call_tool("increment_version", {})
```

## Troubleshooting

### Connection Issues
```bash
# Check Railway deployment status
curl https://textspace-mud-production.up.railway.app/api/status

# Test API endpoints
curl https://textspace-mud-production.up.railway.app/api/config/rooms
```

### Configuration Issues
```bash
# Validate before sending
await call_tool("validate_config", {
    "config_type": "rooms",
    "content": yaml_content
})

# Check backups on Railway server
await call_tool("server_logs", {"lines": 20})
```

### WebSocket Issues
```bash
# Test WebSocket connection
await call_tool("connect_websocket", {})

# Check connection status
await call_tool("get_messages", {"count": 5})
```

## Security Considerations

- **HTTPS Only**: All API calls use HTTPS
- **No Authentication**: Currently open API (Railway internal)
- **Backup Safety**: All changes create backups
- **Validation**: All inputs validated before processing
- **Rate Limiting**: 10-second timeouts prevent abuse

## Future Enhancements

- [ ] API authentication/authorization
- [ ] Real-time log streaming
- [ ] Configuration diff/rollback
- [ ] Multi-environment support (staging/prod)
- [ ] Webhook notifications for config changes
- [ ] Automated testing on deployment

## Files

- `textspace_remote_mcp_server.py` - Remote MCP server implementation
- `test_remote_mcp.py` - Remote MCP server tests
- `server_web_only.py` - Updated with REST API endpoints
- `.kiro/settings/mcp.json` - Dual MCP configuration

---

**Version**: 1.0  
**Railway URL**: https://textspace-mud-production.up.railway.app  
**Status**: Production Ready
