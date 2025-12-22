#!/usr/bin/env python3
"""
TextSpace Management Agent
Specialized agent for managing TextSpace server using MCP tools
"""

import json
import time
from typing import Dict, List, Any, Optional

class TextSpaceAgent:
    """Intelligent TextSpace server management agent"""
    
    def __init__(self):
        self.connected = False
        self.server_status = {}
        self.last_test_results = {}
        
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        print("🔍 Performing TextSpace health check...")
        
        # Check server status
        status_result = self._call_mcp_tool("server_status")
        if status_result.get("error"):
            return {"status": "error", "message": "Failed to get server status"}
        
        self.server_status = json.loads(status_result["content"])
        
        # Run basic tests
        test_result = self._call_mcp_tool("run_tests", {"test_type": "basic"})
        if test_result.get("error"):
            return {"status": "warning", "message": "Tests failed to run"}
        
        self.last_test_results = json.loads(test_result["content"])
        
        # Analyze results
        if not self.server_status.get("running"):
            return {
                "status": "critical",
                "message": "Server is not running",
                "recommendation": "Start server with server_start tool"
            }
        
        failed_tests = [r for r in self.last_test_results.get("results", []) 
                       if r["status"] != "PASS"]
        
        if failed_tests:
            return {
                "status": "warning", 
                "message": f"{len(failed_tests)} tests failed",
                "failed_tests": failed_tests,
                "recommendation": "Check logs and fix issues"
            }
        
        return {
            "status": "healthy",
            "message": "All systems operational",
            "version": self.server_status.get("version"),
            "tests_passed": self.last_test_results.get("summary")
        }
    
    def deploy_update(self, config_changes: Optional[Dict] = None) -> Dict[str, Any]:
        """Deploy updates with proper version management"""
        print("🚀 Deploying TextSpace update...")
        
        steps = []
        
        # 1. Health check first
        health = self.health_check()
        steps.append(f"Health check: {health['status']}")
        
        # 2. Apply config changes if provided
        if config_changes:
            for config_type, content in config_changes.items():
                # Validate first
                validate_result = self._call_mcp_tool("validate_config", {
                    "config_type": config_type,
                    "content": content
                })
                
                if "valid" in validate_result.get("content", "") and "true" in validate_result["content"]:
                    # Write config
                    write_result = self._call_mcp_tool("write_config", {
                        "config_type": config_type,
                        "content": content
                    })
                    steps.append(f"Updated {config_type}.yaml")
                else:
                    return {
                        "status": "error",
                        "message": f"Invalid {config_type} configuration",
                        "steps": steps
                    }
        
        # 3. Increment version
        version_result = self._call_mcp_tool("increment_version")
        if "incremented" in version_result.get("content", ""):
            steps.append("Version incremented")
        
        # 4. Restart server if running
        if self.server_status.get("running"):
            stop_result = self._call_mcp_tool("server_stop")
            steps.append("Server stopped")
            time.sleep(2)
            
            start_result = self._call_mcp_tool("server_start")
            steps.append("Server restarted")
            time.sleep(3)
        
        # 5. Final health check
        final_health = self.health_check()
        steps.append(f"Final health: {final_health['status']}")
        
        return {
            "status": "success" if final_health["status"] == "healthy" else "warning",
            "message": "Deployment completed",
            "steps": steps,
            "final_health": final_health
        }
    
    def interactive_testing(self) -> Dict[str, Any]:
        """Run interactive testing session"""
        print("🧪 Starting interactive testing session...")
        
        # Connect to server
        connect_result = self._call_mcp_tool("connect_websocket")
        if "connected" not in connect_result.get("content", ""):
            return {"status": "error", "message": "Failed to connect to server"}
        
        self.connected = True
        
        # Run test scenarios
        scenarios = [
            ("Basic Commands", ["help", "version", "look"]),
            ("Navigation", ["north", "look", "south", "look"]),
            ("Items", ["inventory", "examine treasure chest", "get treasure chest"]),
            ("Social", ["say Hello from test agent", "who"])
        ]
        
        results = []
        for scenario_name, commands in scenarios:
            print(f"  Running {scenario_name} scenario...")
            scenario_results = []
            
            for cmd in commands:
                send_result = self._call_mcp_tool("send_command", {"command": cmd})
                scenario_results.append(cmd)
                time.sleep(1)
            
            # Get messages to see responses
            messages_result = self._call_mcp_tool("get_messages", {"count": 5})
            
            results.append({
                "scenario": scenario_name,
                "commands": scenario_results,
                "status": "completed"
            })
        
        return {
            "status": "success",
            "message": f"Completed {len(scenarios)} test scenarios",
            "results": results
        }
    
    def monitor_server(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Monitor server for specified duration"""
        print(f"📊 Monitoring server for {duration_minutes} minutes...")
        
        if not self.connected:
            connect_result = self._call_mcp_tool("connect_websocket")
            if "connected" in connect_result.get("content", ""):
                self.connected = True
        
        monitoring_data = {
            "start_time": time.time(),
            "duration_minutes": duration_minutes,
            "snapshots": []
        }
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            # Take snapshot
            snapshot = {
                "timestamp": time.time(),
                "server_status": self._call_mcp_tool("server_status"),
                "recent_messages": self._call_mcp_tool("get_messages", {"count": 3})
            }
            monitoring_data["snapshots"].append(snapshot)
            
            print(f"  📸 Snapshot taken ({len(monitoring_data['snapshots'])})")
            time.sleep(30)  # Snapshot every 30 seconds
        
        return {
            "status": "success",
            "message": f"Monitoring completed - {len(monitoring_data['snapshots'])} snapshots",
            "data": monitoring_data
        }
    
    def _call_mcp_tool(self, tool_name: str, arguments: Dict = None) -> Dict[str, Any]:
        """Call MCP tool via direct manager instance"""
        from textspace_mcp_server import TextSpaceManager
        import json
        
        manager = TextSpaceManager()
        
        try:
            if tool_name == "server_status":
                result = manager.get_server_status()
                return {"content": json.dumps(result), "status": "success"}
            elif tool_name == "run_tests":
                test_type = arguments.get("test_type", "basic") if arguments else "basic"
                result = manager.run_test_suite(test_type)
                return {"content": json.dumps(result), "status": "success"}
            elif tool_name == "server_logs":
                lines = arguments.get("lines", 50) if arguments else 50
                result = manager.get_logs(lines)
                return {"content": result, "status": "success"}
            elif tool_name == "increment_version":
                result = manager.increment_version()
                return {"content": result, "status": "success"}
            elif tool_name == "server_start":
                result = manager.start_server()
                return {"content": result, "status": "success"}
            elif tool_name == "server_stop":
                result = manager.stop_server()
                return {"content": result, "status": "success"}
            elif tool_name == "connect_websocket":
                url = arguments.get("url", "ws://localhost:5000") if arguments else "ws://localhost:5000"
                result = manager.connect_websocket(url)
                return {"content": result, "status": "success"}
            elif tool_name == "send_command":
                if not arguments:
                    return {"content": "No command provided", "status": "error"}
                command = arguments["command"]
                username = arguments.get("username", "admin")
                result = manager.send_command(command, username)
                return {"content": result, "status": "success"}
            elif tool_name == "get_messages":
                count = arguments.get("count", 10) if arguments else 10
                result = manager.get_recent_messages(count)
                return {"content": json.dumps(result), "status": "success"}
            else:
                return {"content": f"Unknown tool: {tool_name}", "status": "error"}
        except Exception as e:
            return {"content": f"Error: {str(e)}", "status": "error"}

def main():
    """Demo the TextSpace management agent"""
    agent = TextSpaceAgent()
    
    print("🤖 TextSpace Management Agent Demo")
    print("=" * 50)
    
    # Health check
    health = agent.health_check()
    print(f"Health Status: {health['status']}")
    print(f"Message: {health['message']}")
    
    # Interactive testing
    test_results = agent.interactive_testing()
    print(f"Testing: {test_results['status']}")
    
    # Example deployment
    config_changes = {
        "rooms": """
rooms:
  lobby:
    name: "Updated Lobby"
    description: "A newly renovated entrance hall."
    exits:
      north: garden
      east: library
    items: ["treasure_chest"]
"""
    }
    
    deploy_results = agent.deploy_update(config_changes)
    print(f"Deployment: {deploy_results['status']}")
    
    print("\n✅ Agent demo completed!")

if __name__ == "__main__":
    main()
