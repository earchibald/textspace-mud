# TextSpace MCP Server & Agent

Specialized MCP server and agent for managing the TextSpace multi-user text adventure server.

## Overview

The TextSpace MCP Server provides comprehensive tools for:
- **Server Management**: Start, stop, monitor server status
- **Configuration Management**: Read, write, validate YAML configs with automatic backups
- **Runtime Interaction**: Connect via WebSocket, send commands, monitor activity
- **Automated Testing**: Run comprehensive test suites with detailed reporting
- **Version Management**: Automatic version incrementing for deployments

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Kiro CLI / Agent                        │
├─────────────────────────────────────────────────────────┤
│                  MCP Client Layer                        │
├─────────────────────────────────────────────────────────┤
│              TextSpace MCP Server                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Server     │  │    Config    │  │   Testing    │ │
│  │  Management  │  │  Management  │  │    Suite     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │  WebSocket   │  │   Version    │                   │
│  │  Connection  │  │  Management  │                   │
│  └──────────────┘  └──────────────┘                   │
├─────────────────────────────────────────────────────────┤
│              TextSpace Server (Flask/SocketIO)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Rooms     │  │    Bots      │  │    Items     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

```bash
# Install MCP SDK
pip install mcp

# Install WebSocket client
pip install websocket-client

# Install YAML parser (already installed)
pip install pyyaml
```

### Setup

1. **MCP Server is already created** at `/Users/earchibald/scratch/006-mats/textspace_mcp_server.py`

2. **MCP Configuration** is set up at `.kiro/settings/mcp.json`

3. **Test the MCP server**:
```bash
cd /Users/earchibald/scratch/006-mats
python3 test_mcp_client.py
```

## Available MCP Tools

### Server Management

#### `server_status`
Check if TextSpace server is running and get version info.

**Parameters**: None

**Returns**: JSON with running status, version, project path, timestamp

**Example**:
```json
{
  "running": true,
  "version": "2.0.7",
  "project_path": "/Users/earchibald/scratch/006-mats",
  "timestamp": "2025-12-21T17:45:00"
}
```

#### `server_start`
Start the TextSpace server in background.

**Parameters**: None

**Returns**: Success message with PID or error

#### `server_stop`
Stop the running TextSpace server.

**Parameters**: None

**Returns**: Success or error message

#### `server_logs`
Get recent server logs.

**Parameters**:
- `lines` (integer, optional): Number of log lines (default: 50)

**Returns**: Log content as text

### Configuration Management

#### `read_config`
Read TextSpace configuration files.

**Parameters**:
- `config_type` (string, required): One of "rooms", "bots", "items", "scripts"

**Returns**: YAML configuration content

#### `write_config`
Write configuration file with validation and automatic backup.

**Parameters**:
- `config_type` (string, required): One of "rooms", "bots", "items", "scripts"
- `content` (string, required): YAML content to write

**Returns**: Success message with backup location or validation error

**Features**:
- Validates YAML syntax before writing
- Creates timestamped backup of existing config
- Validates schema structure (rooms must have name, etc.)

#### `validate_config`
Validate YAML configuration without writing.

**Parameters**:
- `config_type` (string, required): One of "rooms", "bots", "items", "scripts"
- `content` (string, required): YAML content to validate

**Returns**: JSON with validation result

**Example**:
```json
{
  "valid": true,
  "data": { ... parsed YAML ... }
}
```

#### `increment_version`
Increment server version number (patch version).

**Parameters**: None

**Returns**: New version number

**Example**: "2.0.7" → "2.0.8"

### Runtime Interaction

#### `connect_websocket`
Connect to running TextSpace server via WebSocket.

**Parameters**:
- `url` (string, optional): WebSocket URL (default: "ws://localhost:5000")

**Returns**: Connection status

**Note**: Connection is maintained for subsequent commands

#### `send_command`
Send command to TextSpace server.

**Parameters**:
- `command` (string, required): Command to send
- `username` (string, optional): Username to send as (default: "admin")

**Returns**: Confirmation message

**Example Commands**:
- "look" - View current room
- "north" - Move north
- "say Hello" - Speak in room
- "teleport garden" - Admin teleport
- "broadcast Message" - Admin broadcast

#### `get_messages`
Get recent WebSocket messages from server.

**Parameters**:
- `count` (integer, optional): Number of messages (default: 10)

**Returns**: JSON array of messages with timestamps

### Testing

#### `run_tests`
Run automated test suite.

**Parameters**:
- `test_type` (string, optional): One of "basic", "web", "full" (default: "basic")

**Test Types**:
- **basic**: Server status, config files, log file
- **web**: Web server, WebSocket, game commands
- **full**: All tests including room navigation, items, bots

**Returns**: JSON test results with summary

**Example**:
```json
{
  "timestamp": "2025-12-21T17:45:00",
  "test_type": "full",
  "results": [
    {
      "test": "Server Status",
      "status": "PASS",
      "details": "Version: 2.0.7"
    },
    ...
  ],
  "summary": "8/8 tests passed"
}
```

## TextSpace Agent

The `textspace_agent.py` provides high-level management workflows:

### Agent Capabilities

#### `health_check()`
Comprehensive health check with recommendations.

**Returns**:
```json
{
  "status": "healthy|warning|critical",
  "message": "Status description",
  "version": "2.0.7",
  "tests_passed": "8/8 tests passed",
  "recommendation": "Optional action to take"
}
```

#### `deploy_update(config_changes)`
Deploy updates with proper version management.

**Process**:
1. Health check
2. Validate and apply config changes
3. Increment version
4. Restart server
5. Final health check

**Parameters**:
- `config_changes` (dict, optional): Dict of config_type → YAML content

**Example**:
```python
agent.deploy_update({
    "rooms": "rooms:\n  lobby:\n    name: 'New Lobby'\n    ..."
})
```

#### `interactive_testing()`
Run interactive testing session with multiple scenarios.

**Scenarios**:
- Basic Commands (help, version, look)
- Navigation (north, south)
- Items (inventory, examine, get)
- Social (say, who)

#### `monitor_server(duration_minutes)`
Monitor server for specified duration with periodic snapshots.

**Parameters**:
- `duration_minutes` (int): How long to monitor

**Returns**: Monitoring data with snapshots every 30 seconds

## Usage Examples

### Using MCP Tools Directly

```python
# In Kiro CLI with MCP server configured
# The tools are available automatically

# Check server status
result = await call_tool("server_status", {})

# Read rooms configuration
result = await call_tool("read_config", {"config_type": "rooms"})

# Validate new configuration
result = await call_tool("validate_config", {
    "config_type": "rooms",
    "content": new_yaml_content
})

# Write configuration (with backup)
result = await call_tool("write_config", {
    "config_type": "rooms",
    "content": new_yaml_content
})

# Increment version
result = await call_tool("increment_version", {})

# Connect to server
result = await call_tool("connect_websocket", {})

# Send admin command
result = await call_tool("send_command", {
    "command": "teleport garden",
    "username": "admin"
})

# Run full test suite
result = await call_tool("run_tests", {"test_type": "full"})
```

### Using the Agent

```python
from textspace_agent import TextSpaceAgent

agent = TextSpaceAgent()

# Health check
health = agent.health_check()
print(f"Status: {health['status']}")

# Deploy update
config_changes = {
    "rooms": """
rooms:
  lobby:
    name: "Updated Lobby"
    description: "A renovated entrance."
    exits:
      north: garden
    items: []
"""
}

result = agent.deploy_update(config_changes)
print(f"Deployment: {result['status']}")

# Interactive testing
test_results = agent.interactive_testing()
print(f"Tests: {test_results['status']}")

# Monitor server
monitoring = agent.monitor_server(duration_minutes=5)
print(f"Monitoring: {monitoring['message']}")
```

### Common Workflows

#### 1. Safe Configuration Update

```python
# 1. Read current config
current = await call_tool("read_config", {"config_type": "rooms"})

# 2. Modify configuration
new_config = modify_yaml(current)

# 3. Validate before writing
validation = await call_tool("validate_config", {
    "config_type": "rooms",
    "content": new_config
})

if validation["valid"]:
    # 4. Write with automatic backup
    await call_tool("write_config", {
        "config_type": "rooms",
        "content": new_config
    })
    
    # 5. Increment version
    await call_tool("increment_version", {})
    
    # 6. Restart server
    await call_tool("server_stop", {})
    await call_tool("server_start", {})
```

#### 2. Live Server Monitoring

```python
# Connect to server
await call_tool("connect_websocket", {})

# Send test commands
await call_tool("send_command", {"command": "look"})
await call_tool("send_command", {"command": "who"})

# Check responses
messages = await call_tool("get_messages", {"count": 10})
print(messages)
```

#### 3. Automated Testing

```python
# Run full test suite
results = await call_tool("run_tests", {"test_type": "full"})

# Parse results
test_data = json.loads(results)
passed = sum(1 for r in test_data["results"] if r["status"] == "PASS")
total = len(test_data["results"])

print(f"Tests: {passed}/{total} passed")

# Check for failures
failures = [r for r in test_data["results"] if r["status"] != "PASS"]
if failures:
    print("Failed tests:")
    for failure in failures:
        print(f"  - {failure['test']}: {failure.get('error', 'Unknown')}")
```

## Integration with Kiro CLI

The MCP server is configured in `.kiro/settings/mcp.json` and automatically available in Kiro CLI sessions.

### Using in Kiro Chat

```
You: Check the TextSpace server status
Kiro: [calls server_status tool]
      The server is running version 2.0.7

You: Update the lobby room description
Kiro: [calls read_config, modifies, validates, writes]
      Configuration updated successfully

You: Run the full test suite
Kiro: [calls run_tests with test_type="full"]
      All 8 tests passed!
```

### Agent Integration

The TextSpace agent can be invoked by Kiro for complex workflows:

```
You: Deploy the latest configuration changes
Kiro: [uses TextSpaceAgent.deploy_update()]
      1. Health check: healthy
      2. Updated rooms.yaml
      3. Version incremented to 2.0.8
      4. Server restarted
      5. Final health: healthy
      Deployment completed successfully!
```

## Testing the MCP Server

### Basic Test

```bash
cd /Users/earchibald/scratch/006-mats
python3 test_mcp_client.py
```

Expected output:
```
Available tools:
  - server_status: Check TextSpace server status and version
  - server_logs: Get recent server logs
  - server_start: Start the TextSpace server
  - server_stop: Stop the TextSpace server
  - read_config: Read TextSpace configuration files
  - write_config: Write TextSpace configuration files with validation
  - validate_config: Validate YAML configuration without writing
  - increment_version: Increment server version number
  - connect_websocket: Connect to running TextSpace server via WebSocket
  - send_command: Send command to TextSpace server
  - get_messages: Get recent WebSocket messages from server
  - run_tests: Run automated test suite

🔍 Testing server status...
Status: {"running": true, "version": "2.0.7", ...}

📖 Testing config reading...
Rooms config loaded successfully

✅ Testing config validation...
Validation result: True

✅ MCP server test completed!
```

### Agent Test

```bash
cd /Users/earchibald/scratch/006-mats
python3 textspace_agent.py
```

## Troubleshooting

### MCP Server Won't Start

```bash
# Check Python version (need 3.8+)
python3 --version

# Check dependencies
pip install mcp websocket-client pyyaml

# Test directly
python3 textspace_mcp_server.py
```

### WebSocket Connection Fails

```bash
# Ensure TextSpace server is running
python3 server_web_only.py

# Check port 5000 is available
lsof -i :5000

# Test WebSocket manually
wscat -c ws://localhost:5000
```

### Configuration Validation Fails

```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('rooms.yaml'))"

# Use validate_config tool first
# It will show specific validation errors
```

## Security Considerations

- **Admin Commands**: send_command with username="admin" has full privileges
- **Configuration Backups**: All config writes create timestamped backups
- **Validation**: All YAML is validated before writing to prevent corruption
- **Local Only**: MCP server designed for local development use

## Future Enhancements

- [ ] Remote server management (SSH/Railway)
- [ ] Automated deployment to Railway
- [ ] Git integration for config versioning
- [ ] Real-time log streaming
- [ ] Performance metrics collection
- [ ] User management tools
- [ ] Bot script debugging tools
- [ ] Visual configuration editor

## Files

- `textspace_mcp_server.py` - Main MCP server implementation
- `textspace_agent.py` - High-level management agent
- `test_mcp_client.py` - MCP server test client
- `.kiro/settings/mcp.json` - Kiro CLI MCP configuration
- `README_MCP.md` - This documentation

## Support

For issues or questions:
1. Check server logs: `tail -f textspace.log`
2. Run health check: Use `server_status` and `run_tests` tools
3. Review backups: Check for `*.backup.*` files in project directory

---

**Version**: 1.0  
**Last Updated**: 2025-12-21  
**Status**: Production Ready
