# MCP Login Functionality Guide

## Overview

The MCP (Model Context Protocol) Login functionality allows MCP clients to establish proper user sessions with the TextSpace server. This enables testing and interaction with features that require logged-in users, such as:

- Complex tab completion with room state
- Inventory management
- Container interactions
- Room-specific commands
- User-specific game state

## Features

### Three New MCP Tools

1. **mcp_login** - Establish user session
2. **mcp_logout** - Close current session
3. **mcp_status** - Show session information

### Enhanced send_command Tool

The `send_command` tool now automatically:
- Detects active MCP sessions
- Uses full user context when logged in
- Falls back to WebSocket mode when not logged in
- Maintains backward compatibility

## Usage Examples

### Basic Login Flow

```python
# 1. Check current status (should show no session)
mcp_status()
# Response: "No Active MCP Session"

# 2. Login as a user
mcp_login(username="test_user", admin=False)
# Response: 
# ✅ MCP Login Successful
# Username: test_user
# Admin: False
# Room: lobby

# 3. Check status again (should show logged-in user)
mcp_status()
# Response:
# ✅ MCP Session Active
# Username: test_user
# Admin: False
# Room: The Lobby
# Login Time: 2025-12-25T00:00:00.000000
# Inventory: Empty

# 4. Send commands (automatically uses session)
send_command(command="look")
# Response shows room description with user context

send_command(command="inventory")
# Response shows user's inventory

# 5. Logout when done
mcp_logout()
# Response: ✅ MCP Logout Successful
```

### Admin Login

```python
# Login as admin to access admin commands
mcp_login(username="admin", admin=True)

# Or use recognized admin username
mcp_login(username="admin")  # Automatically gets admin privileges

# Now can use admin commands
send_command(command="teleport castle")
send_command(command="broadcast Hello everyone!")
```

### Testing Complex Features

```python
# Login to test inventory and containers
mcp_login(username="tester")

# Pick up items
send_command(command="get Gold Coin")
send_command(command="get Treasure Chest")

# Check inventory
send_command(command="inventory")

# Open container
send_command(command="open Treasure Chest")

# Put items in container
send_command(command="put Gold Coin in Treasure Chest")

# Look at container contents
send_command(command="look Treasure Chest")

# Clean up
mcp_logout()
```

### Multiple User Testing

```python
# Simulate multi-user scenarios

# User 1
mcp_login(username="alice")
send_command(command="say Hello!")
mcp_logout()

# User 2
mcp_login(username="bob")
send_command(command="say Hi Alice!")
send_command(command="who")  # See who's online
mcp_logout()
```

## Technical Details

### Session Management

- MCP sessions are tracked separately from WebSocket sessions
- Session state stored in `mcp_sessions` dictionary
- Current active user stored in `mcp_current_user`
- Sessions persist across command executions
- User data (room, inventory) automatically saved on logout

### API Endpoints

The following API endpoints support MCP login functionality:

#### POST /api/mcp/login
Establish MCP user session.

**Request:**
```json
{
  "username": "test_user",
  "admin": false
}
```

**Response:**
```json
{
  "success": true,
  "username": "test_user",
  "admin": false,
  "room_id": "lobby",
  "message": "MCP user test_user logged in successfully"
}
```

#### POST /api/mcp/logout
Close current MCP session.

**Response:**
```json
{
  "success": true,
  "message": "MCP user test_user logged out successfully"
}
```

#### GET /api/mcp/status
Get current MCP session status.

**Response (logged in):**
```json
{
  "logged_in": true,
  "username": "test_user",
  "admin": false,
  "room_id": "lobby",
  "room_name": "The Lobby",
  "login_time": "2025-12-25T00:00:00.000000",
  "session_id": "mcp_test_user",
  "inventory": ["Gold Coin", "Magic Wand"]
}
```

**Response (not logged in):**
```json
{
  "logged_in": false,
  "message": "No active MCP session"
}
```

#### POST /api/command
Execute command with session awareness.

**Request:**
```json
{
  "command": "look",
  "username": ""  // Optional, uses MCP session if available
}
```

**Response:**
```json
{
  "success": true,
  "result": "You are in The Lobby...",
  "username": "test_user",
  "session_type": "mcp_logged_in"
}
```

### Session Types

The `/api/command` endpoint reports different session types:

- **mcp_logged_in** - Using active MCP session with full user context
- **temporary** - Temporary user created for command execution
- **mcp_cleaned_up** - Invalid session was detected and cleaned up
- **no_session** - No session and no username provided

### Admin Username Detection

The following usernames automatically receive admin privileges:
- `admin`
- `tester-admin`

This logic is centralized in the `is_admin_username()` helper method.

### Session Persistence

- User room location persisted to `users.json`
- User inventory persisted to `users.json`
- Session data loaded on login if available
- Data saved on logout

### Error Handling

The implementation handles several error scenarios:

1. **Inconsistent Session State**: If MCP session exists but user data is missing, the session is automatically cleaned up
2. **No Username Provided**: Clear error message requesting login or username
3. **Session Already Exists**: Existing session is replaced on new login
4. **Invalid Credentials**: Proper error responses for malformed requests

## Integration with Existing Features

### Tab Completion

MCP-logged-in users benefit from contextual tab completion:
- Room items available for pickup
- Inventory items available for use/drop
- Open containers for "put" command
- Other users for "whisper" command
- Valid room names for "teleport" command (admins)

### Room State

Logged-in users have access to:
- Current room description
- Items in the room
- Other users in the room
- Valid exits
- Room-specific scripts

### User State

Logged-in users maintain:
- Personal inventory
- Current room location
- Admin privileges
- Session history

## Best Practices

1. **Always logout when done**: Use `mcp_logout()` to properly clean up sessions
2. **Check status first**: Use `mcp_status()` to verify session state
3. **One session at a time**: MCP supports one active session per server
4. **Use descriptive usernames**: Makes testing and debugging easier
5. **Test as different users**: Create separate sessions to test multi-user features

## Troubleshooting

### "No active MCP session" error
- Make sure you called `mcp_login()` successfully
- Check `mcp_status()` to verify session state
- Try logging in again if session was lost

### "MCP session was invalid" error
- Session became inconsistent (rare)
- Session was automatically cleaned up
- Simply call `mcp_login()` again

### Commands not working as expected
- Verify you're logged in with `mcp_status()`
- Check if the command requires admin privileges
- Ensure user is in correct room for room-specific commands

### Session persists after logout
- This shouldn't happen, but if it does:
- Check `mcp_status()` to confirm
- Try logging in and out again
- Check server logs for errors

## Security Notes

- All MCP API endpoints are IP-whitelisted
- Only whitelisted IPs (configured in `API_WHITELIST`) can access MCP functionality
- Admin privileges are controlled by username or explicit flag
- Sessions are server-side only, no client-side persistence

## Future Enhancements

Potential improvements for future versions:

- Multiple concurrent MCP sessions
- Session timeout/expiration
- Session authentication tokens
- Session activity logging
- Session transfer between users
- Batch command execution with session
