"""
Command Parser Framework for TextSpace MUD
A clean, extensible parser system with pattern matching and context-aware argument parsing.

Design Principles:
1. Separation of concerns: parsing, validation, execution
2. Extensible pattern matching for complex grammar
3. Context-aware argument resolution
4. Clear error messages with usage hints
5. Type-safe argument handling
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Callable, Any
from enum import Enum
import re


class ArgType(Enum):
    """Argument types for context-aware parsing"""
    STRING = "string"              # Any text
    USER = "user"                  # Username in current room
    ROOM_ITEM = "room_item"        # Item in current room or open containers
    INVENTORY_ITEM = "inv_item"    # Item in user's inventory
    EXAMINABLE = "examinable"      # Any examinable entity
    EXIT = "exit"                  # Valid exit from current room
    ROOM = "room"                  # Room ID
    CONTAINER = "container"        # Container item
    MESSAGE = "message"            # Remaining text as single argument


@dataclass
class ParsedCommand:
    """Result of command parsing"""
    command_name: str
    args: List[str]
    raw_text: str
    pattern: Optional[str] = None  # For complex grammar patterns
    
    def __repr__(self):
        return f"ParsedCommand(cmd={self.command_name}, args={self.args}, pattern={self.pattern})"


@dataclass
class CommandPattern:
    """Defines a command pattern with prepositions or complex grammar"""
    pattern_id: str                    # Unique pattern identifier (e.g., "put_in")
    regex: str                         # Regex pattern to match
    arg_groups: List[str]              # Named groups from regex
    arg_types: List[ArgType]           # Type for each arg group
    usage_example: str                 # Example usage
    
    def matches(self, text: str) -> Optional[Tuple[List[str], List[ArgType]]]:
        """Check if text matches this pattern and extract arguments"""
        match = re.match(self.regex, text, re.IGNORECASE)
        if match:
            groups = [match.group(i+1) for i in range(len(self.arg_groups))]
            return groups, self.arg_types
        return None


class CommandParser:
    """
    Extensible command parser with pattern matching support.
    Handles both simple commands and complex grammar with prepositions.
    """
    
    def __init__(self):
        self.patterns = {}  # pattern_id -> CommandPattern
        self._init_default_patterns()
    
    def _init_default_patterns(self):
        """Initialize default command patterns"""
        # PUT patterns
        self.register_pattern(CommandPattern(
            pattern_id="put_in",
            regex=r"^(.+?)\s+(?:in|into)\s+(.+)$",
            arg_groups=["item", "container"],
            arg_types=[ArgType.INVENTORY_ITEM, ArgType.CONTAINER],
            usage_example="put gold coin in treasure chest"
        ))
        
        # GIVE patterns
        self.register_pattern(CommandPattern(
            pattern_id="give_to",
            regex=r"^(.+?)\s+(?:to)\s+(.+)$",
            arg_groups=["item", "target"],
            arg_types=[ArgType.INVENTORY_ITEM, ArgType.USER],
            usage_example="give sword to warrior"
        ))
        
        # WHISPER patterns (user message)
        self.register_pattern(CommandPattern(
            pattern_id="whisper_to",
            regex=r"^(\w+)\s+(.+)$",
            arg_groups=["user", "message"],
            arg_types=[ArgType.USER, ArgType.MESSAGE],
            usage_example="whisper alice hello there"
        ))
    
    def register_pattern(self, pattern: CommandPattern):
        """Register a new command pattern"""
        self.patterns[pattern.pattern_id] = pattern
    
    def parse(self, raw_input: str) -> ParsedCommand:
        """
        Parse raw command input into structured ParsedCommand.
        Returns ParsedCommand with command name and arguments.
        """
        if not raw_input or not raw_input.strip():
            return ParsedCommand("", [], "")
        
        parts = raw_input.strip().split(maxsplit=1)
        cmd_name = parts[0].lower()
        args_text = parts[1] if len(parts) > 1 else ""
        
        # Handle quote alias for 'say' command
        if cmd_name.startswith('"'):
            # Special case: "message => say message
            message = raw_input[1:].strip() if len(raw_input) > 1 else ""
            return ParsedCommand("say", [message], raw_input)
        
        # For simple commands (no complex patterns), just split args
        simple_args = args_text.split() if args_text else []
        
        return ParsedCommand(
            command_name=cmd_name,
            args=simple_args,
            raw_text=raw_input,
            pattern=None
        )
    
    def parse_with_pattern(self, cmd_name: str, args_text: str) -> Optional[Tuple[str, List[str], List[ArgType]]]:
        """
        Try to match args against registered patterns for this command.
        Returns (pattern_id, parsed_args, arg_types) if matched, None otherwise.
        """
        if not args_text:
            return None
        
        # Try each pattern
        for pattern_id, pattern in self.patterns.items():
            result = pattern.matches(args_text)
            if result:
                parsed_args, arg_types = result
                return pattern_id, parsed_args, arg_types
        
        return None
    
    def get_usage_hints(self, cmd_name: str) -> List[str]:
        """Get usage hints for commands with patterns"""
        hints = []
        for pattern in self.patterns.values():
            hints.append(f"  {cmd_name} {pattern.usage_example}")
        return hints


class ArgumentResolver:
    """
    Resolves argument references to actual game objects.
    Context-aware resolution based on user location and inventory.
    """
    
    def __init__(self, context_provider: Callable):
        """
        Initialize with a context provider function.
        context_provider(username, arg_type) -> List[str] of available options
        """
        self.get_context = context_provider
    
    def resolve(self, username: str, arg: str, arg_type: ArgType) -> Optional[Any]:
        """
        Resolve an argument to a game object based on type.
        Returns the resolved object or None if not found.
        """
        if arg_type == ArgType.MESSAGE:
            # Messages are passed through as-is
            return arg
        
        if arg_type == ArgType.STRING:
            return arg
        
        # Get context-appropriate options
        options = self.get_context(username, arg_type.value)
        
        # Try exact match first
        if arg in options:
            return arg
        
        # Try case-insensitive match
        arg_lower = arg.lower()
        for option in options:
            if option.lower() == arg_lower:
                return option
        
        # Try partial match (prefix)
        matches = [opt for opt in options if opt.lower().startswith(arg_lower)]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            return f"AMBIGUOUS:{','.join(matches)}"
        
        return None


class CommandValidator:
    """
    Validates commands before execution.
    Checks permissions, argument counts, and types.
    """
    
    def __init__(self, command_registry):
        self.registry = command_registry
    
    def validate(self, parsed_cmd: ParsedCommand, user_is_admin: bool) -> Tuple[bool, Optional[str]]:
        """
        Validate parsed command.
        Returns (is_valid, error_message)
        """
        # Get command definition
        cmd_def = self.registry.get_command(parsed_cmd.command_name)
        if not cmd_def:
            return False, f"Unknown command: {parsed_cmd.command_name}"
        
        # Check admin permissions
        if cmd_def.admin_only and not user_is_admin:
            return False, "Access denied. Admin privileges required."
        
        # Check argument count
        if len(parsed_cmd.args) < cmd_def.args_required:
            return False, f"Usage: {cmd_def.usage}"
        
        return True, None


class CommandExecutor:
    """
    Executes validated commands.
    Handles both simple and pattern-based commands.
    """
    
    def __init__(self, command_registry, parser, resolver):
        self.registry = command_registry
        self.parser = parser
        self.resolver = resolver
    
    def execute(self, parsed_cmd: ParsedCommand, web_user) -> str:
        """Execute a parsed and validated command"""
        cmd_def = self.registry.get_command(parsed_cmd.command_name)
        if not cmd_def:
            return f"Unknown command: {parsed_cmd.command_name}"
        
        try:
            # Execute command handler
            return cmd_def.handler(web_user, parsed_cmd.args)
        except Exception as e:
            return f"Error executing command: {str(e)}"


class CommandProcessor:
    """
    Main command processing pipeline.
    Orchestrates parsing, validation, and execution.
    """
    
    def __init__(self, command_registry, context_provider):
        self.registry = command_registry
        self.parser = CommandParser()
        self.resolver = ArgumentResolver(context_provider)
        self.validator = CommandValidator(command_registry)
        self.executor = CommandExecutor(command_registry, self.parser, self.resolver)
    
    def process(self, username: str, raw_command: str, web_user) -> str:
        """
        Process a command through the full pipeline:
        1. Parse input into structured command
        2. Resolve command aliases
        3. Validate permissions and arguments
        4. Execute command handler
        """
        # Step 1: Parse
        parsed = self.parser.parse(raw_command)
        if not parsed.command_name:
            return "Please enter a command. Type 'help' for available commands."
        
        # Step 2: Resolve aliases
        resolved_cmd = self._resolve_command_name(parsed.command_name, web_user.admin)
        if resolved_cmd.startswith("AMBIGUOUS:"):
            matches = resolved_cmd.split(":")[1].split(",")
            return f"Ambiguous command. Did you mean: {', '.join(matches)}?"
        
        parsed.command_name = resolved_cmd
        
        # Step 3: Validate
        is_valid, error = self.validator.validate(parsed, web_user.admin)
        if not is_valid:
            return error
        
        # Step 4: Execute
        return self.executor.execute(parsed, web_user)
    
    def _resolve_command_name(self, cmd_name: str, is_admin: bool):
        """Resolve command name through aliases and partial matches"""
        # Direct match
        if self.registry.get_command(cmd_name):
            return cmd_name
        
        # Check aliases
        if cmd_name in self.registry.aliases:
            return self.registry.aliases[cmd_name]
        
        # Partial matching
        matches = []
        for name in self.registry.commands:
            cmd = self.registry.commands[name]
            if cmd.admin_only and not is_admin:
                continue
            if name.startswith(cmd_name):
                matches.append(name)
        
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            return f"AMBIGUOUS:{','.join(matches)}"
        
        return cmd_name  # Return as-is if no match (will fail validation)
