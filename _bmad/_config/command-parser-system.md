# TextSpace Command Parser System

## Architecture Overview

The TextSpace MUD uses a sophisticated command parsing system built around three core components:

1. **Command Registry** - Metadata-driven command definitions
2. **Command Resolution** - Intelligent command matching with aliases  
3. **Tab Completion** - Contextual argument completion system with universal user support

## Recent Architecture Updates (v2.7.x)

### Universal Tab Completion Support
- **Non-logged-in user support**: Creates temporary user context for completion
- **Client-side currentUser fix**: Direct assignment from login response
- **Command context display**: Shows full command in completion options
- **Independent alias completion**: Aliases work regardless of main command matching

### Enhanced User Experience
- **Organized help display**: Clean columnar format for empty TAB completion
- **Permission-aware completions**: Admin commands shown only to admin users
- **Graceful logout**: quit/logout command with session cleanup
- **MOTD system**: Message of the Day with admin/user permission differentiation

## Command Registry System

### Core Classes

#### Command Class
```python
class Command:
    def __init__(self, name, handler, admin_only=False, args_required=0, usage="", aliases=None, arg_types=None):
        self.name = name              # Primary command name
        self.handler = handler        # Function to execute
        self.admin_only = admin_only  # Admin permission required
        self.args_required = args_required  # Minimum arguments
        self.usage = usage           # Help text display
        self.aliases = aliases or [] # Alternative command names
        self.arg_types = arg_types or []  # Argument types for completion
```

#### CommandRegistry Class
```python
class CommandRegistry:
    def register(self, command)     # Register command and aliases
    def get_command(self, name)     # Get command by name or alias
    def get_all_commands(self, admin_only=False)  # Get filtered commands
```

### Command Registration Examples

```python
# Basic command
self.command_registry.register(Command("help", self.handle_help, usage="help"))

# Unified command with aliases (look/examine consolidation)
self.command_registry.register(Command("look", self.handle_look_cmd, 
    usage="look [target]", 
    aliases=["l", "examine", "exam"], 
    arg_types=["examinable"]))

# User session command
self.command_registry.register(Command("quit", self.handle_quit_cmd, 
    usage="quit", 
    aliases=["logout"]))

# MOTD command (permission-aware usage)
self.command_registry.register(Command("motd", self.handle_motd_cmd, 
    usage="motd"))  # Usage varies by admin status

# Admin-only command
self.command_registry.register(Command("teleport", self.handle_teleport_cmd, 
    admin_only=True, 
    usage="teleport [room]", 
    arg_types=["room"]))
``` 
    usage="teleport [room]", 
    arg_types=["room"]))
```

## Command Resolution System

### Resolution Algorithm

1. **Exact Alias Match** - Single-letter commands (n, s, e, w, l, g, i, h, v)
2. **Exact Command Match** - Full command name
3. **Partial Match** - Commands starting with input
4. **Ambiguity Handling** - Returns "AMBIGUOUS:cmd1,cmd2" for multiple matches

### Permission-Based Command Lists

- **Basic Commands**: help, version, whoami, look, who, inventory, say, whisper, get, take, drop, examine, exam, use, go, move, north, south, east, west
- **Admin Commands**: teleport, broadcast, kick, switchuser, script

### Example Resolution Flow
```
Input: "tel" + Admin User
→ Partial matches: ["teleport"]
→ Result: "teleport"

Input: "ex" + Regular User  
→ Partial matches: ["examine", "exam"]
→ Result: "AMBIGUOUS:examine,exam"
```

## Tab Completion System

### Universal Completion Support (v2.7.x)

#### Non-Logged-In User Support
- **Temporary user context**: Creates WebUser instance for completion when user not in active sessions
- **Admin detection**: Determines admin status from username (admin/tester-admin)
- **No session dependency**: Tab completion works before login

#### Client-Server Integration
- **Direct currentUser assignment**: Set from login_response data, not message parsing
- **Robust session handling**: Works across login/logout cycles
- **Context-aware display**: Shows command context in completion options

### Completion Types

#### Command Completion
- **Main commands**: Direct name matching
- **Alias completion**: Independent of main command name matching
- **Permission filtering**: Admin commands shown only to admin users
- **Common prefix extension**: Bash-like intelligent completion

#### Empty Tab Completion
Shows organized help display:
```
Available Commands:

  Basic:        help, version, whoami, who, motd, quit (logout)
  Look:         look (l, examine, exam) [target]
  Items:        get (take) <item>, drop <item>, use <item>
  Interact:     open <item>, close <item>
  Chat:         say <message>, whisper <target> <message>
  Movement:     go (move, g) <direction>, north (n), south (s), east (e), west (w)
  Inventory:    inventory (i)
  
  Admin:        teleport [room], motd [message]  (admin only)
```

#### Argument Completion
- **Context display**: Shows "examine ": targets instead of "": targets
- **Contextual targets**: Based on command and argument position
- **Permission-aware**: Respects user permissions for target visibility

### Argument Types

| Type | Description | Context |
|------|-------------|---------|
| `room_item` | Items in current room | Available for pickup |
| `inventory_item` | Items in user inventory | Available for use/drop |
| `examinable` | All examinable targets | Room items + inventory + users + visible bots |
| `openable`/`closeable` | Interactive containers | Room items + inventory |
| `direction` | Movement directions | north, south, east, west, up, down |
| `user` | Other players | Users in current room |
| `room` | Available rooms | All room IDs (admin only) |

### Completion Context Generation

```python
def get_completion_context(self, username, arg_type):
    """Generate contextual completion options"""
    # Examples:
    # "get <TAB>" → Shows room items
    # "drop <TAB>" → Shows inventory items  
    # "whisper <TAB>" → Shows users in room
    # "examine <TAB>" → Shows all examinable targets
```

### Empty Tab Completion

When user presses TAB on empty input, shows organized help:

```
Available Commands:

  Basic:        help, version, whoami, who
  Look:         look (l, examine, exam) [target]
  Items:        get (take) <item>, drop <item>, use <item>
  Interact:     open <item>, close <item>
  Chat:         say <message>, whisper <target> <message>
  Movement:     go (move, g) <direction>, north (n), south (s), east (e), west (w)
  Inventory:    inventory (i)
  
  Admin:        teleport [room]
```

## Client-Server Integration

### API Endpoint
```
GET /api/completions?partial=<text>&user=<username>&text=<full_command>
```

### Response Format
```json
{
  "completions": [
    {
      "name": "command_name",
      "usage": "command_name <args>",
      "aliases": ["alias1", "alias2"],
      "admin_only": false,
      "type": "command|argument|help"
    }
  ]
}
```

### Client-Side Behavior

1. **Single Match** - Auto-complete command/argument with space
2. **Multiple Matches** - Extend to common prefix or show options with context
3. **Help Display** - Show formatted help for empty input
4. **Intelligent Prefix** - Bash-like completion with common prefix detection
5. **Context Display** - Show full command context: "examine ": targets

### Recent Bug Fixes (v2.7.1 - v2.7.4)
- **Universal user support**: Fixed completion for non-logged-in users
- **Client-side currentUser**: Fixed via direct login response assignment
- **Command context**: Fixed missing verb in completion options display
- **Alias completion**: Fixed independent alias matching logic

## Key Features

### Universal Access
- **Works for all users**: Logged-in, non-logged-in, admin, regular users
- **No session dependency**: Tab completion available immediately
- **Permission-aware**: Commands filtered by admin status
- **Robust error handling**: Graceful fallbacks for edge cases

### Intelligent Matching
- **Independent alias completion**: Aliases work regardless of main command matching
- **Handles ambiguous commands** gracefully with clear error messages
- **Context-aware argument completion**: Shows relevant targets based on command
- **Common prefix extension**: Bash-like intelligent completion behavior

### User Experience
- **Organized help display**: Clean columnar format for command discovery
- **Command context display**: Shows full command in completion options
- **Permission-based filtering**: Admin commands hidden from regular users
- **Consistent behavior**: Works across all command types and user states

### Session Management
- **Graceful logout**: quit/logout command with proper cleanup
- **MOTD integration**: Message of the Day with permission-aware display
- **Persistent user data**: Maintains user state across sessions
- **WebSocket cleanup**: Proper connection management

## Implementation Files

- `command_registry.py` - Core registry classes and Command definition
- `server_web_only.py` - Command resolution, completion logic, and handlers
- `templates/index.html` - Client-side tab completion JavaScript with universal support

## Version History

### v2.7.4 (Current)
- **Fixed**: Independent alias completion logic
- **Improved**: Command expansion for all aliases (e.g., 'exa' → 'examine')

### v2.7.3  
- **Added**: Command context display in completion options
- **Improved**: UX with "examine ": targets instead of "": targets

### v2.7.2
- **Fixed**: Client-side currentUser assignment from login response
- **Improved**: Immediate tab completion availability after login

### v2.7.1
- **Added**: Universal tab completion support for non-logged-in users
- **Fixed**: Temporary user context creation for completion

### v2.7.0
- **Added**: quit/logout command with session cleanup
- **Improved**: User session management

### v2.6.0
- **Added**: MOTD (Message of the Day) functionality
- **Improved**: Permission-aware command help display

## Future Enhancements

- **Dynamic command loading**: From configuration files
- **Custom argument validators**: Enhanced input validation
- **Command history and favorites**: User preference system
- **Multi-word command support**: Complex command structures
- **Contextual help system**: Game state-aware assistance
- **Command macros**: User-defined command shortcuts
