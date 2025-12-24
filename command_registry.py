"""
Command Registry System for TextSpace
Provides a generalized command parser with metadata-driven validation
"""

class Command:
    """Represents a command with its metadata and validation rules"""
    def __init__(self, name, handler, admin_only=False, args_required=0, usage="", aliases=None):
        self.name = name
        self.handler = handler
        self.admin_only = admin_only
        self.args_required = args_required
        self.usage = usage
        self.aliases = aliases or []

class CommandRegistry:
    """Registry for all available commands"""
    def __init__(self):
        self.commands = {}
        self.aliases = {}
    
    def register(self, command):
        """Register a command and its aliases"""
        self.commands[command.name] = command
        for alias in command.aliases:
            self.aliases[alias] = command.name
    
    def get_command(self, name):
        """Get command by name or alias"""
        # Check direct name first
        if name in self.commands:
            return self.commands[name]
        # Check aliases
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        return None
    
    def get_all_commands(self, admin_only=False):
        """Get all commands, optionally filtered by admin status"""
        if admin_only:
            return {name: cmd for name, cmd in self.commands.items() if cmd.admin_only}
        return self.commands.copy()
