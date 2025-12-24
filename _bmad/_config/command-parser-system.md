# TextSpace Command Parser System

## Architecture Overview

The TextSpace MUD uses a sophisticated command parsing system built around three core components:

1. **Command Registry** - Metadata-driven command definitions
2. **Command Resolution** - Intelligent command matching with aliases
3. **Tab Completion** - Contextual argument completion system

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

# Command with aliases
self.command_registry.register(Command("look", self.handle_look_cmd, 
    usage="look [target]", 
    aliases=["l", "examine", "exam"], 
    arg_types=["examinable"]))

# Admin-only command
self.command_registry.register(Command("teleport", self.handle_teleport_cmd, 
    admin_only=True, 
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

### Completion Types

#### Command Completion
- Shows available commands based on user permissions
- Handles partial matching and common prefix extension
- Empty input shows organized help display

#### Argument Completion
- Context-aware based on `arg_types` in command definition
- Provides relevant targets for each argument position

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

1. **Single Match** - Auto-complete command/argument
2. **Multiple Matches** - Extend to common prefix or show options
3. **Help Display** - Show formatted help for empty input
4. **Intelligent Prefix** - Bash-like completion with common prefix detection

## Key Features

### Permission-Aware
- Commands filtered by admin status
- Bot visibility respects user permissions
- Contextual completions based on user access

### Intelligent Matching
- Handles ambiguous commands gracefully
- Supports both full names and aliases
- Provides helpful error messages

### Extensible Design
- Easy to add new commands via registration
- Argument types support new completion contexts
- Modular handler system

### User Experience
- Consistent tab completion across all commands
- Contextual help and suggestions
- Clean, organized command reference

## Implementation Files

- `command_registry.py` - Core registry classes
- `server_web_only.py` - Command resolution and completion logic
- `templates/index.html` - Client-side tab completion JavaScript

## Future Enhancements

- Dynamic command loading from configuration
- Custom argument validators
- Command history and favorites
- Multi-word command support
- Contextual help based on current game state
