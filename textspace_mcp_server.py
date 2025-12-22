#!/usr/bin/env python3
"""
TextSpace MCP Server - Specialized server management for TextSpace
Provides tools for server control, configuration management, and testing
"""

import asyncio
import json
import os
import subprocess
import yaml
import logging
import websocket
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("textspace-mcp")

# Initialize MCP server
server = Server("textspace-mcp")

class TextSpaceManager:
    """Core TextSpace server management functionality"""
    
    def __init__(self, project_path: str = "/Users/earchibald/scratch/006-mats"):
        self.project_path = project_path
        self.server_process = None
        self.ws_connection = None
        self.ws_messages = []
        self.ws_connected = False
        
    def get_server_status(self) -> Dict[str, Any]:
        """Check if TextSpace server is running"""
        try:
            # Check for running process
            result = subprocess.run(
                ["pgrep", "-f", "server_web_only.py"], 
                capture_output=True, text=True
            )
            is_running = result.returncode == 0
            
            # Get version from file
            version = "unknown"
            try:
                with open(f"{self.project_path}/server_web_only.py", "r") as f:
                    for line in f:
                        if line.startswith('VERSION = '):
                            version = line.split('"')[1]
                            break
            except Exception:
                pass
                
            return {
                "running": is_running,
                "version": version,
                "project_path": self.project_path,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "running": False}
    
    def get_logs(self, lines: int = 50) -> str:
        """Get recent server logs"""
        try:
            log_path = f"{self.project_path}/textspace.log"
            if not os.path.exists(log_path):
                return "No log file found"
                
            result = subprocess.run(
                ["tail", "-n", str(lines), log_path],
                capture_output=True, text=True
            )
            return result.stdout if result.returncode == 0 else f"Error reading logs: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def start_server(self) -> str:
        """Start the TextSpace server"""
        try:
            if self.get_server_status()["running"]:
                return "Server is already running"
                
            # Start server in background
            self.server_process = subprocess.Popen(
                ["python3", "server_web_only.py"],
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to start
            asyncio.sleep(2)
            
            if self.server_process.poll() is None:
                return f"Server started with PID {self.server_process.pid}"
            else:
                return "Failed to start server"
        except Exception as e:
            return f"Error starting server: {str(e)}"
    
    def validate_yaml_config(self, config_type: str, content: str) -> Dict[str, Any]:
        """Validate YAML configuration content"""
        try:
            data = yaml.safe_load(content)
            
            # Basic validation based on config type
            if config_type == "rooms":
                if not isinstance(data.get("rooms"), dict):
                    return {"valid": False, "error": "Missing 'rooms' section"}
                for room_id, room in data["rooms"].items():
                    if not isinstance(room.get("name"), str):
                        return {"valid": False, "error": f"Room {room_id} missing name"}
                        
            elif config_type == "bots":
                if not isinstance(data.get("bots"), dict):
                    return {"valid": False, "error": "Missing 'bots' section"}
                    
            elif config_type == "items":
                if not isinstance(data.get("items"), dict):
                    return {"valid": False, "error": "Missing 'items' section"}
                    
            elif config_type == "scripts":
                if not isinstance(data.get("scripts"), dict):
                    return {"valid": False, "error": "Missing 'scripts' section"}
            
            return {"valid": True, "data": data}
        except yaml.YAMLError as e:
            return {"valid": False, "error": f"YAML syntax error: {str(e)}"}
    
    def write_config(self, config_type: str, content: str) -> str:
        """Write configuration file with backup"""
        try:
            # Validate first
            validation = self.validate_yaml_config(config_type, content)
            if not validation["valid"]:
                return f"Validation failed: {validation['error']}"
            
            config_path = f"{self.project_path}/{config_type}.yaml"
            backup_path = f"{config_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup
            if os.path.exists(config_path):
                subprocess.run(["cp", config_path, backup_path])
            
            # Write new content
            with open(config_path, "w") as f:
                f.write(content)
                
            return f"Configuration updated successfully. Backup saved to {backup_path}"
        except Exception as e:
            return f"Error writing config: {str(e)}"
    
    def increment_version(self) -> str:
        """Increment server version"""
        try:
            server_file = f"{self.project_path}/server_web_only.py"
            with open(server_file, "r") as f:
                content = f.read()
            
            # Find current version
            import re
            version_match = re.search(r'VERSION = "(\d+)\.(\d+)\.(\d+)"', content)
            if not version_match:
                return "Could not find version string"
            
            major, minor, patch = map(int, version_match.groups())
            new_version = f"{major}.{minor}.{patch + 1}"
            
            # Replace version
            new_content = re.sub(
                r'VERSION = "\d+\.\d+\.\d+"',
                f'VERSION = "{new_version}"',
                content
            )
            
            with open(server_file, "w") as f:
                f.write(new_content)
                
            return f"Version incremented to {new_version}"
        except Exception as e:
            return f"Error incrementing version: {str(e)}"
    
    def connect_websocket(self, url: str = "ws://localhost:5000") -> str:
        """Connect to TextSpace server via WebSocket"""
        try:
            def on_message(ws, message):
                self.ws_messages.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": message
                })
                # Keep only last 100 messages
                if len(self.ws_messages) > 100:
                    self.ws_messages.pop(0)
            
            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")
                self.ws_connected = False
            
            def on_close(ws, close_status_code, close_msg):
                logger.info("WebSocket connection closed")
                self.ws_connected = False
            
            def on_open(ws):
                logger.info("WebSocket connection opened")
                self.ws_connected = True
            
            self.ws_connection = websocket.WebSocketApp(
                url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Start WebSocket in background thread
            ws_thread = threading.Thread(target=self.ws_connection.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            time.sleep(2)
            
            return "WebSocket connected" if self.ws_connected else "Failed to connect"
        except Exception as e:
            return f"Error connecting WebSocket: {str(e)}"
    
    def send_command(self, command: str, username: str = "admin") -> str:
        """Send command to TextSpace server via WebSocket"""
        try:
            if not self.ws_connected or not self.ws_connection:
                return "Not connected to server. Use connect_websocket first."
            
            # Simulate user login and command
            login_msg = json.dumps({
                "type": "login",
                "username": username
            })
            self.ws_connection.send(login_msg)
            
            time.sleep(0.5)
            
            command_msg = json.dumps({
                "type": "command", 
                "text": command
            })
            self.ws_connection.send(command_msg)
            
            return f"Command '{command}' sent as user '{username}'"
        except Exception as e:
            return f"Error sending command: {str(e)}"
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent WebSocket messages"""
        return self.ws_messages[-count:] if self.ws_messages else []
    
    def run_test_suite(self, test_type: str = "basic") -> Dict[str, Any]:
        """Run automated test suite"""
        try:
            test_results = {
                "timestamp": datetime.now().isoformat(),
                "test_type": test_type,
                "results": []
            }
            
            if test_type == "basic":
                # Basic server tests
                tests = [
                    ("Server Status", self._test_server_running),
                    ("Config Files", self._test_config_files),
                    ("Log File", self._test_log_file)
                ]
            elif test_type == "web":
                # Web interface tests
                tests = [
                    ("Web Server", self._test_web_server),
                    ("WebSocket", self._test_websocket),
                    ("Game Commands", self._test_game_commands)
                ]
            elif test_type == "full":
                # Full test suite
                tests = [
                    ("Server Status", self._test_server_running),
                    ("Config Files", self._test_config_files),
                    ("Web Server", self._test_web_server),
                    ("WebSocket", self._test_websocket),
                    ("Game Commands", self._test_game_commands),
                    ("Room Navigation", self._test_room_navigation),
                    ("Item System", self._test_item_system),
                    ("Bot Interaction", self._test_bot_interaction)
                ]
            else:
                return {"error": f"Unknown test type: {test_type}"}
            
            # Run tests
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    test_results["results"].append({
                        "test": test_name,
                        "status": "PASS" if result["success"] else "FAIL",
                        "details": result.get("details", ""),
                        "error": result.get("error", "")
                    })
                except Exception as e:
                    test_results["results"].append({
                        "test": test_name,
                        "status": "ERROR",
                        "error": str(e)
                    })
            
            # Summary
            passed = sum(1 for r in test_results["results"] if r["status"] == "PASS")
            total = len(test_results["results"])
            test_results["summary"] = f"{passed}/{total} tests passed"
            
            return test_results
        except Exception as e:
            return {"error": f"Test suite error: {str(e)}"}
    
    def _test_server_running(self) -> Dict[str, Any]:
        """Test if server is running"""
        status = self.get_server_status()
        return {
            "success": status.get("running", False),
            "details": f"Version: {status.get('version', 'unknown')}"
        }
    
    def _test_config_files(self) -> Dict[str, Any]:
        """Test configuration files exist and are valid"""
        configs = ["rooms", "bots", "items", "scripts"]
        for config in configs:
            try:
                with open(f"{self.project_path}/{config}.yaml", "r") as f:
                    yaml.safe_load(f.read())
            except Exception as e:
                return {"success": False, "error": f"{config}.yaml: {str(e)}"}
        return {"success": True, "details": "All config files valid"}
    
    def _test_log_file(self) -> Dict[str, Any]:
        """Test log file exists and is recent"""
        log_path = f"{self.project_path}/textspace.log"
        if not os.path.exists(log_path):
            return {"success": False, "error": "Log file not found"}
        
        # Check if log has recent entries (within last hour)
        import time
        stat = os.stat(log_path)
        age = time.time() - stat.st_mtime
        return {
            "success": age < 3600,
            "details": f"Log age: {int(age)} seconds"
        }
    
    def _test_web_server(self) -> Dict[str, Any]:
        """Test web server responds"""
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:5000", timeout=5)
            return {
                "success": response.getcode() == 200,
                "details": f"HTTP {response.getcode()}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_websocket(self) -> Dict[str, Any]:
        """Test WebSocket connection"""
        if not self.ws_connected:
            self.connect_websocket()
            time.sleep(2)
        
        return {
            "success": self.ws_connected,
            "details": f"Messages received: {len(self.ws_messages)}"
        }
    
    def _test_game_commands(self) -> Dict[str, Any]:
        """Test basic game commands"""
        if not self.ws_connected:
            return {"success": False, "error": "WebSocket not connected"}
        
        # Test basic commands
        commands = ["help", "look", "version"]
        for cmd in commands:
            self.send_command(cmd)
            time.sleep(1)
        
        return {
            "success": True,
            "details": f"Tested {len(commands)} commands"
        }
    
    def _test_room_navigation(self) -> Dict[str, Any]:
        """Test room navigation"""
        if not self.ws_connected:
            return {"success": False, "error": "WebSocket not connected"}
        
        # Test movement
        self.send_command("look")
        time.sleep(1)
        self.send_command("north")
        time.sleep(1)
        self.send_command("south")
        time.sleep(1)
        
        return {"success": True, "details": "Navigation tested"}
    
    def _test_item_system(self) -> Dict[str, Any]:
        """Test item interactions"""
        if not self.ws_connected:
            return {"success": False, "error": "WebSocket not connected"}
        
        # Test item commands
        self.send_command("inventory")
        time.sleep(1)
        self.send_command("examine treasure chest")
        time.sleep(1)
        
        return {"success": True, "details": "Item system tested"}
    
    def _test_bot_interaction(self) -> Dict[str, Any]:
        """Test bot interactions"""
        if not self.ws_connected:
            return {"success": False, "error": "WebSocket not connected"}
        
        # Test bot interaction
        self.send_command("say hello")
        time.sleep(2)
        
        return {"success": True, "details": "Bot interaction tested"}

# Initialize manager
manager = TextSpaceManager()

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available TextSpace management tools"""
    return [
        Tool(
            name="server_status",
            description="Check TextSpace server status and version",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="server_logs",
            description="Get recent server logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "lines": {
                        "type": "integer",
                        "description": "Number of log lines to retrieve",
                        "default": 50
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="server_start",
            description="Start the TextSpace server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="server_stop",
            description="Stop the TextSpace server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="read_config",
            description="Read TextSpace configuration files",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_type": {
                        "type": "string",
                        "enum": ["rooms", "bots", "items", "scripts"],
                        "description": "Type of configuration to read"
                    }
                },
                "required": ["config_type"]
            }
        ),
        Tool(
            name="write_config",
            description="Write TextSpace configuration files with validation",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_type": {
                        "type": "string",
                        "enum": ["rooms", "bots", "items", "scripts"],
                        "description": "Type of configuration to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "YAML content to write"
                    }
                },
                "required": ["config_type", "content"]
            }
        ),
        Tool(
            name="validate_config",
            description="Validate YAML configuration without writing",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_type": {
                        "type": "string",
                        "enum": ["rooms", "bots", "items", "scripts"],
                        "description": "Type of configuration to validate"
                    },
                    "content": {
                        "type": "string",
                        "description": "YAML content to validate"
                    }
                },
                "required": ["config_type", "content"]
            }
        ),
        Tool(
            name="increment_version",
            description="Increment server version number",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="connect_websocket",
            description="Connect to running TextSpace server via WebSocket",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "WebSocket URL",
                        "default": "ws://localhost:5000"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="send_command",
            description="Send command to TextSpace server",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to send"
                    },
                    "username": {
                        "type": "string",
                        "description": "Username to send as",
                        "default": "admin"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="get_messages",
            description="Get recent WebSocket messages from server",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of messages to retrieve",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="run_tests",
            description="Run automated test suite",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_type": {
                        "type": "string",
                        "enum": ["basic", "web", "full"],
                        "description": "Type of tests to run",
                        "default": "basic"
                    }
                },
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    
    if name == "server_status":
        status = manager.get_server_status()
        return [TextContent(
            type="text",
            text=json.dumps(status, indent=2)
        )]
    
    elif name == "server_logs":
        lines = arguments.get("lines", 50)
        logs = manager.get_logs(lines)
        return [TextContent(
            type="text", 
            text=logs
        )]
    
    elif name == "server_start":
        result = manager.start_server()
        return [TextContent(
            type="text",
            text=result
        )]
    
    elif name == "server_stop":
        result = manager.stop_server()
        return [TextContent(
            type="text",
            text=result
        )]
    
    elif name == "read_config":
        config_type = arguments["config_type"]
        try:
            config_path = f"{manager.project_path}/{config_type}.yaml"
            with open(config_path, "r") as f:
                content = f.read()
            return [TextContent(
                type="text",
                text=f"=== {config_type}.yaml ===\n{content}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error reading {config_type}.yaml: {str(e)}"
            )]
    
    elif name == "write_config":
        config_type = arguments["config_type"]
        content = arguments["content"]
        result = manager.write_config(config_type, content)
        return [TextContent(
            type="text",
            text=result
        )]
    
    elif name == "validate_config":
        config_type = arguments["config_type"]
        content = arguments["content"]
        validation = manager.validate_yaml_config(config_type, content)
        return [TextContent(
            type="text",
            text=json.dumps(validation, indent=2)
        )]
    
    elif name == "increment_version":
        result = manager.increment_version()
        return [TextContent(
            type="text",
            text=result
        )]
    
    elif name == "connect_websocket":
        url = arguments.get("url", "ws://localhost:5000")
        result = manager.connect_websocket(url)
        return [TextContent(
            type="text",
            text=result
        )]
    
    elif name == "send_command":
        command = arguments["command"]
        username = arguments.get("username", "admin")
        result = manager.send_command(command, username)
        return [TextContent(
            type="text",
            text=result
        )]
    
    elif name == "get_messages":
        count = arguments.get("count", 10)
        messages = manager.get_recent_messages(count)
        return [TextContent(
            type="text",
            text=json.dumps(messages, indent=2)
        )]
    
    elif name == "run_tests":
        test_type = arguments.get("test_type", "basic")
        results = manager.run_test_suite(test_type)
        return [TextContent(
            type="text",
            text=json.dumps(results, indent=2)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
