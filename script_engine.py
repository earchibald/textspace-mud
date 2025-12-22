#!/usr/bin/env python3
import re
from typing import Dict, Any, List

class ScriptEngine:
    def __init__(self, server):
        self.server = server
        self.variables: Dict[str, Any] = {}
        self.functions = {
            'say': self._say,
            'move': self._move,
            'wait': self._wait,
            'set': self._set,
            'get': self._get,
            'if': self._if,
            'broadcast': self._broadcast,
            'random_say': self._random_say,
            'repeat': self._repeat,
            'function': self._function,
            'call': self._call,
            'give': self._give,
            'take': self._take
        }
        self.user_functions: Dict[str, List[Dict]] = {}  # Custom functions
    
    def parse_script(self, script_text: str) -> List[Dict]:
        """Parse script into executable commands"""
        commands = []
        lines = script_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse command and arguments
            parts = line.split(' ', 1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            
            commands.append({'command': cmd, 'args': args})
        
        return commands
    
    async def execute_script(self, script_text: str, bot_name: str):
        """Execute a script for a bot"""
        commands = self.parse_script(script_text)
        await self._execute_commands(commands, bot_name)
    
    async def _execute_commands(self, commands: List[Dict], bot_name: str):
        """Execute a list of commands"""
        i = 0
        while i < len(commands):
            cmd_data = commands[i]
            cmd = cmd_data['command']
            args = cmd_data['args']
            
            if cmd in self.functions:
                result = await self.functions[cmd](bot_name, args)
                # Handle control flow returns
                if isinstance(result, dict) and 'jump' in result:
                    i = result['jump']
                    continue
            
            i += 1
    
    async def _say(self, bot_name: str, message: str):
        """Bot says something in its current room"""
        if bot_name.startswith("item_") or bot_name.startswith("web_item_"):
            # Handle item scripts - broadcast to user's room
            item_id = bot_name.split("_", 1)[1]  # Remove prefix
            # Find which user used the item (simplified - could be enhanced)
            for user in self.server.users.values():
                if item_id in user.inventory:
                    await self.server.send_to_room(user.room_id, message)
                    break
            # Also check web users
            for web_user in self.server.web_users.values():
                if item_id in web_user.inventory:
                    self.server.socketio.emit('message', {'text': message}, room=web_user.room_id)
                    self.server.send_to_room(web_user.room_id, message, exclude_user=web_user.name)
                    break
        else:
            bot = self.server.bots.get(bot_name)
            if bot:
                # Send message to all web users in the same room
                message_text = f"{bot.name} says: {message}"
                for web_user in self.server.web_users.values():
                    if web_user.room_id == bot.room_id:
                        self.server.socketio.emit('message', {'text': message_text}, room=web_user.session_id)
    
    async def _move(self, bot_name: str, room_id: str):
        """Move bot to a different room"""
        bot = self.server.bots.get(bot_name)
        if bot and room_id in self.server.rooms:
            old_room = bot.room_id
            bot.room_id = room_id
            
            # Announce the move to users in both rooms
            for web_user in self.server.web_users.values():
                if web_user.room_id == old_room:
                    self.server.socketio.emit('message', {'text': f'{bot.name} leaves the room.'}, room=web_user.session_id)
                elif web_user.room_id == room_id:
                    self.server.socketio.emit('message', {'text': f'{bot.name} enters the room.'}, room=web_user.session_id)
    
    async def _wait(self, bot_name: str, seconds: str):
        """Wait for specified seconds"""
        import asyncio
        try:
            await asyncio.sleep(float(seconds))
        except ValueError:
            pass
    
    async def _set(self, bot_name: str, args: str):
        """Set a variable: set varname value"""
        parts = args.split(' ', 1)
        if len(parts) == 2:
            var_name, value = parts
            self.variables[f"{bot_name}_{var_name}"] = value
    
    async def _get(self, bot_name: str, var_name: str):
        """Get a variable value"""
        return self.variables.get(f"{bot_name}_{var_name}", "")
    
    async def _if(self, bot_name: str, condition: str):
        """Simple if statement: if var equals value then command"""
        # Simple parser for: var equals value then command
        match = re.match(r'(\w+) equals (\w+) then (.+)', condition)
        if match:
            var_name, expected, command = match.groups()
            actual = await self._get(bot_name, var_name)
            if actual == expected:
                # Execute the then command
                parts = command.split(' ', 1)
                cmd = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                if cmd in self.functions:
                    await self.functions[cmd](bot_name, args)
    
    async def _broadcast(self, bot_name: str, message: str):
        """Broadcast message to all users"""
        message_text = f"[{bot_name}] {message}"
        for web_user in self.server.web_users.values():
            self.server.socketio.emit('message', {'text': message_text}, room=web_user.session_id)
    
    async def _random_say(self, bot_name: str, messages: str):
        """Say one of several random messages: random_say msg1|msg2|msg3"""
        import random
        message_list = messages.split('|')
        if message_list:
            chosen = random.choice(message_list).strip()
            await self._say(bot_name, chosen)
    
    async def _repeat(self, bot_name: str, args: str):
        """Repeat commands: repeat 3 { say Hello; wait 1 }"""
        import re
        match = re.match(r'(\d+)\s*\{(.+)\}', args, re.DOTALL)
        if not match:
            return
        
        count = int(match.group(1))
        commands_text = match.group(2).strip()
        
        # Parse commands inside the block
        commands = []
        for line in commands_text.split(';'):
            line = line.strip()
            if line:
                parts = line.split(' ', 1)
                cmd = parts[0]
                cmd_args = parts[1] if len(parts) > 1 else ""
                commands.append({'command': cmd, 'args': cmd_args})
        
        # Execute the block multiple times
        for _ in range(count):
            await self._execute_commands(commands, bot_name)
    
    async def _function(self, bot_name: str, args: str):
        """Define a function: function greet { say Hello; wait 1 }"""
        import re
        match = re.match(r'(\w+)\s*\{(.+)\}', args, re.DOTALL)
        if not match:
            return
        
        func_name = match.group(1)
        commands_text = match.group(2).strip()
        
        # Parse function commands
        commands = []
        for line in commands_text.split(';'):
            line = line.strip()
            if line:
                parts = line.split(' ', 1)
                cmd = parts[0]
                cmd_args = parts[1] if len(parts) > 1 else ""
                commands.append({'command': cmd, 'args': cmd_args})
        
        # Store function
        func_key = f"{bot_name}_{func_name}"
        self.user_functions[func_key] = commands
    
    async def _call(self, bot_name: str, func_name: str):
        """Call a user-defined function: call greet"""
        func_key = f"{bot_name}_{func_name}"
        if func_key in self.user_functions:
            await self._execute_commands(self.user_functions[func_key], bot_name)
    
    async def _give(self, bot_name: str, args: str):
        """Give item to user: give magic_book alice"""
        parts = args.split(' ', 1)
        if len(parts) != 2:
            return
        
        item_id, user_name = parts
        user = self.server.users.get(user_name)
        bot = self.server.bots.get(bot_name)
        
        if user and bot and item_id in bot.inventory:
            bot.inventory.remove(item_id)
            user.inventory.append(item_id)
            await self._say(bot_name, f"*gives {self.server.items[item_id].name} to {user_name}*")
            self.server.save_user(user)
    
    async def _take(self, bot_name: str, args: str):
        """Take item from user: take magic_book alice"""
        parts = args.split(' ', 1)
        if len(parts) != 2:
            return
        
        item_id, user_name = parts
        user = self.server.users.get(user_name)
        bot = self.server.bots.get(bot_name)
        
        if user and bot and item_id in user.inventory:
            user.inventory.remove(item_id)
            bot.inventory.append(item_id)
            await self._say(bot_name, f"*takes {self.server.items[item_id].name} from {user_name}*")
            self.server.save_user(user)
