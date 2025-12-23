#!/usr/bin/env python3
"""
TextSpace Remote MCP Server - Manages Railway-deployed TextSpace server
Provides tools for remote server control, configuration management, and testing
"""

import asyncio
import json
import os
import requests
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
logger = logging.getLogger("textspace-remote-mcp")

# Force restart by adding timestamp
# Last updated: 2025-12-21 22:16:45 - Changed to API-based server control

# Initialize MCP server
server = Server("textspace-remote-mcp")

class RemoteTextSpaceManager:
    """Remote TextSpace server management via REST API"""
    
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("TEXTSPACE_BASE_URL", "https://exciting-liberation-production.up.railway.app")
        self.base_url = base_url.rstrip('/')
        self.ws_connection = None
        self.ws_messages = []
        self.ws_connected = False
        
    def get_server_status(self) -> Dict[str, Any]:
        """Check remote TextSpace server status"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "running": False}
        except Exception as e:
            return {"error": str(e), "running": False}
    
    def get_logs(self, lines: int = 50) -> str:
        """Get recent server logs"""
        try:
            response = requests.get(f"{self.base_url}/api/logs", params={"lines": lines}, timeout=10)
            if response.status_code == 200:
                return response.json().get("logs", "No logs available")
            else:
                return f"Error getting logs: HTTP {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def read_config(self, config_type: str) -> str:
        """Read configuration from remote server"""
        try:
            response = requests.get(f"{self.base_url}/api/config/{config_type}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return yaml.dump(data, default_flow_style=False)
            else:
                return f"Error reading config: HTTP {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
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
        """Write configuration to remote server"""
        try:
            # Validate first
            validation = self.validate_yaml_config(config_type, content)
            if not validation["valid"]:
                return f"Validation failed: {validation['error']}"
            
            # Send to remote server
            response = requests.post(
                f"{self.base_url}/api/config/{config_type}",
                json=validation["data"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return f"Configuration updated successfully. {result.get('message', '')}"
            else:
                return f"Error updating config: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error writing config: {str(e)}"
    
    def increment_version(self) -> str:
        """Increment server version"""
        try:
            response = requests.post(f"{self.base_url}/api/version", timeout=10)
            if response.status_code == 200:
                result = response.json()
                return f"Version incremented to {result.get('version', 'unknown')}"
            else:
                return f"Error incrementing version: HTTP {response.status_code}"
        except Exception as e:
            return f"Error incrementing version: {str(e)}"
    
    def connect_websocket(self, url: str = None) -> str:
        """Connect to remote TextSpace server via WebSocket"""
        if url is None:
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
            url = f"{ws_url}/socket.io/?EIO=4&transport=websocket"
        
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
        """Send command to remote TextSpace server via WebSocket"""
        try:
            if not self.ws_connected or not self.ws_connection:
                # Try to reconnect
                self.connect_websocket()
                time.sleep(1)
                
            if not self.ws_connected:
                return "Not connected to server. Use connect_websocket first."
            
            # Send command directly as text (simplified approach)
            self.ws_connection.send(command)
            
            return f"Command '{command}' sent as user '{username}'"
        except Exception as e:
            return f"Error sending command: {str(e)}"
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent WebSocket messages"""
        return self.ws_messages[-count:] if self.ws_messages else []
    
    def run_test_suite(self, test_type: str = "basic") -> Dict[str, Any]:
        """Run automated test suite against remote server"""
        try:
            test_results = {
                "timestamp": datetime.now().isoformat(),
                "test_type": test_type,
                "results": []
            }
            
            if test_type == "basic":
                tests = [
                    ("Server Status", self._test_server_running),
                    ("API Endpoints", self._test_api_endpoints),
                    ("Config Access", self._test_config_access)
                ]
            elif test_type == "web":
                tests = [
                    ("Web Server", self._test_web_server),
                    ("WebSocket", self._test_websocket),
                    ("API Endpoints", self._test_api_endpoints)
                ]
            elif test_type == "full":
                tests = [
                    ("Server Status", self._test_server_running),
                    ("API Endpoints", self._test_api_endpoints),
                    ("Config Access", self._test_config_access),
                    ("Web Server", self._test_web_server),
                    ("WebSocket", self._test_websocket),
                    ("Version Management", self._test_version_management)
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
        """Test if remote server is running"""
        status = self.get_server_status()
        return {
            "success": status.get("running", False),
            "details": f"Version: {status.get('version', 'unknown')}, Users: {status.get('users_online', 0)}"
        }
    
    def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            return {
                "success": response.status_code == 200,
                "details": f"Status API: HTTP {response.status_code}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_config_access(self) -> Dict[str, Any]:
        """Test configuration access"""
        try:
            response = requests.get(f"{self.base_url}/api/config/rooms", timeout=5)
            return {
                "success": response.status_code == 200,
                "details": f"Config API: HTTP {response.status_code}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_web_server(self) -> Dict[str, Any]:
        """Test web server responds"""
        try:
            response = requests.get(self.base_url, timeout=5)
            return {
                "success": response.status_code == 200,
                "details": f"HTTP {response.status_code}"
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
    
    def _test_version_management(self) -> Dict[str, Any]:
        """Test version management (read-only)"""
        status = self.get_server_status()
        return {
            "success": "version" in status,
            "details": f"Current version: {status.get('version', 'unknown')}"
        }

# Initialize manager
manager = RemoteTextSpaceManager()

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available remote TextSpace management tools"""
    return [
        Tool(
            name="server_status",
            description="Check remote TextSpace server status and version",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="server_logs",
            description="Get recent server logs from remote server",
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
            name="read_config",
            description="Read TextSpace configuration files from remote server",
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
            description="Write TextSpace configuration files to remote server with validation",
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
            description="Increment server version number on remote server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="connect_websocket",
            description="Connect to remote TextSpace server via WebSocket",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "WebSocket URL (optional, auto-detected from base URL)",
                        "default": ""
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="send_command",
            description="Send command to remote TextSpace server",
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
            description="Get recent WebSocket messages from remote server",
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
            description="Run automated test suite against remote server",
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
        ),
        Tool(
            name="reset_config",
            description="Reset configuration to examples (REQUIRES DOUBLE CONFIRMATION)",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_type": {
                        "type": "string",
                        "enum": ["rooms", "bots", "items", "scripts"],
                        "description": "Type of configuration to reset"
                    },
                    "confirmation_code": {
                        "type": "string",
                        "description": "Required confirmation code (get from first call without code)"
                    }
                },
                "required": ["config_type"]
            }
        ),
        Tool(
            name="config_info",
            description="Get information about configuration storage and status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="server_control",
            description="Start or stop the TextSpace server via API",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop"],
                        "description": "Action to perform: start or stop the server"
                    }
                },
                "required": ["action"]
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
    
    elif name == "read_config":
        config_type = arguments["config_type"]
        content = manager.read_config(config_type)
        return [TextContent(
            type="text",
            text=f"=== {config_type}.yaml ===\n{content}"
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
        url = arguments.get("url", "")
        result = manager.connect_websocket(url if url else None)
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
    
    elif name == "reset_config":
        config_type = arguments["config_type"]
        confirmation_code = arguments.get("confirmation_code", "")
        
        try:
            response = requests.post(
                f"{manager.base_url}/api/config/reset/{config_type}",
                json={"confirmation_code": confirmation_code},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return [TextContent(
                    type="text",
                    text=f"✅ Config reset successful: {result.get('message', 'Reset completed')}"
                )]
            else:
                error_data = response.json()
                if 'required_code' in error_data:
                    return [TextContent(
                        type="text",
                        text=f"⚠️ CONFIRMATION REQUIRED\n\nTo reset {config_type} configuration, use:\nreset_config with confirmation_code: {error_data['required_code']}\n\n🚨 WARNING: {error_data.get('warning', 'This action cannot be undone!')}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ Reset failed: {error_data.get('error', 'Unknown error')}"
                    )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error resetting config: {str(e)}"
            )]
    
    elif name == "config_info":
        try:
            response = requests.get(f"{manager.base_url}/api/config/info", timeout=10)
            if response.status_code == 200:
                info = response.json()
                return [TextContent(
                    type="text",
                    text=json.dumps(info, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error getting config info: HTTP {response.status_code}"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting config info: {str(e)}"
            )]
    
    elif name == "server_control":
        action = arguments.get("action")
        
        if action == "start":
            try:
                # Send restart request to server API
                response = requests.post(f"{manager.base_url}/api/restart", timeout=10)
                if response.status_code == 200:
                    return [TextContent(
                        type="text",
                        text="Server restart initiated via API"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Failed to restart server: HTTP {response.status_code}"
                    )]
            except Exception as e:
                return [TextContent(type="text", text=f"Error restarting server: {str(e)}")]
        
        elif action == "stop":
            try:
                # Send shutdown request to server API
                response = requests.post(f"{manager.base_url}/api/shutdown", timeout=10)
                if response.status_code == 200:
                    return [TextContent(
                        type="text",
                        text="Server shutdown initiated via API"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Failed to shutdown server: HTTP {response.status_code}"
                    )]
            except Exception as e:
                return [TextContent(type="text", text=f"Error shutting down server: {str(e)}")]
        
        else:
            return [TextContent(
                type="text",
                text=f"Invalid action: {action}. Use 'start' or 'stop'"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Run the remote MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
